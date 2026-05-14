from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from datetime import datetime
from app.database import get_session
from app.schemas.usuario import LoginInput, TokenOutput, UsuarioOutput, UsuarioListOutput
from app.services.auth import autenticar_usuario, create_token, decode_token
from app.models.usuario import Usuario

router = APIRouter(prefix='/auth', tags=['Autenticación'])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')

@router.post('/login', response_model=TokenOutput)
def login(
    datos: LoginInput, 
    session: Session = Depends(get_session)): 
    usuario = autenticar_usuario(datos.identificador, datos.contrasena, session)
    
    if not usuario:
        # Mensaje genérico: no revelamos si el problema es el usuario o la contraseña
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail='Credenciales incorrectas o usuario inactivo'
            )
    
    # Actualizamos la fecha de última conexión
    usuario.fecha_ult_conexion = datetime.now()
    session.add(usuario)
    session.commit()

    token = create_token({'sub': str(usuario.id), "rol": usuario.rol})
    return TokenOutput(access_token=token)

@router.post('/logout', status_code=status.HTTP_204_NO_CONTENT)
def logout():
    # Con JWT el logout es responsabilidad del cliente: simplemente descarta el  token. 
    # Este endpoint existe para que el frontend tenga un punto de cierre explícito
    return

@router.get('/me', response_model=UsuarioOutput)
def me(
    token: str = Depends(oauth2_scheme), 
    session: Session = Depends(get_session)):
    # Devuelve los datos del usuario autenticado a partir del token
    try:
        payload = decode_token(token)
        user_id = payload.get('sub')
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail='Token inválido o expirado')
    
    usuario = session.get(Usuario, user_id)
    if not usuario:
        raise HTTPException(status_code=404, 
                            detail='Usuario no encontrado o inactivo')
    return UsuarioOutput(
        id=str(usuario.id),
        codigo_usuario=usuario.codigo_usuario,
        email=usuario.email,
        nombre=usuario.nombre,
        apellidos=usuario.apellidos,
        rol=usuario.rol,
        estado=usuario.estado
    )

@router.get('/usuarios', response_model=list[UsuarioListOutput])
def listar_usuarios(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
):
    # Devuelve la lista de usuarios (sin contraseña) solo si el token corresponde a un administrador
    try:
        payload = decode_token(token)
        user_id = payload.get('sub')
        rol     = payload.get('rol')
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Token inválido o expirado')
    if rol != 'administrador':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='Solo el administrador puede consultar los usuarios')
    usuarios = session.exec(select(Usuario)).all()
    return [
        UsuarioListOutput(
            id=str(u.id), codigo_usuario=u.codigo_usuario,
            nombre=u.nombre, apellidos=u.apellidos,
            rol=u.rol, estado=u.estado
        )
        for u in usuarios
        if u.id != user_id  # excluye al propio administrador
    ]