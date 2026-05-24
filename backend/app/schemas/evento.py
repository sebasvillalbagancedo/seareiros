from pydantic import BaseModel, model_validator, field_validator
from typing import Optional
from datetime import date, datetime

ESTADOS_INSCRIPCION = {"pendiente", "confirmada", "rechazada", "cancelada"}


# ── Evento ──────────────────────────────────────────────
class EventoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    lugar: Optional[str] = None
    fecha_celebracion: datetime
    fecha_inicio_inscripcion: datetime
    fecha_fin_inscripcion: datetime
    plazas_disponibles: int
    fecha_nacimiento_maxima: Optional[date] = None
    fecha_nacimiento_minima: Optional[date] = None
    fecha_alta_maxima: Optional[date] = None

    @field_validator("plazas_disponibles")
    @classmethod
    def plazas_positivas(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("El número de plazas disponibles debe ser mayor que cero")
        return v

    @model_validator(mode="after")
    def validador_campos(self):
        if self.fecha_fin_inscripcion <= self.fecha_inicio_inscripcion:
            raise ValueError(
                "La fecha de fin de inscripción debe ser posterior a la de inicio"
            )
        if self.fecha_celebracion < self.fecha_fin_inscripcion:
            raise ValueError(
                "La fecha de celebración debe ser posterior al cierre de inscripción"
            )
        return self


class EventoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    lugar: Optional[str] = None
    fecha_celebracion: Optional[datetime] = None
    fecha_inicio_inscripcion: Optional[datetime] = None
    fecha_fin_inscripcion: Optional[datetime] = None
    plazas_disponibles: Optional[int] = None
    fecha_nacimiento_maxima: Optional[date] = None
    fecha_nacimiento_minima: Optional[date] = None
    fecha_alta_maxima: Optional[date] = None


class EventoOutput(BaseModel):
    id: str
    nombre: str
    descripcion: Optional[str] = None
    lugar: Optional[str]
    fecha_celebracion: datetime
    fecha_inicio_inscripcion: datetime
    fecha_fin_inscripcion: datetime
    plazas_disponibles: int
    fecha_nacimiento_maxima: Optional[date] = None
    fecha_nacimiento_minima: Optional[date] = None
    fecha_alta_maxima: Optional[date] = None
    estado: str
    fecha_creacion: datetime
    usuario_creacion: str
    motivo_cancelacion: Optional[str] = None
    fecha_cancelacion: Optional[datetime] = None
    usuario_cancelacion: Optional[str] = None
    inscritos: int = 0


class EventoCancelarInput(BaseModel):
    motivo_cancelacion: str


# ── Inscripciones  ─────────────────────────────────────
class InscripcionCreate(BaseModel):
    socio_id: str


class InscripcionGestion(BaseModel):
    estado: str

    @field_validator("estado")
    @classmethod
    def estado_valido(cls, v: str) -> str:
        if v not in ESTADOS_INSCRIPCION:
            raise ValueError(f"Estado debe ser uno de {ESTADOS_INSCRIPCION}")
        return v


class InscripcionOutput(BaseModel):
    id: str
    evento_id: str
    socio_id: str
    usuario_inscripcion: str
    fecha_inscripcion: datetime
    estado: str
    fecha_gestion: Optional[datetime] = None
    usuario_gestion: Optional[str] = None

    # Datos del socio para mostrar en el listado
    socio_nombre: Optional[str] = None
    socio_apellidos: Optional[str] = None
    socio_numero: Optional[int] = None
