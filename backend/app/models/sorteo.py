from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import date, datetime
import uuid

class Sorteo(SQLModel, table=True):
    __tablename__ = "sorteos"

    id:                        uuid.UUID        = Field(default_factory=uuid.uuid4, primary_key=True)
    nombre:                    str              = Field(max_length=255)
    descripcion:               Optional[str]    = Field(default=None)
    fecha_inicio_inscripcion:  datetime         = Field()
    fecha_fin_inscripcion:     datetime         = Field()
    fecha_celebracion:         datetime         = Field()
    numero_premios:            int              = Field(default=1)
    maximo_inscritos:          Optional[int]    = Field(default=None)
    fecha_nacimiento_maxima:   Optional[date]   = Field(default=None)
    fecha_nacimiento_minima:   Optional[date]   = Field(default=None)
    fecha_alta_maxima:         Optional[date]   = Field(default=None)
    estado:                    str              = Field(default="abierto")
    motivo_cancelacion:        Optional[str]    = Field(default=None)
    fecha_creacion:            datetime         = Field(default_factory=datetime.now)
    usuario_creacion:          uuid.UUID        = Field(foreign_key="usuarios.id")