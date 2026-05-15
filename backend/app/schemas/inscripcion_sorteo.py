from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class InscripcionCreate(BaseModel):
    socio_id: str

class InscripcionOutput(BaseModel):
    id:                  str
    sorteo_id:           str
    socio_id:            str
    usuario_inscripcion: str
    fecha_inscripcion:   datetime
    es_ganador:          bool
    estado:              str
    fecha_cancelacion:   Optional[datetime] = None
    usuario_cancelacion: Optional[str]      = None

    # Datos del socio para mostrar en el listado
    socio_nombre:    Optional[str] = None
    socio_apellidos: Optional[str] = None
    socio_numero:    Optional[int] = None