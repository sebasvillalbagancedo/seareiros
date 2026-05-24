from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime
import uuid


class InscripcionEvento(SQLModel, table=True):
    __tablename__ = "inscripciones_eventos"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    evento_id: uuid.UUID = Field(foreign_key="eventos.id")
    socio_id: uuid.UUID = Field(foreign_key="socios.id")
    usuario_inscripcion: uuid.UUID = Field(foreign_key="usuarios.id")
    fecha_inscripcion: datetime = Field(default_factory=datetime.now)
    estado: str = Field(default="pendiente", max_length=20)
    fecha_gestion: Optional[datetime] = Field(default=None)
    usuario_gestion: Optional[uuid.UUID] = Field(
        default=None, foreign_key="usuarios.id"
    )
