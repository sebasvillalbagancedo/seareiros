import bcrypt

from jose import jwt
from datetime import datetime, timedelta
from sqlmodel import Session, select, or_
from app.config import SECRET_KEY, ALGORITHM, TOKEN_MINUTES
from app.models.usuario import Usuario


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now() + timedelta(minutes=TOKEN_MINUTES)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def autenticar_usuario(identificador: str, contrasena: str, session: Session):
    statement = select(Usuario).where(
        or_(Usuario.email == identificador, Usuario.codigo_usuario == identificador)
    )
    usuario = session.exec(statement).first()
    if not usuario:
        return None
    if not verify_password(contrasena, usuario.contrasena_cifrada):
        return None
    if usuario.estado != "activa":
        return None
    return usuario
