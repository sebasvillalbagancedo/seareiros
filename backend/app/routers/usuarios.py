from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.database import get_session
from app.schemas.usuario import UsuarioOutput, UsuarioListOutput
from app.dependencies import oauth2_scheme
from app.services.auth import decode_token
from app.models.usuario import Usuario

router = APIRouter(prefix='/usuarios', tags=['Usuarios'])

@router.get('/me', 
            response_model=UsuarioOutput, 
            summary='Obtener Usuario Autenticado')
def get_usuario_me_ep(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
):
    """Devuelve los datos del usuario autenticado a partir del token."""
    try:
        payload = decode_token(token)
        user_id = payload.get('sub')
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Token inválido o expirado'
        )

    usuario = session.get(Usuario, user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail='Usuario no encontrado o inactivo')

    return UsuarioOutput(
        id=str(usuario.id),
        codigo_usuario=usuario.codigo_usuario,
        email=usuario.email,
        nombre=usuario.nombre,
        apellidos=usuario.apellidos,
        rol=usuario.rol,
        estado=usuario.estado
    )

@router.get('', 
            response_model=list[UsuarioListOutput], 
            summary='Listar Usuarios')
def get_usuarios_ep(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
):
    """
    Devuelve la lista de usuarios.
    """
    try:
        payload = decode_token(token)
        user_id = payload.get('sub')
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Token inválido o expirado'
        )

    usuarios = session.exec(select(Usuario)).all()
    return [
        UsuarioListOutput(
            id=str(u.id),
            codigo_usuario=u.codigo_usuario,
            nombre=u.nombre,
            apellidos=u.apellidos,
            rol=u.rol,
            estado=u.estado
        )
        for u in usuarios
        if u.id != user_id  # excluye al propio usuario
    ]