from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime
import uuid

class Chat(SQLModel, table=True):
    __tablename__ = "chats"

    id:               uuid.UUID        = Field(default_factory=uuid.uuid4, primary_key=True)
    nombre:           str              = Field(max_length=255)
    descripcion:      Optional[str]    = Field(default=None)
    tipo_acceso:      str              = Field()  # libre | restringido
    modalidad:        str              = Field()  # bidireccional | canal
    visibilidad:      str              = Field()  # visible | oculta
    fecha_creacion:   datetime         = Field(default_factory=datetime.now)
    usuario_creacion: uuid.UUID        = Field(foreign_key="usuarios.id")