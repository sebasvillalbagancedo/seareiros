from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime
import uuid

class MensajeDestinatario(SQLModel, table=True):
    __tablename__ = "mensajes_destinatarios"

    id:                   uuid.UUID             = Field(default_factory=uuid.uuid4, primary_key=True)
    mensaje_id:           uuid.UUID             = Field(foreign_key="mensajes.id")
    usuario_destinatario: uuid.UUID             = Field(foreign_key="usuarios.id")
    fecha_recepcion:      Optional[datetime]    = Field(default=None)
    fecha_lectura:        Optional[datetime]    = Field(default=None)
    estado:               str                   = Field(default="enviado")  # enviado | recibido | leido