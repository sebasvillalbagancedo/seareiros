from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.database import get_session
from app.models.socio import Socio
from app.models.usuario import Usuario
from app.models.usuario_socio import UsuarioSocio
from app.schemas.socio import SocioCreate, SocioUpdate, SocioOutput
from app.services.socios import (
    get_socios_usuario,
    get_socio_usuario,
    crear_socio,
    editar_socio,
    dar_baja_socio,
    get_permisos_socio,
    asignar_permiso,
    revocar_permiso,
)
from app.dependencies import get_usuario_actual

router = APIRouter(prefix="/socios", tags=["Socios"])

# ── Helper para construir SocioOutput ────────────────────────────


def _socio_to_output(socio: Socio) -> SocioOutput:
    """Construye un SocioOutput a partir de un objeto Socio."""
    return SocioOutput(
        id=str(socio.id),
        numero_socio=socio.numero_socio,
        nombre=socio.nombre,
        apellidos=socio.apellidos,
        fecha_nacimiento=socio.fecha_nacimiento,
        direccion=socio.direccion,
        codigo_postal=socio.codigo_postal,
        localidad=socio.localidad,
        provincia=socio.provincia,
        pais=socio.pais,
        telefono_fijo=socio.telefono_fijo,
        telefono_movil=socio.telefono_movil,
        email=socio.email,
        fecha_alta=socio.fecha_alta,
        estado=socio.estado,
    )


# ── Endpoints de socios ───────────────────────────────────────────


@router.get("", response_model=list[SocioOutput], summary="Listar Socios")
def get_socios_ep(
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Lista los socios accesibles según el rol del usuario."""
    socios = get_socios_usuario(usuario, session)
    return [_socio_to_output(s) for s in socios]


@router.post(
    "",
    response_model=SocioOutput,
    status_code=status.HTTP_201_CREATED,
    summary="Crear Socio",
)
def post_socio_ep(
    datos: SocioCreate,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Creación de socios. Solo el administrador puede crear socios."""
    socio = crear_socio(datos, usuario, session)
    return _socio_to_output(socio)


@router.get("/{socio_id}", response_model=SocioOutput, summary="Obtener Socio")
def get_socio_ep(
    socio_id: str,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Obtiene un socio si el usuario tiene acceso a él."""
    socio = get_socio_usuario(socio_id, usuario, session)
    if not socio:
        raise HTTPException(status_code=404, detail="Socio no encontrado o sin acceso")
    return _socio_to_output(socio)


@router.put("/{socio_id}", response_model=SocioOutput, summary="Editar Socio")
def put_socio_ep(
    socio_id: str,
    datos: SocioUpdate,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Edita los datos de un socio si el usuario tiene acceso."""
    socio = get_socio_usuario(socio_id, usuario, session)
    if not socio:
        raise HTTPException(status_code=404, detail="Socio no encontrado o sin acceso")
    socio = editar_socio(socio, datos, session)
    return _socio_to_output(socio)


@router.patch("/{socio_id}", response_model=SocioOutput, summary="Baja Socio")
def patch_socio_ep(
    socio_id: str,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Dar de baja a un socio. Solo administrador."""
    socio = dar_baja_socio(socio_id, usuario, session)
    return _socio_to_output(socio)


# ── Endpoints de permisos ─────────────────────────────────────────


@router.get("/{socio_id}/permisos", summary="Listar Permisos de Socio")
def get_permisos_socio_ep(
    socio_id: str,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Lista los permisos vigentes de un socio. Solo administrador."""
    permisos = get_permisos_socio(socio_id, usuario, session)
    return [{"usuario_id": str(p.usuario_id)} for p in permisos]


@router.post(
    "/{socio_id}/permisos/{usuario_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Asignar Permiso",
)
def post_permiso_socio_ep(
    socio_id: str,
    usuario_id: str,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Asignar un socio a un usuario normal. Solo administrador."""
    asignar_permiso(socio_id, usuario_id, usuario, session)
    return {"mensaje": "Permiso asignado correctamente"}


@router.patch("/{socio_id}/permisos/{usuario_id}", summary="Revocar Permiso")
def patch_permiso_socio_ep(
    socio_id: str,
    usuario_id: str,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session),
):
    """Revoca el permiso de un usuario sobre un socio. Solo administrador."""
    revocar_permiso(socio_id, usuario_id, usuario, session)
    return {"mensaje": "Permiso revocado correctamente"}
