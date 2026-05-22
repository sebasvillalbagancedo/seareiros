from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime
import uuid

class InscripcionSorteo(SQLModel, table=True):
    __tablename__ = "inscripciones_sorteos"

    id:                  uuid.UUID              = Field(default_factory=uuid.uuid4, primary_key=True)
    sorteo_id:           uuid.UUID              = Field(foreign_key="sorteos.id")
    socio_id:            uuid.UUID              = Field(foreign_key="socios.id")
    usuario_inscripcion: uuid.UUID              = Field(foreign_key="usuarios.id")
    fecha_inscripcion:   datetime               = Field(default_factory=datetime.now)
    es_ganador:          bool                   = Field(default=False)
    estado:              str                    = Field(default="activa")
    fecha_cancelacion:   Optional[datetime]     = Field(default=None)
    usuario_cancelacion: Optional[uuid.UUID]    = Field(default=None, foreign_key="usuarios.id")