from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.database import get_session
from app.models.evento import Evento
from app.models.inscripcion_evento import InscripcionEvento
from app.models.socio import Socio
from app.models.usuario import Usuario
from app.schemas.evento import (
    EventoCreate,
    EventoUpdate,
    EventoOutput,
    EventoCancelarInput,
    InscripcionCreate,
    InscripcionGestion,
    InscripcionOutput,
)
from app.services.eventos import (
    get_eventos,
    get_historico_eventos,
    get_historico_eventos_usuario,
    get_evento,
    crear_evento,
    editar_evento,
    cancelar_evento,
    get_inscripciones,
    inscribir_socio,
    gestionar_inscripcion,
    contar_inscritos,
)
from app.dependencies import get_usuario_actual
import uuid

router = APIRouter(prefix="/eventos", tags=["Eventos"])

# ── Helpers para construir outputs ────────────────────────────


def _evento_to_output(evento: Evento, session: Session) -> EventoOutput:
    """Construye un EventoOutput con el número de inscritos calculado."""
    return EventoOutput(
        id=str(evento.id),
        nombre=evento.nombre,
        descripcion=evento.descripcion,
        lugar=evento.lugar,
        fecha_celebracion=evento.fecha_celebracion,
        fecha_inicio_inscripcion=evento.fecha_inicio_inscripcion,
        fecha_fin_inscripcion=evento.fecha_fin_inscripcion,
        plazas_disponibles=evento.plazas_disponibles,
        fecha_nacimiento_maxima=evento.fecha_nacimiento_maxima,
        fecha_nacimiento_minima=evento.fecha_nacimiento_minima,
        fecha_alta_maxima=evento.fecha_alta_maxima,
        estado=evento.estado,
        fecha_creacion=evento.fecha_creacion,
        usuario_creacion=str(evento.usuario_creacion),
        motivo_cancelacion=evento.motivo_cancelacion,
        fecha_cancelacion=evento.fecha_cancelacion,
        usuario_cancelacion=str(evento.usuario_cancelacion),
        inscritos=contar_inscritos(evento.id, session),
    )


def _inscripcion_to_output(
    inscripcion: InscripcionEvento, socio: Socio
) -> InscripcionOutput:
    """Construye un InscripcionOutput con los datos del socio."""
    return InscripcionOutput(
        id=str(inscripcion.id),
        evento_id=str(inscripcion.evento_id),
        socio_id=str(inscripcion.socio_id),
        usuario_inscripcion=str(inscripcion.usuario_inscripcion),
        fecha_inscripcion=inscripcion.fecha_inscripcion,
        estado=inscripcion.estado,
        fecha_gestion=inscripcion.fecha_gestion,
        usuario_gestion=(
            str(inscripcion.usuario_gestion) if inscripcion.usuario_gestion else None
        ),
        socio_nombre=socio.nombre,
        socio_apellidos=socio.apellidos,
        socio_numero=socio.numero_socio,
    )


# ── Endpoints de eventos ──────────────────────────────────────────


@router.get("", response_model=list[EventoOutput], summary="Listar Eventos Disponibles")
def get_eventos_list_ep(session: Session = Depends(get_session)):
    """Eventos cuya fecha de celebración es posterior a hoy. Todos los usuarios autenticados."""
    eventos = get_eventos(session)
    return [_evento_to_output(e, session) for e in eventos]


@router.get(
    "/historico", response_model=list[EventoOutput], summary="Histórico de Eventos"
)
def get_historico_eventos_ep(
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """
    Eventos cuya fecha de celebración ya ha pasado.
    Admin ve todos; usuario normal solo ve eventos en los que participan sus socios asignados.
    """
    if usuario.rol == "administrador":
        eventos = get_historico_eventos(session)
    else:
        eventos = get_historico_eventos_usuario(session, usuario.id)
    return [_evento_to_output(e, session) for e in eventos]


@router.post(
    "",
    response_model=EventoOutput,
    status_code=status.HTTP_201_CREATED,
    summary="Crear Evento",
)
def post_evento_ep(
    datos: EventoCreate,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Crear Evento — Solo administrador."""
    evento = crear_evento(datos, usuario, session)
    return _evento_to_output(evento, session)


@router.get("/{evento_id}", response_model=EventoOutput, summary="Obtener Evento")
def get_evento_by_id_ep(evento_id: str, session: Session = Depends(get_session)):
    """Obtiene el detalle de un evento concreto."""
    evento = get_evento(evento_id, session)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return _evento_to_output(evento, session)


@router.put("/{evento_id}", response_model=EventoOutput, summary="Editar Evento")
def put_evento_ep(
    evento_id: str,
    datos: EventoUpdate,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Editar un evento en estado abierto. Solo administrador."""
    evento = get_evento(evento_id, session)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    evento = editar_evento(evento, datos, usuario, session)
    return _evento_to_output(evento, session)


@router.patch(
    "/{evento_id}/cancelar", response_model=EventoOutput, summary="Cancelar Evento"
)
def patch_evento_cancelar_ep(
    evento_id: str,
    datos: EventoCancelarInput,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Cancelar un evento — Solo administrador."""
    evento = get_evento(evento_id, session)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    evento = cancelar_evento(evento, datos.motivo_cancelacion, usuario, session)
    return _evento_to_output(evento, session)


# ── Endpoints de inscripciones ────────────────────────────────────


@router.get(
    "/{evento_id}/inscripciones",
    response_model=list[InscripcionOutput],
    summary="Listar Inscripciones Evento",
)
def get_inscripciones_evento_ep(
    evento_id: str, session: Session = Depends(get_session)
):
    """Listar inscripciones de un evento."""
    evento = get_evento(evento_id, session)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    resultados = get_inscripciones(evento_id, session)
    return [_inscripcion_to_output(i, s) for i, s in resultados]


@router.post(
    "/{evento_id}/inscripciones",
    response_model=InscripcionOutput,
    status_code=status.HTTP_201_CREATED,
    summary="Inscribir Socio",
)
def post_inscripcion_ep(
    evento_id: str,
    datos: InscripcionCreate,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """
    Inscribe a un socio en un evento.
    """
    evento = get_evento(evento_id, session)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    socio = session.get(Socio, uuid.UUID(datos.socio_id))
    if not socio:
        raise HTTPException(status_code=404, detail="Socio no encontrado")
    inscripcion, motivo = inscribir_socio(evento, socio, usuario, session)
    if not inscripcion:
        raise HTTPException(status_code=400, detail=motivo)

    return _inscripcion_to_output(inscripcion, socio)


@router.patch(
    "/{evento_id}/inscripciones/{inscripcion_id}",
    response_model=InscripcionOutput,
    summary="Gestionar Inscripción",
)
def patch_inscripcion_ep(
    evento_id: str,
    inscripcion_id: str,
    datos: InscripcionGestion,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Confirmar, rechazar o cancelar una inscripción — Solo administrador."""
    evento = get_evento(evento_id, session)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    inscripcion = session.get(InscripcionEvento, uuid.UUID(inscripcion_id))

    if not inscripcion or str(inscripcion.evento_id) != evento_id:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada")

    inscripcion = gestionar_inscripcion(inscripcion, datos.estado, usuario, session)
    socio = session.get(Socio, inscripcion.socio_id)
    return _inscripcion_to_output(inscripcion, socio)
