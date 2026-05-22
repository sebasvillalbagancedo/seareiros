from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import datetime
import uuid

class UsuarioSocio(SQLModel, table=True):
    __tablename__ = 'usuarios_socios'
    id:                     uuid.UUID           = Field(default_factory=uuid.uuid4, primary_key=True)
    usuario_id:             uuid.UUID           = Field(foreign_key="usuarios.id")
    socio_id:               uuid.UUID           = Field(foreign_key="socios.id")
    fecha_asignacion:       datetime            = Field(default_factory=datetime.now)
    usuario_asignacion:     uuid.UUID           = Field(foreign_key="usuarios.id")
    fecha_revocacion:       Optional[datetime]  = Field(default=None)
    usuario_revocacion:     Optional[uuid.UUID] = Field(default=None, foreign_key="usuarios.id")