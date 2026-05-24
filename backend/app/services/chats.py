import uuid
from datetime import datetime
from sqlmodel import Session, select, func, and_, or_

from app.models.chat import Chat
from app.models.miembro_chat import MiembroChat
from app.models.invitacion_chat import InvitacionChat
from app.models.solicitud_chat import SolicitudChat
from app.models.mensaje import Mensaje
from app.models.mensaje_destinatario import MensajeDestinatario
from app.models.usuario import Usuario

from app.schemas.chat import ChatCreate, ChatUpdate


# ── Helpers ───────────────────────────────────────────────────────
def _contar_admins(chat_id: uuid.UUID, session: Session) -> int:
    """Devuelve el número de administradores activos de un chat."""
    return session.exec(
        select(func.count(MiembroChat.id)).where(
            MiembroChat.chat_id == chat_id,
            MiembroChat.estado == "activo",
            MiembroChat.rol == "administrador",
        )
    ).one()


def _get_miembros_activos(chat_id: uuid.UUID, session: Session) -> list[MiembroChat]:
    """Devuelve todos los miembros activos de un chat."""
    return session.exec(
        select(MiembroChat).where(
            MiembroChat.chat_id == chat_id, MiembroChat.estado == "activo"
        )
    ).all()


def _crear_miembro(
    chat_id: uuid.UUID, usuario_id: uuid.UUID, rol: str, session: Session
) -> MiembroChat:
    """Helper interno: crea un registro en miembros_chat con estado activo."""
    miembro = MiembroChat(
        chat_id=chat_id,
        usuario_id=usuario_id,
        rol=rol,
        estado="activo",
        fecha_incorporacion=datetime.now(),
    )
    session.add(miembro)
    return miembro


# ── Chats ────────────────────────────────────────────────────────


def get_membresia(
    chat_id: uuid.UUID, usuario_id: uuid.UUID, session: Session
) -> MiembroChat | None:
    """Devuelve la membresía activa de un usuario en un chat, o None si no es miembro."""
    return session.exec(
        select(MiembroChat).where(
            MiembroChat.chat_id == chat_id,
            MiembroChat.usuario_id == usuario_id,
            MiembroChat.estado == "activo",
        )
    ).first()


def es_admin_chat(chat_id: uuid.UUID, usuario_id: uuid.UUID, session: Session) -> bool:
    """Comprueba si un usuario es administrador de un chat."""
    membresia = get_membresia(chat_id, usuario_id, session)
    return membresia is not None and membresia.rol == "administrador"


def contar_miembros(chat_id: uuid.UUID, session: Session) -> int:
    """Devuelve el número de miembros activos (aceptados) de un chat."""
    return session.exec(
        select(func.count(MiembroChat.id)).where(
            MiembroChat.chat_id == chat_id, MiembroChat.estado == "activo"
        )
    ).one()


def get_chats_visibles(usuario: Usuario, session: Session) -> list[Chat]:
    """
    Devuelve los chats visibles para el usuario.
    Los chats visibles son accesibles para todos los usuarios autenticados.
    Los chats ocultos solo los ven sus miembros activos.
    """
    # IDs de chats donde el usuario es miembro activo
    membresías = session.exec(
        select(MiembroChat.chat_id).where(
            MiembroChat.usuario_id == usuario.id, MiembroChat.estado == "activo"
        )
    ).all()
    ids_miembro = set(membresías)

    chats = session.exec(select(Chat)).all()

    return [c for c in chats if c.visibilidad == "visible" or c.id in ids_miembro]


def get_chat(chat_id: str, session: Session) -> Chat | None:
    """Devuelve un chat por su ID."""
    return session.get(Chat, uuid.UUID(chat_id))


def crear_chat(datos: ChatCreate, usuario: Usuario, session: Session) -> Chat:
    """
    Crea un chat y añade al creador como administrador activo.
    Crea también la SolicitudChat correspondiente con estado aceptada.
    """
    chat = Chat(**datos.model_dump(), usuario_creacion=usuario.id)
    session.add(chat)
    session.flush()  # necesitamos el id del chat antes del commit

    # Solicitud automática aceptada para el creador
    solicitud = SolicitudChat(
        chat_id=chat.id,
        usuario_id=usuario.id,
        estado="aceptada",
        fecha_resolucion=datetime.now(),
        usuario_resolucion=usuario.id,
    )
    session.add(solicitud)

    # Membresía activa como administrador
    _crear_miembro(chat.id, usuario.id, "administrador", session)

    session.commit()
    session.refresh(chat)
    return chat


def editar_chat(chat: Chat, datos: ChatUpdate, session: Session) -> Chat:
    """Edita la configuración de un chat."""
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(chat, campo, valor)
    session.add(chat)
    session.commit()
    session.refresh(chat)
    return chat


# ── Solicitudes ───────────────────────────────────────────────────


def get_solicitud_pendiente(
    chat_id: uuid.UUID, usuario_id: uuid.UUID, session: Session
) -> SolicitudChat | None:
    """Devuelve la solicitud pendiente de un usuario en un chat, si existe."""
    return session.exec(
        select(SolicitudChat).where(
            SolicitudChat.chat_id == chat_id,
            SolicitudChat.usuario_id == usuario_id,
            SolicitudChat.estado == "pendiente",
        )
    ).first()


def get_solicitudes_pendientes(
    chat_id: str, session: Session
) -> list[tuple[SolicitudChat, Usuario]]:
    """Devuelve las solicitudes pendientes de un chat."""
    return session.exec(
        select(SolicitudChat, Usuario)
        .join(Usuario, Usuario.id == SolicitudChat.usuario_id)
        .where(
            SolicitudChat.chat_id == uuid.UUID(chat_id),
            SolicitudChat.estado == "pendiente",
        )
        .order_by(SolicitudChat.fecha_solicitud)
    ).all()


def enviar_solicitud(
    chat: Chat, usuario: Usuario, session: Session
) -> tuple[SolicitudChat | None, str]:
    """
    Gestiona la petición de acceso de un usuario a un chat.
    - Chat libre: crea SolicitudChat aceptada y MiembroChat en la misma operación.
    - Chat restringido: crea SolicitudChat pendiente. No crea MiembroChat.
    """
    if get_membresia(chat.id, usuario.id, session):
        return None, "El usuario ya es miembro activo de este chat"

    if get_solicitud_pendiente(chat.id, usuario.id, session):
        return None, "El usuario ya tiene una solicitud pendiente en este chat"

    if chat.tipo_acceso == "libre":
        solicitud = SolicitudChat(
            chat_id=chat.id,
            usuario_id=usuario.id,
            estado="aceptada",
            fecha_resolucion=datetime.now(),
            usuario_resolucion=usuario.id,
        )
        session.add(solicitud)
        session.flush()
        rol_entrada = "administrador" if usuario.rol == "administrador" else "miembro"
        _crear_miembro(chat.id, usuario.id, rol_entrada, session)
    else:
        solicitud = SolicitudChat(
            chat_id=chat.id, usuario_id=usuario.id, estado="pendiente"
        )
        session.add(solicitud)

    session.commit()
    session.refresh(solicitud)
    return solicitud, ""


def resolver_solicitud(
    solicitud: SolicitudChat,
    aceptar: bool,
    usuario_resolucion: Usuario,
    session: Session,
) -> tuple[SolicitudChat, MiembroChat | None]:
    """
    El administrador aprueba o rechaza una solicitud pendiente.
        Si aprueba: actualiza SolicitudChat y crea MiembroChat.
        Si rechaza: actualiza SolicitudChat. No crea MiembroChat.
    """
    solicitud.estado = "aceptada" if aceptar else "rechazada"
    solicitud.fecha_resolucion = datetime.now()
    solicitud.usuario_resolucion = usuario_resolucion.id
    session.add(solicitud)

    miembro = None
    if aceptar:
        session.flush()
        usuario_solicitante = session.get(Usuario, solicitud.usuario_id)
        rol_entrada = (
            "administrador"
            if usuario_solicitante and usuario_solicitante.rol == "administrador"
            else "miembro"
        )
        miembro = _crear_miembro(
            solicitud.chat_id, solicitud.usuario_id, rol_entrada, session
        )

    session.commit()
    session.refresh(solicitud)
    if miembro:
        session.refresh(miembro)
    return solicitud, miembro


# ── Miembros ────────────────────────────────────────────────────


def get_miembros(chat_id: str, session: Session) -> list[tuple[MiembroChat, Usuario]]:
    """Devuelve los miembros activos de un chat con sus datos de usuario."""
    return session.exec(
        select(MiembroChat, Usuario)
        .join(Usuario, Usuario.id == MiembroChat.usuario_id)
        .where(
            MiembroChat.chat_id == uuid.UUID(chat_id), MiembroChat.estado == "activo"
        )
        .order_by(Usuario.apellidos, Usuario.nombre)
    ).all()


def cambiar_rol(
    miembro: MiembroChat, nuevo_rol: str, session: Session
) -> tuple[MiembroChat | None, str]:
    """
    Cambia el rol de un miembro activo.
    Valida que el chat no quede sin administrador.
    """
    if nuevo_rol == "miembro" and miembro.rol == "administrador":
        if _contar_admins(miembro.chat_id, session) <= 1:
            return None, "No se puede degradar al único administrador del chat"

    miembro.rol = nuevo_rol
    session.add(miembro)
    session.commit()
    session.refresh(miembro)
    return miembro, ""


def dar_baja_miembro(
    miembro: MiembroChat, usuario_baja: Usuario, session: Session
) -> tuple[MiembroChat | None, str]:
    """
    Baja lógica de un miembro. El registro se conserva en miembros_chat
    con estado 'baja' para trazabilidad histórica.
    Valida que el chat no quede sin miembros ni sin administrador.
    """
    if contar_miembros(miembro.chat_id, session) <= 1:
        return None, "No se puede dar de baja al único miembro del chat"

    if miembro.rol == "administrador" and _contar_admins(miembro.chat_id, session) <= 1:
        return None, "No se puede dar de baja al único administrador del chat"

    miembro.estado = "baja"
    miembro.fecha_baja = datetime.now()
    miembro.usuario_baja = usuario_baja.id
    session.add(miembro)
    session.commit()
    session.refresh(miembro)
    return miembro, ""


# ── Invitaciones ──────────────────────────────────────────────────


def get_invitacion_pendiente(
    chat_id: uuid.UUID, usuario_destinatario: uuid.UUID, session: Session
) -> InvitacionChat | None:
    """Devuelve la invitación pendiente de un usuario en un chat, si existe."""
    return session.exec(
        select(InvitacionChat).where(
            InvitacionChat.chat_id == chat_id,
            InvitacionChat.usuario_destinatario == usuario_destinatario,
            InvitacionChat.estado == "pendiente",
        )
    ).first()


def get_invitacion_rechazada(
    chat_id: uuid.UUID, usuario_destinatario: uuid.UUID, session: Session
) -> InvitacionChat | None:
    """Comprueba si existe una invitación rechazada (bloquea nuevas invitaciones)."""
    return session.exec(
        select(InvitacionChat).where(
            InvitacionChat.chat_id == chat_id,
            InvitacionChat.usuario_destinatario == usuario_destinatario,
            InvitacionChat.estado == "rechazada",
        )
    ).first()


def get_invitaciones_pendientes_usuario(
    usuario_id: uuid.UUID, session: Session
) -> list[tuple[InvitacionChat, Chat, Usuario]]:
    """Devuelve las invitaciones pendientes del usuario autenticado."""
    return session.exec(
        select(InvitacionChat, Chat, Usuario)
        .join(Chat, Chat.id == InvitacionChat.chat_id)
        .join(Usuario, Usuario.id == InvitacionChat.usuario_invitacion)
        .where(
            InvitacionChat.usuario_destinatario == usuario_id,
            InvitacionChat.estado == "pendiente",
        )
        .order_by(InvitacionChat.fecha_invitacion.desc())
    ).all()


def enviar_invitacion(
    chat: Chat, usuario_destinatario: Usuario, admin: Usuario, session: Session
) -> tuple[InvitacionChat | None, str]:
    """
    El administrador envía una invitación a un usuario.
    Verifica que el usuario no sea ya miembro, no tenga invitación pendiente
    y no haya rechazado previamente una invitación de este chat.
    """
    if get_membresia(chat.id, usuario_destinatario.id, session):
        return None, "El usuario ya es miembro activo de este chat"

    if get_invitacion_pendiente(chat.id, usuario_destinatario.id, session):
        return None, "El usuario ya tiene una invitación pendiente de este chat"

    if get_invitacion_rechazada(chat.id, usuario_destinatario.id, session):
        return None, "El usuario rechazó previamente una invitación de este chat"

    invitacion = InvitacionChat(
        chat_id=chat.id,
        usuario_destinatario=usuario_destinatario.id,
        usuario_invitacion=admin.id,
        estado="pendiente",
    )
    session.add(invitacion)
    session.commit()
    session.refresh(invitacion)
    return invitacion, ""


def resolver_invitacion(
    invitacion: InvitacionChat, aceptar: bool, session: Session
) -> tuple[InvitacionChat, MiembroChat | None]:
    """
    El usuario acepta o rechaza una invitación.
    Si acepta: actualiza InvitacionChat y crea MiembroChat.
    Si rechaza: actualiza InvitacionChat. No crea MiembroChat.
             El rechazo bloquea futuras invitaciones del mismo chat.
    """
    invitacion.estado = "aceptada" if aceptar else "rechazada"
    invitacion.fecha_resolucion = datetime.now()
    session.add(invitacion)

    miembro = None
    if aceptar:
        session.flush()
        usuario_destinatario_obj = session.get(Usuario, invitacion.usuario_destinatario)
        rol_entrada = (
            "administrador"
            if usuario_destinatario_obj
            and usuario_destinatario_obj.rol == "administrador"
            else "miembro"
        )
        miembro = _crear_miembro(
            invitacion.chat_id, invitacion.usuario_destinatario, rol_entrada, session
        )

    session.commit()
    session.refresh(invitacion)
    if miembro:
        session.refresh(miembro)
    return invitacion, miembro


# ── Mensajes ──────────────────────────────────────────────────────


def get_mensajes_chat(
    chat_id: str, usuario_id: uuid.UUID, session: Session
) -> list[tuple[Mensaje, Usuario, MensajeDestinatario | None]]:
    """
    Devuelve los mensajes de un chat ordenados cronológicamente,
    junto con el estado de lectura del usuario actual.
    """
    return session.exec(
        select(Mensaje, Usuario, MensajeDestinatario)
        .join(Usuario, Usuario.id == Mensaje.usuario_envio)
        .outerjoin(
            MensajeDestinatario,
            and_(
                MensajeDestinatario.mensaje_id == Mensaje.id,
                MensajeDestinatario.usuario_destinatario == usuario_id,
            ),
        )
        .where(Mensaje.chat_id == uuid.UUID(chat_id))
        .order_by(Mensaje.fecha_envio)
    ).all()


def get_mensajes_directos(
    usuario_id: uuid.UUID, otro_usuario_id: uuid.UUID, session: Session
) -> list[tuple[Mensaje, Usuario, MensajeDestinatario | None]]:
    """
    Devuelve los mensajes directos entre dos usuarios ordenados cronológicamente.
    Incluye tanto los mensajes enviados como los recibidos por el usuario actual.
    """
    return session.exec(
        select(Mensaje, Usuario, MensajeDestinatario)
        .join(Usuario, Usuario.id == Mensaje.usuario_envio)
        .outerjoin(
            MensajeDestinatario,
            and_(
                MensajeDestinatario.mensaje_id == Mensaje.id,
                MensajeDestinatario.usuario_destinatario == usuario_id,
            ),
        )
        .where(
            Mensaje.chat_id == None,
            or_(
                # Mensajes enviados por el usuario actual al otro usuario
                and_(
                    Mensaje.usuario_envio == usuario_id,
                    Mensaje.id.in_(
                        select(MensajeDestinatario.mensaje_id).where(
                            MensajeDestinatario.usuario_destinatario == otro_usuario_id
                        )
                    ),
                ),
                # Mensajes enviados por el otro al usuario actual
                and_(
                    Mensaje.usuario_envio == otro_usuario_id,
                    Mensaje.id.in_(
                        select(MensajeDestinatario.mensaje_id).where(
                            MensajeDestinatario.usuario_destinatario == usuario_id
                        )
                    ),
                ),
            ),
        )
        .order_by(Mensaje.fecha_envio)
    ).all()


def enviar_mensaje_directo(
    contenido: str, remitente: Usuario, destinatario: Usuario, session: Session
) -> Mensaje:
    """
    Envía un mensaje directo a otro usuario.
    Crea el mensaje y un único registro en mensajes_destinatarios.
    """
    mensaje = Mensaje(contenido=contenido, usuario_envio=remitente.id, chat_id=None)
    session.add(mensaje)
    session.flush()

    destinatario_registro = MensajeDestinatario(
        mensaje_id=mensaje.id,
        usuario_destinatario=destinatario.id,
        fecha_recepcion=datetime.now(),
        estado="recibido",
    )
    session.add(destinatario_registro)
    session.commit()
    session.refresh(mensaje)
    return mensaje


def enviar_mensaje_chat(
    contenido: str, remitente: Usuario, chat: Chat, session: Session
) -> tuple[Mensaje | None, str]:
    """
    Envía un mensaje a un chat.
    Verifica permisos según la modalidad del chat:
    - bidireccional: cualquier miembro puede escribir.
    - canal: solo los administradores del chat pueden escribir.
    Crea un registro en mensajes_destinatarios por cada miembro activo.
    """
    membresia = get_membresia(chat.id, remitente.id, session)
    if not membresia:
        return None, "No eres miembro de este chat"

    # En canal de difusión solo los administradores pueden escribir
    if chat.modalidad == "canal" and membresia.rol != "administrador":
        return None, "Solo los administradores pueden publicar en este canal"

    mensaje = Mensaje(contenido=contenido, usuario_envio=remitente.id, chat_id=chat.id)
    session.add(mensaje)
    session.flush()

    # Crear un registro por cada miembro activo excepto el remitente
    miembros = _get_miembros_activos(chat.id, session)
    for miembro in miembros:
        if miembro.usuario_id != remitente.id:
            dest = MensajeDestinatario(
                mensaje_id=mensaje.id,
                usuario_destinatario=miembro.usuario_id,
                fecha_recepcion=datetime.now(),
                estado="recibido",
            )
            session.add(dest)

    session.commit()
    session.refresh(mensaje)
    return mensaje, ""


def marcar_mensajes_leidos(
    mensaje_ids: list[uuid.UUID], usuario_id: uuid.UUID, session: Session
) -> None:
    """
    Marca como leídos los mensajes indicados para el usuario actual.
    Se llama cuando el usuario abre una conversación o chat.
    """
    registros = session.exec(
        select(MensajeDestinatario).where(
            MensajeDestinatario.mensaje_id.in_(mensaje_ids),
            MensajeDestinatario.usuario_destinatario == usuario_id,
            MensajeDestinatario.estado != "leido",
        )
    ).all()

    for registro in registros:
        registro.estado = "leido"
        registro.fecha_lectura = datetime.now()
        session.add(registro)

    session.commit()


# ── Historial ─────────────────────────────────────────────


def get_historial_directo(usuario_id: uuid.UUID, session: Session) -> list[dict]:
    """Historial de conversaciones directas con no leídos."""
    enviados = session.exec(
        select(MensajeDestinatario.usuario_destinatario, Mensaje)
        .join(Mensaje, Mensaje.id == MensajeDestinatario.mensaje_id)
        .where(Mensaje.chat_id == None, Mensaje.usuario_envio == usuario_id)
    ).all()

    recibidos = session.exec(
        select(Mensaje)
        .join(MensajeDestinatario, MensajeDestinatario.mensaje_id == Mensaje.id)
        .where(
            Mensaje.chat_id == None,
            MensajeDestinatario.usuario_destinatario == usuario_id,
        )
    ).all()

    interlocutores = set()
    for dest, _ in enviados:
        interlocutores.add(dest)
    for m in recibidos:
        interlocutores.add(m.usuario_envio)
    interlocutores.discard(usuario_id)

    resultado = []
    for interlocutor_id in interlocutores:
        usuario = session.get(Usuario, interlocutor_id)
        if not usuario:
            continue

        ultimo = session.exec(
            select(Mensaje)
            .outerjoin(
                MensajeDestinatario, MensajeDestinatario.mensaje_id == Mensaje.id
            )
            .where(
                Mensaje.chat_id == None,
                or_(
                    and_(
                        Mensaje.usuario_envio == usuario_id,
                        MensajeDestinatario.usuario_destinatario == interlocutor_id,
                    ),
                    and_(
                        Mensaje.usuario_envio == interlocutor_id,
                        MensajeDestinatario.usuario_destinatario == usuario_id,
                    ),
                ),
            )
            .order_by(Mensaje.fecha_envio.desc())
        ).first()

        no_leidos = session.exec(
            select(func.count(MensajeDestinatario.id)).where(
                MensajeDestinatario.usuario_destinatario == usuario_id,
                MensajeDestinatario.estado != "leido",
                MensajeDestinatario.mensaje_id.in_(
                    select(Mensaje.id).where(
                        Mensaje.usuario_envio == interlocutor_id,
                        Mensaje.chat_id == None,
                    )
                ),
            )
        ).one()

        resultado.append(
            {
                "usuario_id": str(interlocutor_id),
                "nombre": usuario.nombre,
                "apellidos": usuario.apellidos,
                "codigo_usuario": usuario.codigo_usuario,
                "ultimo_mensaje": ultimo.contenido if ultimo else None,
                "fecha_ultimo": ultimo.fecha_envio if ultimo else None,
                "no_leidos": no_leidos,
            }
        )

    return sorted(
        resultado, key=lambda x: x["fecha_ultimo"] or datetime.min, reverse=True
    )


def get_historial_chats(usuario_id: uuid.UUID, session: Session) -> list[dict]:
    """Historial de chats del usuario con no leídos."""
    membresías = session.exec(
        select(MiembroChat).where(
            MiembroChat.usuario_id == usuario_id, MiembroChat.estado == "activo"
        )
    ).all()

    resultado = []
    for membresia in membresías:
        chat = session.get(Chat, membresia.chat_id)
        if not chat:
            continue

        ultimo = session.exec(
            select(Mensaje)
            .where(Mensaje.chat_id == chat.id)
            .order_by(Mensaje.fecha_envio.desc())
        ).first()

        no_leidos = session.exec(
            select(func.count(MensajeDestinatario.id)).where(
                MensajeDestinatario.usuario_destinatario == usuario_id,
                MensajeDestinatario.estado != "leido",
                MensajeDestinatario.mensaje_id.in_(
                    select(Mensaje.id).where(Mensaje.chat_id == chat.id)
                ),
            )
        ).one()

        solicitudes_pendientes = (
            session.exec(
                select(func.count(SolicitudChat.id)).where(
                    SolicitudChat.chat_id == chat.id,
                    SolicitudChat.estado == "pendiente",
                )
            ).one()
            if membresia.rol == "administrador"
            else 0
        )

        resultado.append(
            {
                "chat_id": str(chat.id),
                "nombre": chat.nombre,
                "modalidad": chat.modalidad,
                "ultimo_mensaje": ultimo.contenido if ultimo else None,
                "fecha_ultimo": ultimo.fecha_envio if ultimo else None,
                "no_leidos": no_leidos,
                "solicitudes_pendientes": solicitudes_pendientes,
            }
        )

    return sorted(
        resultado, key=lambda x: x["fecha_ultimo"] or datetime.min, reverse=True
    )
