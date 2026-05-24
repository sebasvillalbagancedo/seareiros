from sqlmodel import Session, select, asc
from app.models.socio import Socio
from app.models.usuario_socio import UsuarioSocio
from app.models.usuario import Usuario
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
            UsuarioSocio.usuario_id == usuario.id, UsuarioSocio.fecha_revocacion == None
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
