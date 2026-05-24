from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.database import get_session
from app.models.usuario import Usuario
from app.models.chat import Chat
from app.models.miembro_chat import MiembroChat
from app.models.solicitud_chat import SolicitudChat
from app.models.invitacion_chat import InvitacionChat
from app.schemas.chat import (
    ChatCreate,
    ChatUpdate,
    ChatOutput,
    MiembroChatOutput,
    MiembroRolUpdate,
    SolicitudChatOutput,
    InvitacionChatCreate,
    InvitacionChatOutput,
    MensajeCreate,
    MensajeOutput,
    ConversacionDirectaOutput,
    ChatResumenOutput,
)
from app.services.chats import (
    get_chats_visibles,
    get_chat,
    crear_chat,
    editar_chat,
    get_membresia,
    get_solicitud_pendiente,
    es_admin_chat,
    contar_miembros,
    get_miembros,
    get_solicitudes_pendientes,
    enviar_solicitud,
    resolver_solicitud,
    cambiar_rol,
    dar_baja_miembro,
    get_invitaciones_pendientes_usuario,
    enviar_invitacion,
    resolver_invitacion,
    get_mensajes_chat,
    get_mensajes_directos,
    enviar_mensaje_directo,
    enviar_mensaje_chat,
    marcar_mensajes_leidos,
    get_historial_directo,
    get_historial_chats,
)
from app.dependencies import get_usuario_actual
import uuid

router = APIRouter(prefix="/chat", tags=["Chat"])

# ── Helpers para construir outputs ────────────────────────────


def _chat_to_output(chat: Chat, usuario: Usuario, session: Session) -> ChatOutput:
    """Construye un ChatOutput con los campos calculados para el usuario actual."""
    membresia = get_membresia(chat.id, usuario.id, session)
    solicitud = get_solicitud_pendiente(chat.id, usuario.id, session)
    return ChatOutput(
        id=str(chat.id),
        nombre=chat.nombre,
        descripcion=chat.descripcion,
        tipo_acceso=chat.tipo_acceso,
        modalidad=chat.modalidad,
        visibilidad=chat.visibilidad,
        fecha_creacion=chat.fecha_creacion,
        usuario_creacion=str(chat.usuario_creacion),
        num_miembros=contar_miembros(chat.id, session),
        es_miembro=membresia is not None,
        mi_rol=membresia.rol if membresia else None,
        solicitud_estado=solicitud.estado if solicitud else None,
    )


def _miembro_to_output(miembro: MiembroChat, usuario: Usuario) -> MiembroChatOutput:
    """Construye un MiembroChatOutput con los datos del usuario."""
    return MiembroChatOutput(
        id=str(miembro.id),
        chat_id=str(miembro.chat_id),
        usuario_id=str(miembro.usuario_id),
        nombre_usuario=usuario.nombre,
        apellidos_usuario=usuario.apellidos,
        codigo_usuario=usuario.codigo_usuario,
        rol=miembro.rol,
        rol_sistema=usuario.rol,
        estado=miembro.estado,
        fecha_incorporacion=miembro.fecha_incorporacion,
        fecha_baja=miembro.fecha_baja,
        usuario_baja=str(miembro.usuario_baja) if miembro.usuario_baja else None,
    )


def _solicitud_to_output(
    solicitud: SolicitudChat, usuario: Usuario
) -> SolicitudChatOutput:
    """Construye un SolicitudChatOutput con los datos del solicitante."""
    return SolicitudChatOutput(
        id=str(solicitud.id),
        chat_id=str(solicitud.chat_id),
        usuario_id=str(solicitud.usuario_id),
        nombre_usuario=usuario.nombre,
        apellidos_usuario=usuario.apellidos,
        codigo_usuario=usuario.codigo_usuario,
        estado=solicitud.estado,
        fecha_solicitud=solicitud.fecha_solicitud,
        fecha_resolucion=solicitud.fecha_resolucion,
        usuario_resolucion=(
            str(solicitud.usuario_resolucion) if solicitud.usuario_resolucion else None
        ),
    )


def _invitacion_to_output(
    invitacion: InvitacionChat,
    chat: Chat,
    destinatario: Usuario,
    invitador: Usuario,
) -> InvitacionChatOutput:
    """Construye un InvitacionChatOutput con todos los datos relacionados."""
    return InvitacionChatOutput(
        id=str(invitacion.id),
        chat_id=str(invitacion.chat_id),
        usuario_destinatario=str(invitacion.usuario_destinatario),
        nombre_destinatario=destinatario.nombre,
        apellidos_destinatario=destinatario.apellidos,
        usuario_invitacion=str(invitacion.usuario_invitacion),
        nombre_invitador=invitador.nombre,
        apellidos_invitador=invitador.apellidos,
        nombre_chat=chat.nombre,
        fecha_invitacion=invitacion.fecha_invitacion,
        estado=invitacion.estado,
        fecha_resolucion=invitacion.fecha_resolucion,
    )


def _mensaje_to_output(
    mensaje, usuario_remitente, destinatario_registro
) -> MensajeOutput:
    """Construye un MensajeOutput con los datos del remitente y estado de lectura."""
    return MensajeOutput(
        id=str(mensaje.id),
        contenido=mensaje.contenido,
        usuario_envio=str(mensaje.usuario_envio),
        nombre_remitente=usuario_remitente.nombre,
        apellidos_remitente=usuario_remitente.apellidos,
        fecha_envio=mensaje.fecha_envio,
        chat_id=str(mensaje.chat_id) if mensaje.chat_id else None,
        estado=destinatario_registro.estado if destinatario_registro else None,
        fecha_lectura=(
            destinatario_registro.fecha_lectura if destinatario_registro else None
        ),
    )


# ── Endpoints de chats ───────────────────────────────────────────


@router.get("/chats", response_model=list[ChatOutput], summary="Listar chats visibles")
def get_chats_ep(
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Lista los chats visibles para el usuario autenticado."""
    chats = get_chats_visibles(usuario, session)
    return [_chat_to_output(c, usuario, session) for c in chats]


@router.post(
    "/chats",
    response_model=ChatOutput,
    status_code=status.HTTP_201_CREATED,
    summary="Crear Chat",
)
def post_chat_ep(
    datos: ChatCreate,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Crear Chats. Solo el administrador puede crear chats."""
    if usuario.rol != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador puede crear chat",
        )
    chat = crear_chat(datos, usuario, session)
    return _chat_to_output(chat, usuario, session)


@router.get("/chats/{chat_id}", response_model=ChatOutput, summary="Obtener chat")
def get_chat_by_id_ep(
    chat_id: str,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Obtener Chat. Obtiene el detalle de un chat si el usuario puede verlo."""
    chat = get_chat(chat_id, session)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat no encontrado")

    # Chats ocultos solo los ven sus miembros
    if chat.visibilidad == "oculta":
        if not get_membresia(chat.id, usuario.id, session):
            raise HTTPException(status_code=404, detail="Chat no encontrado")

    return _chat_to_output(chat, usuario, session)


@router.put("/chats/{chat_id}", response_model=ChatOutput, summary="Editar chat")
def put_chat_ep(
    chat_id: str,
    datos: ChatUpdate,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Editar chat. Solo el administrador del chat puede editar su configuración."""
    chat = get_chat(chat_id, session)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat no encontrado")
    if not es_admin_chat(chat.id, usuario.id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador del chat puede editarlo",
        )
    chat = editar_chat(chat, datos, session)
    return _chat_to_output(chat, usuario, session)


# ── Endpoints de solicitudes ──────────────────────────────────────


@router.post(
    "/chats/{chat_id}/solicitudes",
    response_model=SolicitudChatOutput,
    status_code=status.HTTP_201_CREATED,
    summary="Unirse o solicitar acceso a un chat",
)
def post_solicitud_ep(
    chat_id: str,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """
    El usuario solicita acceso a un chat.
    - Chat libre: se une directamente (SolicitudChat aceptada + MiembroChat).
    - Chat restringido: crea SolicitudChat pendiente.
    """
    chat = get_chat(chat_id, session)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat no encontrado")
    if chat.visibilidad == "oculta" and not get_membresia(chat.id, usuario.id, session):
        raise HTTPException(status_code=404, detail="Chat no encontrado")

    solicitud, motivo = enviar_solicitud(chat, usuario, session)
    if not solicitud:
        raise HTTPException(status_code=400, detail=motivo)

    u = session.get(Usuario, solicitud.usuario_id)
    return _solicitud_to_output(solicitud, u)


@router.get(
    "/chats/{chat_id}/solicitudes",
    response_model=list[SolicitudChatOutput],
    summary="Listar solicitudes pendientes",
)
def get_solicitudes_ep(
    chat_id: str,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Lista las solicitudes pendientes. Solo administrador del chat."""
    chat = get_chat(chat_id, session)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat no encontrado")
    if not es_admin_chat(chat.id, usuario.id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador puede ver las solicitudes",
        )
    solicitudes = get_solicitudes_pendientes(chat_id, session)
    return [_solicitud_to_output(s, u) for s, u in solicitudes]


@router.patch(
    "/chats/{chat_id}/solicitudes/{solicitud_id}",
    response_model=SolicitudChatOutput,
    summary="Resolver solicitud de acceso",
)
def patch_solicitud_ep(
    chat_id: str,
    solicitud_id: str,
    aceptar: bool,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """El administrador aprueba o rechaza una solicitud pendiente."""
    chat = get_chat(chat_id, session)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat no encontrado")
    if not es_admin_chat(chat.id, usuario.id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador puede resolver solicitudes",
        )

    solicitud = session.get(SolicitudChat, uuid.UUID(solicitud_id))
    if not solicitud or str(solicitud.chat_id) != chat_id:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if solicitud.estado != "pendiente":
        raise HTTPException(status_code=400, detail="La solicitud no está pendiente")

    solicitud, _ = resolver_solicitud(solicitud, aceptar, usuario, session)
    u = session.get(Usuario, solicitud.usuario_id)
    return _solicitud_to_output(solicitud, u)


# ── Endpoints de membresía ────────────────────────────────────────


@router.get(
    "/chats/{chat_id}/miembros",
    response_model=list[MiembroChatOutput],
    summary="Listar miembros del chat",
)
def get_miembros_ep(
    chat_id: str,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Lista los miembros activos de un chat."""
    chat = get_chat(chat_id, session)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat no encontrado")
    if (
        not get_membresia(chat.id, usuario.id, session)
        and usuario.rol != "administrador"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No tienes acceso a este chat"
        )
    miembros = get_miembros(chat_id, session)
    return [_miembro_to_output(m, u) for m, u in miembros]


@router.patch(
    "/chats/{chat_id}/miembros/{miembro_id}/rol",
    response_model=MiembroChatOutput,
    summary="Cambiar rol de un miembro",
)
def patch_miembro_rol_ep(
    chat_id: str,
    miembro_id: str,
    datos: MiembroRolUpdate,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """El administrador cambia el rol de un miembro."""
    chat = get_chat(chat_id, session)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat no encontrado")
    if not es_admin_chat(chat.id, usuario.id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador puede cambiar roles",
        )
    if datos.rol not in ("miembro", "administrador"):
        raise HTTPException(
            status_code=400, detail="El rol debe ser 'miembro' o 'administrador'"
        )

    miembro = session.get(MiembroChat, uuid.UUID(miembro_id))
    if not miembro or str(miembro.chat_id) != chat_id:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")
    if miembro.estado != "activo":
        raise HTTPException(status_code=400, detail="El usuario no es miembro activo")
    if datos.rol == "miembro":
        usuario_miembro = session.get(Usuario, miembro.usuario_id)
        if usuario_miembro and usuario_miembro.rol == "administrador":
            raise HTTPException(
                status_code=400,
                detail="No se puede degradar a un usuario con rol de administrador del sistema",
            )

    miembro, motivo = cambiar_rol(miembro, datos.rol, session)
    if not miembro:
        raise HTTPException(status_code=400, detail=motivo)

    u = session.get(Usuario, miembro.usuario_id)
    return _miembro_to_output(miembro, u)


@router.patch(
    "/chats/{chat_id}/miembros/{miembro_id}/baja",
    response_model=MiembroChatOutput,
    summary="Dar de baja a un miembro",
)
def patch_miembro_baja_ep(
    chat_id: str,
    miembro_id: str,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """
    Baja lógica de un miembro.
    El administrador puede dar de baja a cualquier miembro.
    Un miembro puede darse de baja a sí mismo.
    """
    chat = get_chat(chat_id, session)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat no encontrado")

    miembro = session.get(MiembroChat, uuid.UUID(miembro_id))
    if not miembro or str(miembro.chat_id) != chat_id:
        raise HTTPException(status_code=404, detail="Miembro no encontrado")
    if miembro.estado != "activo":
        raise HTTPException(status_code=400, detail="El usuario no es miembro activo")

    es_propio = miembro.usuario_id == usuario.id
    if not es_propio and not es_admin_chat(chat.id, usuario.id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para dar de baja a este miembro",
        )

    miembro, motivo = dar_baja_miembro(miembro, usuario, session)
    if not miembro:
        raise HTTPException(status_code=400, detail=motivo)

    u = session.get(Usuario, miembro.usuario_id)
    return _miembro_to_output(miembro, u)


# ── Endpoints de invitaciones ─────────────────────────────────────


@router.post(
    "/chats/{chat_id}/invitaciones",
    response_model=InvitacionChatOutput,
    status_code=status.HTTP_201_CREATED,
    summary="Enviar invitación a un usuario",
)
def post_invitacion_ep(
    chat_id: str,
    datos: InvitacionChatCreate,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """El administrador envía una invitación a un usuario."""
    chat = get_chat(chat_id, session)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat no encontrado")
    if not es_admin_chat(chat.id, usuario.id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador puede enviar invitaciones",
        )

    destinatario = session.get(Usuario, uuid.UUID(datos.usuario_destinatario))
    if not destinatario:
        raise HTTPException(
            status_code=404, detail="Usuario destinatario no encontrado"
        )

    invitacion, motivo = enviar_invitacion(chat, destinatario, usuario, session)
    if not invitacion:
        raise HTTPException(status_code=400, detail=motivo)

    return _invitacion_to_output(invitacion, chat, destinatario, usuario)


@router.get(
    "/invitaciones",
    response_model=list[InvitacionChatOutput],
    summary="Listar invitaciones pendientes recibidas",
)
def get_invitaciones_ep(
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Lista las invitaciones pendientes del usuario autenticado."""
    resultados = get_invitaciones_pendientes_usuario(usuario.id, session)
    return [
        _invitacion_to_output(inv, chat, usuario, invitador)
        for inv, chat, invitador in resultados
    ]


@router.patch(
    "/invitaciones/{invitacion_id}",
    response_model=InvitacionChatOutput,
    summary="Aceptar o rechazar una invitación",
)
def patch_invitacion_ep(
    invitacion_id: str,
    aceptar: bool,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """El usuario acepta o rechaza una invitación recibida."""
    invitacion = session.get(InvitacionChat, uuid.UUID(invitacion_id))
    if not invitacion or invitacion.usuario_destinatario != usuario.id:
        raise HTTPException(status_code=404, detail="Invitación no encontrada")
    if invitacion.estado != "pendiente":
        raise HTTPException(status_code=400, detail="La invitación no está pendiente")

    invitacion, _ = resolver_invitacion(invitacion, aceptar, session)

    chat = session.get(Chat, invitacion.chat_id)
    invitador = session.get(Usuario, invitacion.usuario_invitacion)
    return _invitacion_to_output(invitacion, chat, usuario, invitador)


# ── Endpoints de mensajes de chat ───────────────────────────────


@router.get(
    "/chats/{chat_id}/mensajes",
    response_model=list[MensajeOutput],
    summary="Listar mensajes de un chat",
)
def get_mensajes_chat_ep(
    chat_id: str,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Lista los mensajes de un chat. Solo miembros activos."""
    chat = get_chat(chat_id, session)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat no encontrado")
    if not get_membresia(chat.id, usuario.id, session):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No eres miembro de este chat"
        )

    resultados = get_mensajes_chat(chat_id, usuario.id, session)
    output = [_mensaje_to_output(m, u, d) for m, u, d in resultados]

    ids_no_leidos = [m.id for m, _, d in resultados if d and d.estado != "leido"]
    if ids_no_leidos:
        marcar_mensajes_leidos(ids_no_leidos, usuario.id, session)

    return output


@router.post(
    "/chats/{chat_id}/mensajes",
    response_model=MensajeOutput,
    status_code=status.HTTP_201_CREATED,
    summary="Enviar mensaje a un chat",
)
def post_mensaje_chat_ep(
    chat_id: str,
    datos: MensajeCreate,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Envía un mensaje a un chat."""
    chat = get_chat(chat_id, session)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat no encontrado")

    mensaje, motivo = enviar_mensaje_chat(datos.contenido, usuario, chat, session)
    if not mensaje:
        raise HTTPException(status_code=400, detail=motivo)

    u = session.get(Usuario, mensaje.usuario_envio)
    return _mensaje_to_output(mensaje, u, None)


# ── Endpoints de mensajes directos ───────────────────────────────


@router.get(
    "/directos/{usuario_id}",
    response_model=list[MensajeOutput],
    summary="Listar mensajes directos con un usuario",
)
def get_mensajes_directos_ep(
    usuario_id: str,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Lista los mensajes directos entre el usuario actual y otro."""
    otro = session.get(Usuario, uuid.UUID(usuario_id))
    if not otro:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    resultados = get_mensajes_directos(usuario.id, otro.id, session)
    output = [_mensaje_to_output(m, u, d) for m, u, d in resultados]

    ids_no_leidos = [
        m.id
        for m, _, d in resultados
        if d and d.estado != "leido" and m.usuario_envio != usuario.id
    ]
    if ids_no_leidos:
        marcar_mensajes_leidos(ids_no_leidos, usuario.id, session)

    return output


@router.post(
    "/directos",
    response_model=MensajeOutput,
    status_code=status.HTTP_201_CREATED,
    summary="Enviar mensaje directo",
)
def post_mensaje_directo_ep(
    datos: MensajeCreate,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Envía un mensaje directo a otro usuario."""
    if not datos.usuario_destinatario:
        raise HTTPException(
            status_code=400, detail="Debes indicar el usuario destinatario"
        )

    destinatario = session.get(Usuario, uuid.UUID(datos.usuario_destinatario))
    if not destinatario:
        raise HTTPException(
            status_code=404, detail="Usuario destinatario no encontrado"
        )
    if destinatario.id == usuario.id:
        raise HTTPException(
            status_code=400, detail="No puedes enviarte un mensaje a ti mismo"
        )

    mensaje = enviar_mensaje_directo(datos.contenido, usuario, destinatario, session)
    u = session.get(Usuario, mensaje.usuario_envio)
    return _mensaje_to_output(mensaje, u, None)


# ── Endpoints de historial ────────────────────────────────────────


@router.get(
    "/historial/directos",
    response_model=list[ConversacionDirectaOutput],
    summary="Historial de conversaciones directas",
)
def get_historial_directos_ep(
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Historial de conversaciones directas con indicador de no leídos."""
    datos = get_historial_directo(usuario.id, session)
    return [ConversacionDirectaOutput(**d) for d in datos]


@router.get(
    "/historial/chats",
    response_model=list[ChatResumenOutput],
    summary="Historial de chats",
)
def get_historial_chats_ep(
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Historial de chats del usuario con indicador de no leídos."""
    datos = get_historial_chats(usuario.id, session)
    return [ChatResumenOutput(**d) for d in datos]
