from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from datetime import datetime
from app.database import get_session
from app.models.socio import Socio
from app.models.usuario import Usuario
from app.models.usuario_socio import UsuarioSocio
from app.schemas.socio import SocioCreate, SocioUpdate, SocioOutput
from app.services.socios import get_socios_usuario, get_socio_usuario
from app.dependencies import get_usuario_actual
import uuid

router = APIRouter(prefix="/socios", tags=["Socios"])


# ── Helper para construir SocioOutput ────────────────────────────

def _socio_to_output(socio: Socio) -> SocioOutput:
    """ Construye un SocioOutput a partir de un objeto Socio. """
    return SocioOutput(
        id=str(socio.id), numero_socio=socio.numero_socio,
        nombre=socio.nombre, apellidos=socio.apellidos,
        fecha_nacimiento=socio.fecha_nacimiento, direccion=socio.direccion,
        codigo_postal=socio.codigo_postal, localidad=socio.localidad,
        provincia=socio.provincia, pais=socio.pais,
        telefono_fijo=socio.telefono_fijo, telefono_movil=socio.telefono_movil,
        email=socio.email, fecha_alta=socio.fecha_alta, estado=socio.estado
    )

# ── Endpoints de socios ───────────────────────────────────────────

@router.get('', response_model=list[SocioOutput], summary='Listar Socios')
def get_socios(
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session)
):
    """ Lista los socios accesibles según el rol del usuario. """
    socios = get_socios_usuario(usuario, session)
    return [_socio_to_output(s) for s in socios]


@router.post('', response_model=SocioOutput, status_code=status.HTTP_201_CREATED, summary='Crear Socio' )
def post_socio(
    datos: SocioCreate,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session)
):
    """ Creación de socios. Solo el administrador puede crear socios. """
    if usuario.rol != "administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Solo el administrador puede crear socios")
    socio = Socio(**datos.model_dump())
    session.add(socio)
    session.commit()
    session.refresh(socio)
    return _socio_to_output(socio)


@router.get('/{socio_id}', response_model=SocioOutput, summary='Obtener Socio')
def get_socio(
    socio_id: str,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session)
):
    """ Obtiene un socio si el usuario tiene acceso a él. """
    socio = get_socio_usuario(socio_id, usuario, session)
    if not socio:
        raise HTTPException(status_code=404, detail="Socio no encontrado o sin acceso")
    return _socio_to_output(socio)


@router.put('/{socio_id}', response_model=SocioOutput, summary='Editar Socio')
def put_socio(
    socio_id: str,
    datos: SocioUpdate,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session)
):
    """ Edita los datos de un socio si el usuario tiene acceso."""
    socio = get_socio_usuario(socio_id, usuario, session)
    if not socio:
        raise HTTPException(status_code=404, detail="Socio no encontrado o sin acceso")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(socio, campo, valor)
    socio.fecha_actualizacion = datetime.now()
    session.add(socio)
    session.commit()
    session.refresh(socio)
    return _socio_to_output(socio)


@router.patch('/{socio_id}', response_model=SocioOutput, summary='Baja Socio')
def patch_socio(
    socio_id: str,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session)
):
    """Dar de baja a un socio. Solo administrador."""
    if usuario.rol != "administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Solo el administrador puede dar de baja socios")
    socio = session.get(Socio, uuid.UUID(socio_id))
    if not socio:
        raise HTTPException(status_code=404, detail="Socio no encontrado")
    if socio.estado == "baja":
        raise HTTPException(status_code=400, detail="El socio ya está en estado de baja")
    socio.estado = "baja"
    socio.fecha_actualizacion = datetime.now()
    session.add(socio)
    session.commit()
    session.refresh(socio)
    return _socio_to_output(socio)


# ── Endpoints de permisos ─────────────────────────────────────────

@router.get('/{socio_id}/permisos', summary='Listar Permisos de Socio')
def get_permisos_socio(
    socio_id: str,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session)
):
    """Lista los permisos vigentes de un socio. Solo administrador."""
    if usuario.rol != "administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Solo el administrador puede consultar permisos")
    permisos = session.exec(
        select(UsuarioSocio).where(
            UsuarioSocio.socio_id == uuid.UUID(socio_id),
            UsuarioSocio.fecha_revocacion == None
        )
    ).all()
    return [{"usuario_id": str(p.usuario_id)} for p in permisos]


@router.post('/{socio_id}/permisos/{usuario_id}', status_code=status.HTTP_201_CREATED, summary='Asignar Permiso')
def post_permiso_socio(
    socio_id: str,
    usuario_id: str,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session)
):
    """Asignar un socio a un usuario normal. Solo administrador."""
    if usuario.rol != "administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Solo el administrador puede asignar permisos")

    existente = session.exec(
        select(UsuarioSocio).where(
            UsuarioSocio.usuario_id == uuid.UUID(usuario_id),
            UsuarioSocio.socio_id == uuid.UUID(socio_id),
            UsuarioSocio.fecha_revocacion == None
        )
    ).first()
    if existente:
        raise HTTPException(status_code=400, detail="El permiso ya existe y está vigente")

    relacion = UsuarioSocio(
        usuario_id=uuid.UUID(usuario_id),
        socio_id=uuid.UUID(socio_id),
        usuario_asignacion=usuario.id
    )
    session.add(relacion)
    session.commit()
    return {"mensaje": "Permiso asignado correctamente"}


@router.patch('/{socio_id}/permisos/{usuario_id}', summary='Revocar Permiso')
def patch_permiso_socio(
    socio_id: str,
    usuario_id: str,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session)
):
    """Revoca el permiso de un usuario sobre un socio. Solo administrador."""
    if usuario.rol != "administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Solo el administrador puede revocar permisos")

    relacion = session.exec(
        select(UsuarioSocio).where(
            UsuarioSocio.usuario_id == uuid.UUID(usuario_id),
            UsuarioSocio.socio_id == uuid.UUID(socio_id),
            UsuarioSocio.fecha_revocacion == None
        )
    ).first()
    if not relacion:
        raise HTTPException(status_code=404, detail="No existe un permiso vigente para revocar")

    relacion.fecha_revocacion  = datetime.now()
    relacion.usuario_revocacion = usuario.id
    session.add(relacion)
    session.commit()
    return {"mensaje": "Permiso revocado correctamente"}