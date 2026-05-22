from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime
import uuid
 
 
class InvitacionChat(SQLModel, table=True):
    __tablename__ = "invitaciones_chats"
 
    id:                   uuid.UUID           = Field(default_factory=uuid.uuid4, primary_key=True)
    chat_id:              uuid.UUID           = Field(foreign_key="chats.id")
    usuario_destinatario: uuid.UUID           = Field(foreign_key="usuarios.id")
    usuario_invitacion:   uuid.UUID           = Field(foreign_key="usuarios.id")
    fecha_invitacion:     datetime            = Field(default_factory=datetime.now)
    estado:               str                 = Field(default="pendiente")  # pendiente | aceptada | rechazada
    fecha_resolucion:     Optional[datetime]  = Field(default=None)