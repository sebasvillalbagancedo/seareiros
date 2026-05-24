from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import date, datetime
import uuid


class Evento(SQLModel, table=True):
    __tablename__ = "eventos"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    nombre: str = Field(max_length=255)
    descripcion: Optional[str] = Field(default=None)
    lugar: Optional[str] = Field(default=None, max_length=255)
    fecha_celebracion: datetime = Field()
    fecha_inicio_inscripcion: datetime = Field()
    fecha_fin_inscripcion: datetime = Field()
    plazas_disponibles: int = Field(gt=0)
    fecha_nacimiento_maxima: Optional[date] = Field(default=None)
    fecha_nacimiento_minima: Optional[date] = Field(default=None)
    fecha_alta_maxima: Optional[date] = Field(default=None)
    estado: str = Field(default="abierto", max_length=20)
    fecha_creacion: datetime = Field(default_factory=datetime.now)
    usuario_creacion: uuid.UUID = Field(foreign_key="usuarios.id")
    motivo_cancelacion: Optional[str] = Field(default=None)
    fecha_cancelacion: Optional[datetime] = Field(default=None)
    usuario_cancelacion: Optional[uuid.UUID] = Field(
        default=None, foreign_key="usuarios.id"
    )
