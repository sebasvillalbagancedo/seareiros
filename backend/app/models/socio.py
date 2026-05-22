from sqlmodel import Field, SQLModel
from sqlalchemy import Column, Integer, Sequence
from typing import Optional
from datetime import date, datetime
import uuid

socio_seq = Sequence('socios_numero_socio_seq')

class Socio(SQLModel, table=True):
    __tablename__ = 'socios'
    id:                     uuid.UUID           = Field(default_factory=uuid.uuid4, primary_key=True)
    numero_socio:           Optional[int]       = Field(
                                                    default=None,
                                                    sa_column=Column(
                                                        Integer,
                                                        socio_seq,
                                                        server_default=socio_seq.next_value(),
                                                        unique=True,
                                                        nullable=False
                                                    )
                                                )
    nombre:                 str                 = Field(max_length=255)
    apellidos:              str                 = Field(max_length=255)
    fecha_nacimiento:       Optional[date]      = Field(default=None)
    direccion:              Optional[str]       = Field(default=None, max_length=1000)
    codigo_postal:          Optional[str]       = Field(default=None, max_length=10)
    localidad:              Optional[str]       = Field(default=None, max_length=100)
    provincia:              Optional[str]       = Field(default=None, max_length=100)
    pais:                   Optional[str]       = Field(default=None, max_length=100)
    telefono_fijo:          Optional[str]       = Field(default=None, max_length=20)
    telefono_movil:         Optional[str]       = Field(default=None, max_length=20)
    email:                  Optional[str]       = Field(default=None, max_length=255)
    fecha_alta:             Optional[date]      = Field(default_factory=date.today)
    estado:                 str                 = Field(default="activo", max_length=10)  # 'activo', 'baja'
    fecha_creacion:         datetime            = Field(default_factory=datetime.now)
    fecha_actualizacion:    datetime            = Field(default_factory=datetime.now)