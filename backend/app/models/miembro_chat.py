from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime
import uuid

class MiembroChat(SQLModel, table=True):
    __tablename__ = "miembros_chats"

    id:                     uuid.UUID           = Field(default_factory=uuid.uuid4, primary_key=True)
    chat_id:                uuid.UUID           = Field(foreign_key="chats.id")
    usuario_id:             uuid.UUID           = Field(foreign_key="usuarios.id")
    rol:                    str                 = Field(default="miembro")   # miembro | administrador
    estado:                 str                 = Field(default="activo") # activo | baja
    fecha_incorporacion:    datetime            = Field(default_factory=datetime.now)
    usuario_baja:           Optional[uuid.UUID] = Field(default=None, foreign_key="usuarios.id")
    fecha_baja:             Optional[datetime]  = Field(default=None)
    
