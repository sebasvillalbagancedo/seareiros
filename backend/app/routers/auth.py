from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from datetime import datetime
from app.database import get_session
from app.schemas.usuario import LoginInput, TokenOutput
from app.services.auth import autenticar_usuario, create_token

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenOutput)
def login_ep(datos: LoginInput, session: Session = Depends(get_session)):
    """Inicia sesión y devuelve un token JWT."""
    usuario = autenticar_usuario(datos.identificador, datos.contrasena, session)

    if not usuario:
        # Mensaje genérico: no revelamos si el problema es el usuario o la contraseña
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas o usuario inactivo",
        )

    # Actualizamos la fecha de última conexión
    usuario.fecha_ult_conexion = datetime.now()
    session.add(usuario)
    session.commit()

    token = create_token({"sub": str(usuario.id), "rol": usuario.rol})
    return TokenOutput(access_token=token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_ep():
    """
    Cierre de sesión.
    Con JWT el logout es responsabilidad del cliente: simplemente descarta el token.
    Este endpoint existe para que el frontend tenga un punto de cierre explícito.
    """
    return None  # No hacemos nada en el backend, el cliente debe eliminar el token
