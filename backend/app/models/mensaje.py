from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime
import uuid

class Mensaje(SQLModel, table=True):
    __tablename__ = "mensajes"

    id:              uuid.UUID              = Field(default_factory=uuid.uuid4, primary_key=True)
    contenido:       str                    = Field()
    usuario_envio:   uuid.UUID              = Field(foreign_key="usuarios.id")
    fecha_envio:     datetime               = Field(default_factory=datetime.now)
    chat_id:         Optional[uuid.UUID]    = Field(default=None, foreign_key="chats.id")