from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime
import uuid
 
 
class SolicitudChat(SQLModel, table=True):
    __tablename__ = "solicitudes_chats"
 
    id:                 uuid.UUID           = Field(default_factory=uuid.uuid4, primary_key=True)
    chat_id:            uuid.UUID           = Field(foreign_key="chats.id")
    usuario_id:         uuid.UUID           = Field(foreign_key="usuarios.id")
    estado:             str                 = Field(default="pendiente")  # pendiente | aceptada | rechazada
    fecha_solicitud:    datetime            = Field(default_factory=datetime.now)
    fecha_resolucion:   Optional[datetime]  = Field(default=None)
    usuario_resolucion: Optional[uuid.UUID] = Field(default=None, foreign_key="usuarios.id")