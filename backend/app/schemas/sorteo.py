from pydantic import BaseModel, model_validator
from typing import Optional
from datetime import date, datetime

# ── Sorteo ──────────────────────────────────────────────
class SorteoCreate(BaseModel):
    nombre:                   str
    descripcion:              Optional[str]     = None
    fecha_inicio_inscripcion: datetime
    fecha_fin_inscripcion:    datetime
    fecha_celebracion:        datetime
    numero_premios:           int                = 1
    maximo_inscritos:         Optional[int]     = None
    fecha_nacimiento_maxima:  Optional[date]    = None
    fecha_nacimiento_minima:  Optional[date]    = None
    fecha_alta_maxima:        Optional[date]    = None

    @model_validator(mode='after')
    def validador_campos(self):
        if self.fecha_fin_inscripcion <= self.fecha_inicio_inscripcion:
            raise ValueError(
                'La fecha de fin de inscripción debe ser posterior a la de inicio'
            )
        if self.fecha_celebracion < self.fecha_fin_inscripcion:
            raise ValueError(
                'La fecha de celebración debe ser posterior al cierre de inscripción'
            )
        if self.numero_premios < 1:
            raise ValueError('El número de premios debe ser mayor que cero')
        if self.maximo_inscritos is not None:
            if self.maximo_inscritos < 1:
                raise ValueError('El máximo de inscritos debe ser mayor que cero')
            if self.numero_premios > self.maximo_inscritos:
                raise ValueError(
                    'El número de premios no puede superar el máximo de inscritos'
                )
        return self

class SorteoUpdate(BaseModel):
    nombre:                   Optional[str]     = None
    descripcion:              Optional[str]     = None
    fecha_inicio_inscripcion: Optional[datetime] = None
    fecha_fin_inscripcion:    Optional[datetime] = None
    fecha_celebracion:        Optional[datetime] = None
    numero_premios:           Optional[int]     = None
    maximo_inscritos:         Optional[int]     = None
    fecha_nacimiento_maxima:  Optional[date]    = None
    fecha_nacimiento_minima:  Optional[date]    = None
    fecha_alta_maxima:        Optional[date]    = None

class SorteoOutput(BaseModel):
    id:                       str
    nombre:                   str
    descripcion:              Optional[str]     = None
    fecha_inicio_inscripcion: datetime
    fecha_fin_inscripcion:    datetime
    fecha_celebracion:        datetime
    numero_premios:           int
    maximo_inscritos:         Optional[int]     = None
    fecha_nacimiento_maxima:  Optional[date]    = None
    fecha_nacimiento_minima:  Optional[date]    = None
    fecha_alta_maxima:        Optional[date]    = None
    estado:                   str
    motivo_cancelacion:       Optional[str]     = None
    fecha_creacion:           datetime
    usuario_creacion:         str
    inscritos:                int               = 0

class SorteoCancelarInput(BaseModel):
    motivo_cancelacion: str

# ── Inscripciones  ─────────────────────────────────────
class InscripcionCreate(BaseModel):
    socio_id: str

class InscripcionOutput(BaseModel):
    id:                     str
    sorteo_id:              str
    socio_id:               str
    usuario_inscripcion:    str
    fecha_inscripcion:      datetime
    es_ganador:             bool
    estado:                 str
    fecha_cancelacion:      Optional[datetime] = None
    usuario_cancelacion:    Optional[str]      = None

    # Datos del socio para mostrar en el listado
    socio_nombre:           Optional[str] = None
    socio_apellidos:        Optional[str] = None
    socio_numero:           Optional[int] = None