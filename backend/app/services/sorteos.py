from sqlmodel import Session, select, func
from datetime import datetime
from app.models.sorteo import Sorteo
from app.models.inscripcion_sorteo import InscripcionSorteo
from app.models.socio import Socio
from app.models.usuario import Usuario
from app.schemas.sorteo import SorteoCreate, SorteoUpdate
import uuid
import random


# ── Helpers de validación de requisitos ──────────────────────────

def validar_requisitos_socio(socio: Socio, sorteo: Sorteo) -> tuple[bool, str]:
    """
    Verifica si un socio cumple los requisitos de participación del sorteo.
    Devuelve (True, '') si cumple, (False, motivo) si no cumple.
    """
    # Verificación de fecha de nacimiento máxima (edad mínima)
    if sorteo.fecha_nacimiento_maxima:
        if socio.fecha_nacimiento is None:
            return False, "El socio no tiene fecha de nacimiento registrada"
        if socio.fecha_nacimiento > sorteo.fecha_nacimiento_maxima:
            return False, (
                f"El socio no cumple la edad mínima requerida "
                f"(nacido antes de {sorteo.fecha_nacimiento_maxima})"
            )

    # Verificación de fecha de nacimiento mínima (edad máxima)
    if sorteo.fecha_nacimiento_minima:
        if socio.fecha_nacimiento is None:
            return False, "El socio no tiene fecha de nacimiento registrada"
        if socio.fecha_nacimiento < sorteo.fecha_nacimiento_minima:
            return False, (
                f"El socio supera la edad máxima permitida "
                f"(nacido después de {sorteo.fecha_nacimiento_minima})"
            )

    # Verificación de antigüedad mínima
    if sorteo.fecha_alta_maxima:
        if socio.fecha_alta > sorteo.fecha_alta_maxima:
            return False, (
                f"El socio no cumple la antigüedad mínima requerida "
                f"(dado de alta antes de {sorteo.fecha_alta_maxima})"
            )

    return True, ""


# ── Sorteos ───────────────────────────────────────────────────────

def contar_inscritos(sorteo_id: uuid.UUID, session: Session) -> int:
    """Devuelve el número de inscripciones activas de un sorteo."""
    return session.exec(
        select(func.count(InscripcionSorteo.id)).where(
            InscripcionSorteo.sorteo_id == sorteo_id,
            InscripcionSorteo.estado == "activa"
        )
    ).one()


def get_sorteos(session: Session) -> list[Sorteo]:
    """Devuelve todos los sorteos ordenados por fecha de celebración."""
    return session.exec(
        select(Sorteo).order_by(Sorteo.fecha_celebracion.asc())
    ).all()


def get_sorteo(sorteo_id: str, session: Session) -> Sorteo | None:
    """Devuelve un sorteo por su ID o None si no existe."""
    return session.get(Sorteo, uuid.UUID(sorteo_id))


def crear_sorteo(datos: SorteoCreate, usuario: Usuario, session: Session) -> Sorteo:
    """Crea un nuevo sorteo."""
    sorteo = Sorteo(
        **datos.model_dump(),
        usuario_creacion=usuario.id
    )
    session.add(sorteo)
    session.commit()
    session.refresh(sorteo)
    return sorteo


def editar_sorteo(sorteo: Sorteo, datos: SorteoUpdate, session: Session) -> Sorteo:
    """Edita los datos de un sorteo existente. Solo en estado abierto."""
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(sorteo, campo, valor)
    session.add(sorteo)
    session.commit()
    session.refresh(sorteo)
    return sorteo


def cancelar_sorteo(sorteo: Sorteo, motivo: str, session: Session) -> Sorteo:
    """Cancela un sorteo e informa el motivo."""
    sorteo.estado             = "cancelado"
    sorteo.motivo_cancelacion = motivo
    session.add(sorteo)
    session.commit()
    session.refresh(sorteo)
    return sorteo


# ── Inscripciones ─────────────────────────────────────────────────

def get_inscripciones(sorteo_id: str, session: Session) -> list[tuple[InscripcionSorteo, Socio]]:
    """
    Devuelve las inscripciones activas de un sorteo junto con los datos del socio.
    """
    statement = (
        select(InscripcionSorteo, Socio)
        .join(Socio, Socio.id == InscripcionSorteo.socio_id)
        .where(
            InscripcionSorteo.sorteo_id == uuid.UUID(sorteo_id),
            InscripcionSorteo.estado == "activa"
        )
        .order_by(Socio.apellidos, Socio.nombre)
    )
    return session.exec(statement).all()


def inscribir_socio(
    sorteo: Sorteo,
    socio: Socio,
    usuario: Usuario,
    session: Session
) -> tuple[InscripcionSorteo | None, str]:
    """
    Inscribe a un socio en un sorteo.
    Devuelve (inscripcion, '') si OK, (None, motivo) si no se puede inscribir.
    """
    # Verificar que el sorteo está abierto
    if sorteo.estado != "abierto":
        return None, "El sorteo no está en estado abierto"

    # Verificar que el plazo de inscripción está activo
    ahora = datetime.now()
    if ahora < sorteo.fecha_inicio_inscripcion:
        return None, "El plazo de inscripción aún no ha comenzado"
    if ahora > sorteo.fecha_fin_inscripcion:
        return None, "El plazo de inscripción ha finalizado"

    # Verificar que quedan plazas
    if sorteo.maximo_inscritos is not None:
        inscritos = contar_inscritos(sorteo.id, session)
        if inscritos >= sorteo.maximo_inscritos:
            return None, "No quedan plazas disponibles en este sorteo"

    # Verificar que el socio no está ya inscrito
    existente = session.exec(
        select(InscripcionSorteo).where(
            InscripcionSorteo.sorteo_id == sorteo.id,
            InscripcionSorteo.socio_id == socio.id,
            InscripcionSorteo.estado == "activa"
        )
    ).first()
    if existente:
        return None, "El socio ya está inscrito en este sorteo"

    # Verificar que el socio está activo
    if socio.estado != "activo":
        return None, "El socio no está en estado activo"

    # Verificar requisitos de participación
    cumple, motivo = validar_requisitos_socio(socio, sorteo)
    if not cumple:
        return None, motivo

    # Crear la inscripción
    inscripcion = InscripcionSorteo(
        sorteo_id=sorteo.id,
        socio_id=socio.id,
        usuario_inscripcion=usuario.id
    )
    session.add(inscripcion)
    session.commit()
    session.refresh(inscripcion)
    return inscripcion, ""


def cancelar_inscripcion(
    inscripcion: InscripcionSorteo,
    usuario: Usuario,
    session: Session
) -> InscripcionSorteo:
    """Cancela la inscripción de un socio en un sorteo."""
    inscripcion.estado             = "cancelada"
    inscripcion.fecha_cancelacion  = datetime.now()
    inscripcion.usuario_cancelacion = usuario.id
    session.add(inscripcion)
    session.commit()
    session.refresh(inscripcion)
    return inscripcion


# ── Resolución del sorteo ─────────────────────────────────────────

def resolver_sorteo(sorteo: Sorteo, session: Session) -> tuple[Sorteo, list[InscripcionSorteo]]:
    """
    Resuelve el sorteo seleccionando ganadores aleatoriamente.
    Si no hay inscritos, cancela el sorteo.
    Devuelve (sorteo_actualizado, lista_de_ganadores).
    """
    # Obtener inscripciones activas
    inscripciones = session.exec(
        select(InscripcionSorteo).where(
            InscripcionSorteo.sorteo_id == sorteo.id,
            InscripcionSorteo.estado == "activa"
        )
    ).all()

    # Sin inscritos: cancelar el sorteo
    if not inscripciones:
        sorteo = cancelar_sorteo(
            sorteo,
            "No hay socios inscritos en el momento de la resolución",
            session
        )
        return sorteo, []

    # Seleccionar ganadores aleatoriamente
    num_ganadores = min(sorteo.numero_premios, len(inscripciones))
    ganadores     = random.sample(list(inscripciones), num_ganadores)

    # Marcar ganadores
    for inscripcion in ganadores:
        inscripcion.es_ganador = True
        session.add(inscripcion)

    # Actualizar estado del sorteo
    sorteo.estado = "resuelto"
    session.add(sorteo)
    session.commit()

    for inscripcion in ganadores:
        session.refresh(inscripcion)
    session.refresh(sorteo)

    return sorteo, ganadores