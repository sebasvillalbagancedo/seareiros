from pydantic import BaseModel
from typing import Optional
from datetime import date

class SocioCreate(BaseModel):
    nombre:           str
    apellidos:        str
    fecha_nacimiento: Optional[date] = None
    direccion:        Optional[str]  = None
    codigo_postal:    Optional[str]  = None
    localidad:        Optional[str]  = None
    provincia:        Optional[str]  = None
    pais:             Optional[str]  = None
    telefono_fijo:    Optional[str]  = None
    telefono_movil:   Optional[str]  = None
    email:            Optional[str]  = None

class SocioUpdate(BaseModel):
    nombre:           Optional[str]  = None
    apellidos:        Optional[str]  = None
    fecha_nacimiento: Optional[date] = None
    direccion:        Optional[str]  = None
    codigo_postal:    Optional[str]  = None
    localidad:        Optional[str]  = None
    provincia:        Optional[str]  = None
    pais:             Optional[str]  = None
    telefono_fijo:    Optional[str]  = None
    telefono_movil:   Optional[str]  = None
    email:            Optional[str]  = None

class SocioOutput(BaseModel):
    id:               str
    numero_socio:     Optional[int]
    nombre:           str
    apellidos:        str
    fecha_nacimiento: Optional[date] = None
    direccion:        Optional[str]  = None
    codigo_postal:    Optional[str]  = None
    localidad:        Optional[str]  = None
    provincia:        Optional[str]  = None
    pais:             Optional[str]  = None
    telefono_fijo:    Optional[str]  = None
    telefono_movil:   Optional[str]  = None
    email:            Optional[str]  = None
    fecha_alta:       date
    estado:           str