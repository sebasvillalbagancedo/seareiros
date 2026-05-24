from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.database import get_session
from app.models.sorteo import Sorteo
from app.models.inscripcion_sorteo import InscripcionSorteo
from app.models.socio import Socio
from app.models.usuario import Usuario
from app.models.usuario_socio import UsuarioSocio
from app.schemas.sorteo import (
    SorteoCreate,
    SorteoUpdate,
    SorteoOutput,
    SorteoCancelarInput,
    InscripcionCreate,
    InscripcionOutput,
)
from app.services.sorteos import (
    get_sorteos,
    get_historico_sorteos,
    get_sorteo,
    crear_sorteo,
    editar_sorteo,
    cancelar_sorteo,
    get_inscripciones,
    inscribir_socio,
    cancelar_inscripcion,
    resolver_sorteo,
    contar_inscritos,
)
from app.dependencies import get_usuario_actual
import uuid

router = APIRouter(prefix="/sorteos", tags=["Sorteos"])

# ── Helpers para construir outputs ────────────────────────────


def _sorteo_to_output(sorteo: Sorteo, session: Session) -> SorteoOutput:
    """Construye un SorteoOutput con el número de inscritos calculado."""
    return SorteoOutput(
        id=str(sorteo.id),
        nombre=sorteo.nombre,
        descripcion=sorteo.descripcion,
        fecha_inicio_inscripcion=sorteo.fecha_inicio_inscripcion,
        fecha_fin_inscripcion=sorteo.fecha_fin_inscripcion,
        fecha_celebracion=sorteo.fecha_celebracion,
        numero_premios=sorteo.numero_premios,
        maximo_inscritos=sorteo.maximo_inscritos,
        fecha_nacimiento_maxima=sorteo.fecha_nacimiento_maxima,
        fecha_nacimiento_minima=sorteo.fecha_nacimiento_minima,
        fecha_alta_maxima=sorteo.fecha_alta_maxima,
        estado=sorteo.estado,
        fecha_creacion=sorteo.fecha_creacion,
        usuario_creacion=str(sorteo.usuario_creacion),
        motivo_cancelacion=sorteo.motivo_cancelacion,
        fecha_cancelacion=sorteo.fecha_cancelacion,
        usuario_cancelacion=str(sorteo.usuario_cancelacion),
        inscritos=contar_inscritos(sorteo.id, session),
    )


def _inscripcion_to_output(
    inscripcion: InscripcionSorteo, socio: Socio
) -> InscripcionOutput:
    """Construye un InscripcionOutput con los datos del socio."""
    return InscripcionOutput(
        id=str(inscripcion.id),
        sorteo_id=str(inscripcion.sorteo_id),
        socio_id=str(inscripcion.socio_id),
        usuario_inscripcion=str(inscripcion.usuario_inscripcion),
        fecha_inscripcion=inscripcion.fecha_inscripcion,
        es_ganador=inscripcion.es_ganador,
        estado=inscripcion.estado,
        fecha_cancelacion=inscripcion.fecha_cancelacion,
        usuario_cancelacion=(
            str(inscripcion.usuario_cancelacion)
            if inscripcion.usuario_cancelacion
            else None
        ),
        socio_nombre=socio.nombre,
        socio_apellidos=socio.apellidos,
        socio_numero=socio.numero_socio,
    )


# ── Endpoints de sorteos ──────────────────────────────────────────


@router.get("", response_model=list[SorteoOutput], summary="Listar Sorteos Disponibles")
def get_sorteos_list_ep(session: Session = Depends(get_session)):
    """
    Listado de sorteos cuya fecha de celebración es posterior a hoy.
    Todos los usuarios autenticados pueden ver el listado de sorteos.
    """
    sorteos = get_sorteos(session)
    return [_sorteo_to_output(s, session) for s in sorteos]


@router.get(
    "/historico", response_model=list[SorteoOutput], summary="Histórico de Sorteos"
)
def get_historico_sorteos_ep(session: Session = Depends(get_session)):
    """
    Historico de Sorteos
    """
    sorteos = get_historico_sorteos(session)
    return [_sorteo_to_output(s, session) for s in sorteos]


@router.post(
    "",
    response_model=SorteoOutput,
    status_code=status.HTTP_201_CREATED,
    summary="Crear Sorteo",
)
def post_sorteo_ep(
    datos: SorteoCreate,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Crear Sorteo — Solo administrador."""
    if usuario.rol != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador puede crear sorteos",
        )
    sorteo = crear_sorteo(datos, usuario, session)
    return _sorteo_to_output(sorteo, session)


@router.get("/{sorteo_id}", response_model=SorteoOutput, summary="Obtener Sorteo")
def get_sorteo_by_id_ep(
    sorteo_id: str,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Obtiene el detalle de un sorteo concreto."""
    sorteo = get_sorteo(sorteo_id, session)
    if not sorteo:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")
    return _sorteo_to_output(sorteo, session)


@router.put("/{sorteo_id}", response_model=SorteoOutput, summary="Editar Sorteo")
def put_sorteo_ep(
    sorteo_id: str,
    datos: SorteoUpdate,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Editar un sorteo en estado abierto. Solo administrador."""
    if usuario.rol != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador puede editar sorteos",
        )
    sorteo = get_sorteo(sorteo_id, session)
    if not sorteo:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")
    if sorteo.estado != "abierto":
        raise HTTPException(
            status_code=400, detail="Solo se pueden editar sorteos en estado abierto"
        )
    sorteo = editar_sorteo(sorteo, datos, session)
    return _sorteo_to_output(sorteo, session)


@router.patch(
    "/{sorteo_id}/cancelar", response_model=SorteoOutput, summary="Cancelar Sorteo"
)
def patch_sorteo_cancelar_ep(
    sorteo_id: str,
    datos: SorteoCancelarInput,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Cancelar un sorteo — Solo administrador."""
    if usuario.rol != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador puede cancelar sorteos",
        )
    sorteo = get_sorteo(sorteo_id, session)
    if not sorteo:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")
    if sorteo.estado in ("resuelto", "cancelado"):
        raise HTTPException(
            status_code=400,
            detail="No se puede cancelar un sorteo ya resuelto o cancelado",
        )
    sorteo = cancelar_sorteo(sorteo, datos.motivo_cancelacion, session)
    return _sorteo_to_output(sorteo, session)


@router.patch(
    "/{sorteo_id}/resolver", response_model=SorteoOutput, summary="Resolver Sorteo"
)
def patch_sorteo_resolver_ep(
    sorteo_id: str,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """
    Resuelve el sorteo manualmente.
    En producción lo ejecutará el planificador automático,
    pero se expone como endpoint para permitir la resolución manual por el administrador.
    """
    if usuario.rol != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el administrador puede resolver sorteos",
        )
    sorteo = get_sorteo(sorteo_id, session)
    if not sorteo:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")
    if sorteo.estado not in ("abierto", "cerrado", "pendiente"):
        raise HTTPException(
            status_code=400,
            detail="El sorteo no está en un estado que permita su resolución",
        )
    sorteo, _ = resolver_sorteo(sorteo, session)
    return _sorteo_to_output(sorteo, session)


# ── Endpoints de inscripciones ────────────────────────────────────


@router.get(
    "/{sorteo_id}/inscripciones",
    response_model=list[InscripcionOutput],
    summary="Listar Inscripciones Sorteo",
)
def get_inscripciones_sorteo_ep(
    sorteo_id: str,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Listar Inscripciones Sorteo."""
    sorteo = get_sorteo(sorteo_id, session)
    if not sorteo:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")
    resultados = get_inscripciones(sorteo_id, session)
    return [_inscripcion_to_output(i, s) for i, s in resultados]


@router.post(
    "/{sorteo_id}/inscripciones",
    response_model=InscripcionOutput,
    status_code=status.HTTP_201_CREATED,
    summary="Inscribir Socio",
)
def post_inscripcion_ep(
    sorteo_id: str,
    datos: InscripcionCreate,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """
    Inscribe a un socio en un sorteo.
    El administrador puede inscribir cualquier socio activo.
    El usuario normal solo puede inscribir socios que tenga asignados.
    """
    sorteo = get_sorteo(sorteo_id, session)
    if not sorteo:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")

    socio = session.get(Socio, uuid.UUID(datos.socio_id))
    if not socio:
        raise HTTPException(status_code=404, detail="Socio no encontrado")

    # Usuario normal: verificar que tiene permiso sobre el socio
    if usuario.rol != "administrador":
        permiso = session.exec(
            select(UsuarioSocio).where(
                UsuarioSocio.usuario_id == usuario.id,
                UsuarioSocio.socio_id == socio.id,
                UsuarioSocio.fecha_revocacion == None,
            )
        ).first()
        if not permiso:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso sobre este socio",
            )

    inscripcion, motivo = inscribir_socio(sorteo, socio, usuario, session)
    if not inscripcion:
        raise HTTPException(status_code=400, detail=motivo)

    return _inscripcion_to_output(inscripcion, socio)


@router.patch(
    "/{sorteo_id}/inscripciones/{inscripcion_id}",
    response_model=InscripcionOutput,
    summary="Cancelar Inscripción",
)
def patch_inscripcion_ep(
    sorteo_id: str,
    inscripcion_id: str,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Cancelar Inscripción en Sorteo."""
    sorteo = get_sorteo(sorteo_id, session)
    if not sorteo:
        raise HTTPException(status_code=404, detail="Sorteo no encontrado")
    if sorteo.estado not in ("abierto",):
        raise HTTPException(
            status_code=400,
            detail="Solo se pueden cancelar inscripciones en sorteos abiertos",
        )

    inscripcion = session.get(InscripcionSorteo, uuid.UUID(inscripcion_id))
    if not inscripcion or str(inscripcion.sorteo_id) != sorteo_id:
        raise HTTPException(status_code=404, detail="Inscripción no encontrada")
    if inscripcion.estado != "activa":
        raise HTTPException(status_code=400, detail="La inscripción no está activa")

    # Usuario normal: solo puede cancelar inscripciones de sus socios
    if usuario.rol != "administrador":
        permiso = session.exec(
            select(UsuarioSocio).where(
                UsuarioSocio.usuario_id == usuario.id,
                UsuarioSocio.socio_id == inscripcion.socio_id,
                UsuarioSocio.fecha_revocacion == None,
            )
        ).first()
        if not permiso:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso sobre este socio",
            )

    inscripcion = cancelar_inscripcion(inscripcion, usuario, session)
    socio = session.get(Socio, inscripcion.socio_id)
    return _inscripcion_to_output(inscripcion, socio)
