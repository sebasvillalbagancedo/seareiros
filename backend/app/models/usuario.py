from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime
import uuid


class Usuario(SQLModel, table=True):
    __tablename__ = "usuarios"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    codigo_usuario: str = Field(max_length=50, unique=True)
    email: str = Field(max_length=255, unique=True)
    contrasena_cifrada: str = Field(max_length=255)
    nombre: str = Field(max_length=255)
    apellidos: str = Field(max_length=255)
    rol: str = Field(max_length=20)  # 'administrador' o 'usuario'
    estado: str = Field(max_length=20)  # 'activa', 'bloqueada', 'inactiva'
    fecha_creacion: datetime = Field(default_factory=datetime.now)
    fecha_ult_conexion: Optional[datetime] = Field(default=None)
