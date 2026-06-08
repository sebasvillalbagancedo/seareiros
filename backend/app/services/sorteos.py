from sqlmodel import Session, select, func
from datetime import datetime
from fastapi import HTTPException, status
from app.models.sorteo import Sorteo
from app.models.inscripcion_sorteo import InscripcionSorteo
from app.models.socio import Socio
from app.models.usuario import Usuario
from app.models.usuario_socio import UsuarioSocio
from app.schemas.sorteo import SorteoCreate, SorteoUpdate
import uuid
import random

# ── Helpers ───────────────────────────────────────────────────────


def _validar_requisitos_socio(socio: Socio, sorteo: Sorteo) -> tuple[bool, str]:
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
            UsuarioSocio.fecha_revocacion == None
        )
    ).first()
    if not permiso:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso sobre este socio",
        )

def _resolver_sorteo(
    sorteo: Sorteo, session: Session
) -> tuple[Sorteo, list[InscripcionSorteo]]:
    """
    Lógica pura de resolución de un sorteo, sin comprobación de autorización.
    Usada tanto por el endpoint (previa comprobación de rol) como por el planificador.
    Si no hay inscritos, cancela el sorteo directamente en base de datos.
    Devuelve (sorteo_actualizado, lista_de_ganadores).
    """
    inscripciones = session.exec(
        select(InscripcionSorteo).where(
            InscripcionSorteo.sorteo_id == sorteo.id,
            InscripcionSorteo.estado == "activa",
        )
    ).all()

    if not inscripciones:
        sorteo.estado = "cancelado"
        sorteo.motivo_cancelacion = (
            "No hay socios inscritos en el momento de la resolución"
        )
        session.add(sorteo)
        session.commit()
        session.refresh(sorteo)
        return sorteo, []

    num_ganadores = min(sorteo.numero_premios, len(inscripciones))
    ganadores = random.sample(list(inscripciones), num_ganadores)

    for inscripcion in ganadores:
        inscripcion.es_ganador = True
        session.add(inscripcion)

    sorteo.estado = "resuelto"
    session.add(sorteo)
    session.commit()

    for inscripcion in ganadores:
        session.refresh(inscripcion)
    session.refresh(sorteo)

    return sorteo, ganadores

# ── Sorteos ───────────────────────────────────────────────────────


def contar_inscritos(sorteo_id: uuid.UUID, session: Session) -> int:
    """Devuelve el número de inscripciones activas de un sorteo."""
    return session.exec(
        select(func.count(InscripcionSorteo.id)).where(
            InscripcionSorteo.sorteo_id == sorteo_id,
            InscripcionSorteo.estado == "activa",
        )
    ).one()


def get_sorteos(session: Session) -> list[Sorteo]:
    """
    Devuelve los sorteos cuya fecha de celebración es posterior a hoy (disponibles).
    Todos los usuarios autenticados ven el listado completo.
    """
    ahora = datetime.now()
    stmt = select(Sorteo).where(Sorteo.fecha_celebracion > ahora)
    stmt = stmt.order_by(Sorteo.fecha_celebracion.asc())
    return session.exec(stmt).all()


def get_historico_sorteos(session: Session) -> list[Sorteo]:
    """
    Devuelve los sorteos cuya fecha de celebración ya ha pasado (histórico).
    Todos los usuarios autenticados ven el histórico completo.
    """
    ahora = datetime.now()
    stmt = select(Sorteo).where(Sorteo.fecha_celebracion <= ahora)
    stmt = stmt.order_by(Sorteo.fecha_celebracion.desc())
    return session.exec(stmt).all()


def get_sorteo(sorteo_id: str, session: Session) -> Sorteo | None:
    """Devuelve un sorteo por su ID o None si no existe."""
    return session.get(Sorteo, uuid.UUID(sorteo_id))


def crear_sorteo(datos: SorteoCreate, usuario: Usuario, session: Session) -> Sorteo:
    """Crea un nuevo sorteo. Solo el administrador puede invocar esta función."""
    if usuario.rol != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador puede crear sorteos",
        )
    sorteo = Sorteo(**datos.model_dump(), usuario_creacion=usuario.id)
    session.add(sorteo)
    session.commit()
    session.refresh(sorteo)
    return sorteo


def editar_sorteo(sorteo: Sorteo, datos: SorteoUpdate, usuario: Usuario, session: Session) -> Sorteo:
    """
    Edita los datos de un sorteo existente.
    Solo el administrador puede editar y solo en estado abierto.
    """
    if usuario.rol != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador puede editar sorteos",
        )
    if sorteo.estado != "abierto":
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden editar sorteos en estado abierto",
        )
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(sorteo, campo, valor)
    session.add(sorteo)
    session.commit()
    session.refresh(sorteo)
    return sorteo


def cancelar_sorteo(sorteo: Sorteo, motivo: str, usuario: Usuario, session: Session) -> Sorteo:
    """
    Cancela un sorteo.
    Solo el administrador puede cancelar y solo si no está ya resuelto o cancelado.
    """
    if usuario.rol != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador puede cancelar sorteos",
        )
    if sorteo.estado in ("resuelto", "cancelado"):
        raise HTTPException(
            status_code=400,
            detail="No se puede cancelar un sorteo ya resuelto o cancelado",
        )
    sorteo.estado = "cancelado"
    sorteo.motivo_cancelacion = motivo
    session.add(sorteo)
    session.commit()
    session.refresh(sorteo)
    return sorteo


# ── Inscripciones ─────────────────────────────────────────────────


def get_inscripciones(
    sorteo_id: str, session: Session
) -> list[tuple[InscripcionSorteo, Socio]]:
    """
    Devuelve las inscripciones de un sorteo junto con los datos del socio.
    """
    statement = (
        select(InscripcionSorteo, Socio)
        .join(Socio, Socio.id == InscripcionSorteo.socio_id)
        .where(InscripcionSorteo.sorteo_id == uuid.UUID(sorteo_id))
        .order_by(Socio.apellidos, Socio.nombre)
    )
    return session.exec(statement).all()


def inscribir_socio(
    sorteo: Sorteo, socio: Socio, usuario: Usuario, session: Session
) -> tuple[InscripcionSorteo | None, str]:
    """
    Inscribe a un socio en un sorteo.
    Devuelve (inscripcion, '') si OK, (None, motivo) si no se puede inscribir.
    """
    # Verificar permiso del usuario sobre el socio
    _verificar_permiso_sobre_socio(usuario, socio, session)
    
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
            InscripcionSorteo.estado == "activa",
        )
    ).first()
    if existente:
        return None, "El socio ya está inscrito en este sorteo"

    # Verificar que el socio está activo
    if socio.estado != "activo":
        return None, "El socio no está en estado activo"

    # Verificar requisitos de participación
    cumple, motivo = _validar_requisitos_socio(socio, sorteo)
    if not cumple:
        return None, motivo

    # Crear la inscripción
    inscripcion = InscripcionSorteo(
        sorteo_id=sorteo.id, socio_id=socio.id, usuario_inscripcion=usuario.id
    )
    session.add(inscripcion)
    session.commit()
    session.refresh(inscripcion)
    return inscripcion, ""


def cancelar_inscripcion(
    inscripcion: InscripcionSorteo, usuario: Usuario, session: Session
) -> InscripcionSorteo:
    """
    Cancela la inscripción de un socio en un sorteo.
    Verifica que el sorteo esté abierto, que la inscripción esté activa
    y que el usuario tenga permiso sobre el socio.
    """
    sorteo = session.get(Sorteo, inscripcion.sorteo_id)
    if not sorteo or sorteo.estado not in ("abierto",):
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden cancelar inscripciones en sorteos abiertos",
        )
    if inscripcion.estado != "activa":
        raise HTTPException(status_code=400, detail="La inscripción no está activa")

    socio = session.get(Socio, inscripcion.socio_id)
    _verificar_permiso_sobre_socio(usuario, socio, session)

    inscripcion.estado = "cancelada"
    inscripcion.fecha_cancelacion = datetime.now()
    inscripcion.usuario_cancelacion = usuario.id
    session.add(inscripcion)
    session.commit()
    session.refresh(inscripcion)
    return inscripcion


# ── Resolución del sorteo ─────────────────────────────────────────


def resolver_sorteo(
    sorteo: Sorteo, usuario: Usuario, session: Session
) -> tuple[Sorteo, list[InscripcionSorteo]]:
    """
    Resuelve el sorteo seleccionando ganadores aleatoriamente.
    Solo el administrador puede resolver manualmente.
    Verifica que el sorteo esté en un estado que permita resolución.
    Si no hay inscritos, cancela el sorteo.
    Devuelve (sorteo_actualizado, lista_de_ganadores).
    """
    if usuario.rol != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador puede resolver sorteos",
        )
    if sorteo.estado not in ("abierto", "cerrado", "pendiente"):
        raise HTTPException(
            status_code=400,
            detail="El sorteo no está en un estado que permita su resolución",
        )

    return _resolver_sorteo(sorteo, session)


def resolver_sorteo_automatico(
    sorteo: Sorteo, session: Session
) -> tuple[Sorteo, list[InscripcionSorteo]]:
    """
    Resuelve el sorteo desde el planificador automático, sin usuario asociado.
    """
    return _resolver_sorteo(sorteo, session)
