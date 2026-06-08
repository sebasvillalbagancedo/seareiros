from datetime import datetime
from sqlmodel import Session, select, asc
from fastapi import HTTPException, status
from app.models.socio import Socio
from app.models.usuario_socio import UsuarioSocio
from app.models.usuario import Usuario
from app.schemas.socio import SocioCreate, SocioUpdate
import uuid


def get_socios_usuario(usuario: Usuario, session: Session) -> list[Socio]:
    """
    Devuelve la lista de socios a los que el usuario tiene acceso.
    """
    if usuario.rol == "administrador":
        return session.exec(select(Socio).order_by(asc(Socio.numero_socio))).all()

    statement = (
        select(Socio)
        .join(UsuarioSocio, UsuarioSocio.socio_id == Socio.id)
        .where(
            UsuarioSocio.usuario_id == usuario.id, 
            UsuarioSocio.fecha_revocacion == None
        )
        .order_by(asc(Socio.numero_socio))
    )
    return session.exec(statement).all()


def get_socio_usuario(
    socio_id: str, usuario: Usuario, session: Session
) -> Socio | None:
    """
    Devuelve el socio si el usuario tiene acceso a él, None si no.
    """
    socio = session.get(Socio, uuid.UUID(socio_id))
    if not socio:
        return None
    if usuario.rol == "administrador":
        return socio

    relacion = session.exec(
        select(UsuarioSocio).where(
            UsuarioSocio.usuario_id == usuario.id,
            UsuarioSocio.socio_id == socio.id,
            UsuarioSocio.fecha_revocacion == None,
        )
    ).first()
    return socio if relacion else None

def crear_socio(datos: SocioCreate, usuario: Usuario, session: Session) -> Socio:
    """Crea un nuevo socio. Solo el administrador puede invocar esta función."""
    if usuario.rol != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador puede crear socios",
        )
    socio = Socio(**datos.model_dump())
    session.add(socio)
    session.commit()
    session.refresh(socio)
    return socio


def editar_socio(
    socio: Socio, datos: SocioUpdate, session: Session
) -> Socio:
    """Edita los datos de un socio."""
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(socio, campo, valor)
    socio.fecha_actualizacion = datetime.now()
    session.add(socio)
    session.commit()
    session.refresh(socio)
    return socio


def dar_baja_socio(
    socio_id: str, usuario: Usuario, session: Session
) -> Socio:
    """Da de baja a un socio. Solo el administrador puede invocar esta función."""
    if usuario.rol != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador puede dar de baja socios",
        )
    socio = session.get(Socio, uuid.UUID(socio_id))
    if not socio:
        raise HTTPException(status_code=404, detail="Socio no encontrado")
    if socio.estado == "baja":
        raise HTTPException(
            status_code=400, detail="El socio ya está en estado de baja"
        )
    socio.estado = "baja"
    socio.fecha_actualizacion = datetime.now()
    session.add(socio)
    session.commit()
    session.refresh(socio)
    return socio


def get_permisos_socio(
    socio_id: str, usuario: Usuario, session: Session
) -> list[UsuarioSocio]:
    """Lista los permisos vigentes de un socio. Solo el administrador."""
    if usuario.rol != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador puede consultar permisos",
        )
    return session.exec(
        select(UsuarioSocio).where(
            UsuarioSocio.socio_id == uuid.UUID(socio_id),
            UsuarioSocio.fecha_revocacion == None
        )
    ).all()


def asignar_permiso(
    socio_id: str, usuario_id: str, usuario: Usuario, session: Session
) -> None:
    """Asigna un socio a un usuario normal. Solo el administrador."""
    if usuario.rol != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador puede asignar permisos",
        )
    existente = session.exec(
        select(UsuarioSocio).where(
            UsuarioSocio.usuario_id == uuid.UUID(usuario_id),
            UsuarioSocio.socio_id == uuid.UUID(socio_id),
            UsuarioSocio.fecha_revocacion == None
        )
    ).first()
    if existente:
        raise HTTPException(
            status_code=400, detail="El permiso ya existe y está vigente"
        )
    relacion = UsuarioSocio(
        usuario_id=uuid.UUID(usuario_id),
        socio_id=uuid.UUID(socio_id),
        usuario_asignacion=usuario.id,
    )
    session.add(relacion)
    session.commit()


def revocar_permiso(
    socio_id: str, usuario_id: str, usuario: Usuario, session: Session
) -> None:
    """Revoca el permiso de un usuario sobre un socio. Solo el administrador."""
    if usuario.rol != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador puede revocar permisos",
        )
    relacion = session.exec(
        select(UsuarioSocio).where(
            UsuarioSocio.usuario_id == uuid.UUID(usuario_id),
            UsuarioSocio.socio_id == uuid.UUID(socio_id),
            UsuarioSocio.fecha_revocacion == None
        )
    ).first()
    if not relacion:
        raise HTTPException(
            status_code=404, detail="No existe un permiso vigente para revocar"
        )
    relacion.fecha_revocacion = datetime.now()
    relacion.usuario_revocacion = usuario.id
    session.add(relacion)
    session.commit()

