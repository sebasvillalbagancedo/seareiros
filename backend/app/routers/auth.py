from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session
from datetime import datetime
from app.database import get_session
from app.schemas.usuario import LoginInput, TokenOutput, UsuarioOutput
from app.services.auth import autenticar_usuario, create_token, decode_token
from app.models.usuario import Usuario

router = APIRouter(prefix='/auth', tags=['Autenticación'])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')

@router.post('/login', response_model=TokenOutput)
def login(datos: LoginInput, session: Session = Depends(get_session)):
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
    # Con JWT el logout es responsabilidad del cliente: simplemente descarta el  toke. Este endpoint existe para que el frontend tenga un punto de cierre explícito
    return

@router.get('/me', response_model=UsuarioOutput)
def me(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
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
