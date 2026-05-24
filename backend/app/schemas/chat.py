from pydantic import BaseModel, model_validator
from typing import Optional
from datetime import datetime

TIPOS_ACCESO = {"libre", "restringido"}
MODALIDADES = {"bidireccional", "canal"}
VISIBILIDADES = {"visible", "oculta"}


# ── Chat ──────────────────────────────────────────────
class ChatCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    tipo_acceso: str  # libre | restringido
    modalidad: str  # bidireccional | canal
    visibilidad: str  # visible | oculta

    @model_validator(mode="after")
    def validar_campos(self):
        if self.tipo_acceso not in TIPOS_ACCESO:
            raise ValueError("Tipo Acceso debe ser {TIPOS_ACCESO}")
        if self.modalidad not in MODALIDADES:
            raise ValueError("Modalidad debe ser {MODALIDADES}")
        if self.visibilidad not in VISIBILIDADES:
            raise ValueError("Visibilidad debe ser {VISIBILIDADES}")
        return self


class ChatUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    tipo_acceso: Optional[str] = None
    modalidad: Optional[str] = None
    visibilidad: Optional[str] = None


class ChatOutput(BaseModel):
    id: str
    nombre: str
    descripcion: Optional[str] = None
    tipo_acceso: str
    modalidad: str
    visibilidad: str
    fecha_creacion: datetime
    usuario_creacion: str
    # Campos calculados para devolver toda la información relevante en la misma consulta
    num_miembros: int = 0
    es_miembro: bool = False
    mi_rol: Optional[str] = None  # miembro | administrador | None
    solicitud_estado: Optional[str] = None  # pendiente | aceptada | rechazada | None


# ── MiembroChat ───────────────────────────────────────
class MiembroChatOutput(BaseModel):
    id: str
    chat_id: str
    usuario_id: str
    nombre_usuario: str
    apellidos_usuario: str
    codigo_usuario: str
    rol: str
    rol_sistema: str
    estado: str
    fecha_incorporacion: datetime
    fecha_baja: Optional[datetime] = None
    usuario_baja: Optional[str] = None


class MiembroRolUpdate(BaseModel):
    rol: str  # miembro | administrador


# ── SolicitudChat ─────────────────────────────────────


class SolicitudChatOutput(BaseModel):
    id: str
    chat_id: str
    usuario_id: str
    nombre_usuario: str
    apellidos_usuario: str
    codigo_usuario: str
    estado: str  # pendiente | aceptada | rechazada
    fecha_solicitud: datetime
    fecha_resolucion: Optional[datetime] = None
    usuario_resolucion: Optional[str] = None


# ── InvitacionChat ────────────────────────────────────


class InvitacionChatCreate(BaseModel):
    usuario_destinatario: str


class InvitacionChatOutput(BaseModel):
    id: str
    chat_id: str
    usuario_destinatario: str
    nombre_destinatario: str
    apellidos_destinatario: str
    usuario_invitacion: str
    nombre_invitador: str
    apellidos_invitador: str
    nombre_chat: str
    fecha_invitacion: datetime
    estado: str  # pendiente | aceptada | rechazada
    fecha_resolucion: Optional[datetime] = None


# ── Mensaje  ────────────────────────────────────
class MensajeCreate(BaseModel):
    contenido: str
    usuario_destinatario: Optional[str] = None  # para mensajes directos
    # chat_id viene de la URL en mensajes grupales


class MensajeOutput(BaseModel):
    id: str
    contenido: str
    usuario_envio: str
    nombre_remitente: str
    apellidos_remitente: str
    fecha_envio: datetime
    chat_id: Optional[str] = None
    estado: Optional[str] = None  # estado del destinatario actual
    fecha_lectura: Optional[datetime] = None


class ConversacionDirectaOutput(BaseModel):
    """Resumen de una conversación directa para el historial"""

    usuario_id: str
    nombre: str
    apellidos: str
    codigo_usuario: str
    ultimo_mensaje: Optional[str] = None
    fecha_ultimo: Optional[datetime] = None
    no_leidos: int = 0


class ChatResumenOutput(BaseModel):
    """Resumen de un chat para el historial"""

    chat_id: str
    nombre: str
    modalidad: str
    ultimo_mensaje: Optional[str] = None
    fecha_ultimo: Optional[datetime] = None
    no_leidos: int = 0
    solicitudes_pendientes: int = 0
