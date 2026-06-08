from sqlmodel import Session, select, func
from datetime import datetime
from fastapi import HTTPException, status
from app.models.evento import Evento
from app.models.inscripcion_evento import InscripcionEvento
from app.models.socio import Socio
from app.models.usuario import Usuario
from app.models.usuario_socio import UsuarioSocio
from app.schemas.evento import EventoCreate, EventoUpdate
import uuid

# ── Helpers ───────────────────────────────────────────────────────


def _validar_requisitos_socio(socio: Socio, evento: Evento) -> tuple[bool, str]:
    """
    Verifica si un socio cumple los requisitos de participación en un evento.
    Devuelve (True, '') si cumple, (False, motivo) si no cumple.
    """
    # Verificación de fecha de nacimiento máxima (edad mínima)
    if evento.fecha_nacimiento_maxima:
        if socio.fecha_nacimiento is None:
            return False, "El socio no tiene fecha de nacimiento registrada"
        if socio.fecha_nacimiento > evento.fecha_nacimiento_maxima:
            return False, (
                f"El socio no cumple la edad mínima requerida "
                f"(nacido antes de {evento.fecha_nacimiento_maxima})"
            )

    # Verificación de fecha de nacimiento mínima (edad máxima)
    if evento.fecha_nacimiento_minima:
        if socio.fecha_nacimiento is None:
            return False, "El socio no tiene fecha de nacimiento registrada"
        if socio.fecha_nacimiento < evento.fecha_nacimiento_minima:
            return False, (
                f"El socio supera la edad máxima permitida "
                f"(nacido después de {evento.fecha_nacimiento_minima})"
            )

    # Verificación de antigüedad mínima
    if evento.fecha_alta_maxima:
        if socio.fecha_alta > evento.fecha_alta_maxima:
            return False, (
                f"El socio no cumple la antigüedad mínima requerida "
                f"(dado de alta antes de {evento.fecha_alta_maxima})"
            )

    return True, ""


def _socio_ids_de_usuario(session: Session, usuario_id: uuid.UUID) -> list[uuid.UUID]:
    """Devuelve los UUIDs de los socios activos asignados al usuario."""
    return session.exec(
        select(UsuarioSocio.socio_id).where(
            UsuarioSocio.usuario_id == usuario_id,
            UsuarioSocio.fecha_revocacion == None,
        )
    ).all()

def _verificar_permiso_sobre_socio(
    usuario: Usuario, socio: Socio, session: Session
) -> None:
    """
    Verifica que el usuario tiene permiso sobre el socio.
    Los administradores tienen acceso a cualquier socio.
    Los usuarios normales solo pueden operar con sus socios asignados.
    Lanza HTTPException 403 si no tiene permiso.
    """
    if usuario.rol == "administrador":
        return
    permiso = session.exec(
        select(UsuarioSocio).where(
            UsuarioSocio.usuario_id == usuario.id,
            UsuarioSocio.socio_id == socio.id,
            UsuarioSocio.fecha_revocacion == None,  # noqa: E711
        )
    ).first()
    if not permiso:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso sobre este socio",
        )
    
# ── Eventos ───────────────────────────────────────────────────────


def contar_inscritos(evento_id: uuid.UUID, session: Session) -> int:
    """Devuelve el número de inscripciones no canceladas en un evento."""
    return session.exec(
        select(func.count(InscripcionEvento.id)).where(
            InscripcionEvento.evento_id == evento_id,
            InscripcionEvento.estado.in_(["pendiente", "confirmada"]),
        )
    ).one()


def get_eventos(session: Session) -> list[Evento]:
    """
    Devuelve los eventos cuya fecha de celebración es posterior a hoy (disponibles).
    """
    ahora = datetime.now()
    stmt = select(Evento).where(Evento.fecha_celebracion > ahora)
    stmt = stmt.order_by(Evento.fecha_celebracion.asc())
    return session.exec(stmt).all()


def get_historico_eventos(session: Session) -> list[Evento]:
    """
    Devuelve todos los eventos cuya fecha de celebración ya ha pasado.
    Solo para administradores.
    """
    ahora = datetime.now()
    stmt = select(Evento).where(Evento.fecha_celebracion <= ahora)
    stmt = stmt.order_by(Evento.fecha_celebracion.desc())
    return session.exec(stmt).all()


def get_historico_eventos_usuario(
    session: Session, usuario_id: uuid.UUID
) -> list[Evento]:
    """
    Variante del histórico para usuarios normales.
    Solo devuelve eventos en los que alguno de sus socios asignados tiene inscripción.
    """
    ahora = datetime.now()
    socio_ids = _socio_ids_de_usuario(session, usuario_id)

    if not socio_ids:
        return []

    stmt = (
        select(Evento)
        .join(InscripcionEvento, InscripcionEvento.evento_id == Evento.id)
        .where(
            Evento.fecha_celebracion <= ahora, InscripcionEvento.socio_id.in_(socio_ids)
        )
        .distinct()
        .order_by(Evento.fecha_celebracion.desc())
    )
    return session.exec(stmt).all()


def get_evento(evento_id: str, session: Session) -> Evento | None:
    """Devuelve un evento por su ID o None si no existe."""
    return session.get(Evento, uuid.UUID(evento_id))


def crear_evento(datos: EventoCreate, usuario: Usuario, session: Session) -> Evento:
    """Crea un nuevo evento."""
    if usuario.rol != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador puede crear eventos",
        )
    evento = Evento(**datos.model_dump(), usuario_creacion=usuario.id)
    session.add(evento)
    session.commit()
    session.refresh(evento)
    return evento


def editar_evento(evento: Evento, datos: EventoUpdate, usuario: Usuario, session: Session) -> Evento:
    """Edita los datos de un evento existente. Solo en estado abierto."""
    if usuario.rol != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador puede editar eventos",
        )
    if evento.estado != "abierto":
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden editar eventos en estado abierto",
        )
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(evento, campo, valor)
    session.add(evento)
    session.commit()
    session.refresh(evento)
    return evento


def cancelar_evento(
    evento: Evento, motivo: str, usuario: Usuario, session: Session
) -> Evento:
    """
    Cancela un evento.
    Solo el administrador puede cancelar y solo si no está ya cancelado o celebrado.
    """
    if usuario.rol != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador puede cancelar eventos",
        )
    if evento.estado == "cancelado":
        raise HTTPException(status_code=400, detail="El evento ya está cancelado")
    if evento.estado == "celebrado":
        raise HTTPException(status_code=400, detail="El evento ya está celebrado")
    evento.estado = "cancelado"
    evento.motivo_cancelacion = motivo
    evento.fecha_cancelacion = datetime.now()
    evento.usuario_cancelacion = usuario.id
    session.add(evento)
    session.commit()
    session.refresh(evento)
    return evento


def celebrar_evento(evento: Evento, session: Session) -> Evento:
    """
    Marca un evento como celebrado.
    """
    evento.estado = "celebrado"
    session.add(evento)
    session.commit()
    session.refresh(evento)
    return evento


# ── Inscripciones ─────────────────────────────────────────────────


def get_inscripciones(
    evento_id: str, session: Session
) -> list[tuple[InscripcionEvento, Socio]]:
    """
    Devuelve las inscripciones de un evento junto con los datos del socio.
    """
    statement = (
        select(InscripcionEvento, Socio)
        .join(Socio, Socio.id == InscripcionEvento.socio_id)
        .where(InscripcionEvento.evento_id == uuid.UUID(evento_id))
        .order_by(Socio.apellidos, Socio.nombre)
    )
    return session.exec(statement).all()


def inscribir_socio(
    evento: Evento, socio: Socio, usuario: Usuario, session: Session
) -> tuple[InscripcionEvento | None, str]:
    """
    Inscribe a un socio en un evento.
    Verifica permisos del usuario sobre el socio, estado del evento,
    plazas disponibles, duplicados y requisitos de participación.
    Devuelve (inscripcion, '') si OK, (None, motivo) si no es posible.
    """
    # Verificar permisos del usuario sobre el socio
    _verificar_permiso_sobre_socio(usuario, socio, session)

    # Verificar que el evento está abierto
    if evento.estado != "abierto":
        return None, "El evento no está en estado abierto"

    # Verificar que el plazo de inscripción está activo
    ahora = datetime.now()
    if ahora < evento.fecha_inicio_inscripcion:
        return None, "El plazo de inscripción aún no ha comenzado"
    if ahora > evento.fecha_fin_inscripcion:
        return None, "El plazo de inscripción ha finalizado"

    # Verificar que quedan plazas
    inscritos = contar_inscritos(evento.id, session)
    if inscritos >= evento.plazas_disponibles:
        return None, "No quedan plazas disponibles en este evento"

    # Verificar que el socio no está ya inscrito
    existente = session.exec(
        select(InscripcionEvento).where(
            InscripcionEvento.evento_id == evento.id,
            InscripcionEvento.socio_id == socio.id,
            InscripcionEvento.estado.in_(["pendiente", "confirmada"]),
        )
    ).first()
    if existente:
        return None, "El socio ya está inscrito en este evento"

    # Verificar que el socio está activo
    if socio.estado != "activo":
        return None, "El socio no está en estado activo"

    # Verificar requisitos de participación
    cumple, motivo = _validar_requisitos_socio(socio, evento)
    if not cumple:
        return None, motivo

    # Crear la inscripción
    inscripcion = InscripcionEvento(
        evento_id=evento.id, socio_id=socio.id, usuario_inscripcion=usuario.id
    )
    session.add(inscripcion)

    # Si se completan las plazas, marcar el evento como completo
    if inscritos + 1 >= evento.plazas_disponibles:
        evento.estado = "completo"
        session.add(evento)

    session.commit()
    session.refresh(inscripcion)
    return inscripcion, ""


def gestionar_inscripcion(
    inscripcion: InscripcionEvento,
    nuevo_estado: str,
    usuario: Usuario,
    session: Session,
) -> InscripcionEvento:
    """
    El administrador confirma, rechaza o cancela una inscripción.
    Verifica permisos, estado actual de la inscripción y actualiza el evento si procede.
    """
    if usuario.rol != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador puede gestionar inscripciones",
        )
    if inscripcion.estado in ("rechazada", "cancelada"):
        raise HTTPException(
            status_code=400,
            detail="La inscripción ya está finalizada y no puede modificarse",
        )
    evento = session.get(Evento, inscripcion.evento_id)
    inscripcion.estado = nuevo_estado
    inscripcion.usuario_gestion = usuario.id
    inscripcion.fecha_gestion = datetime.now()
    session.add(inscripcion)

    if nuevo_estado in ("rechazada", "cancelada"):
        if evento and evento.estado == "completo":
            evento.estado = "abierto"
            session.add(evento)

    session.commit()
    session.refresh(inscripcion)
    return inscripcion