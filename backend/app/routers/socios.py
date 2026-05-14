from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from datetime import datetime
from app.database import get_session
from app.models.socio import Socio
from app.models.usuario import Usuario
from app.models.usuario_socio import UsuarioSocio
from app.schemas.socio import SocioCreate, SocioUpdate, SocioOutput
from app.services.socios import get_socios_usuario, get_socio_usuario
from app.routers.auth import oauth2_scheme
from app.services.auth import decode_token
import uuid

router = APIRouter(prefix="/socios", tags=["Socios"])


def get_usuario_actual(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> Usuario:
    """Dependencia reutilizable: extrae el usuario autenticado del token."""
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token inválido o expirado")
    usuario = session.get(Usuario, user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@router.get("", response_model=list[SocioOutput])
def listar_socios(
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session)
):
    """RF.0204 — Lista los socios accesibles según el rol del usuario."""
    socios = get_socios_usuario(usuario, session)
    return [SocioOutput(
        id=str(s.id), numero_socio=s.numero_socio,
        nombre=s.nombre, apellidos=s.apellidos,
        fecha_nacimiento=s.fecha_nacimiento, direccion=s.direccion,
        codigo_postal=s.codigo_postal, localidad=s.localidad,
        provincia=s.provincia, pais=s.pais,
        telefono_fijo=s.telefono_fijo, telefono_movil=s.telefono_movil,
        email=s.email, fecha_alta=s.fecha_alta, estado=s.estado
    ) for s in socios]


@router.post("", response_model=SocioOutput, status_code=status.HTTP_201_CREATED)
def crear_socio(
    datos: SocioCreate,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session)
):
    """RF.0201 — Solo el administrador puede dar de alta socios."""
    if usuario.rol != "administrador":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Solo el administrador puede crear socios")
    socio = Socio(**datos.model_dump())
    session.add(socio)
    session.commit()
    session.refresh(socio)
    return SocioOutput(
        id=str(socio.id), numero_socio=socio.numero_socio,
        nombre=socio.nombre, apellidos=socio.apellidos,
        fecha_nacimiento=socio.fecha_nacimiento, direccion=socio.direccion,
        codigo_postal=socio.codigo_postal, localidad=socio.localidad,
        provincia=socio.provincia, pais=socio.pais,
        telefono_fijo=socio.telefono_fijo, telefono_movil=socio.telefono_movil,
        email=socio.email, fecha_alta=socio.fecha_alta, estado=socio.estado
    )


@router.get("/{socio_id}", response_model=SocioOutput)
def obtener_socio(
    socio_id: str,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session)
):
    """RF.0204 — Obtiene un socio si el usuario tiene acceso a él."""
    socio = get_socio_usuario(socio_id, usuario, session)
    if not socio:
        raise HTTPException(status_code=404, detail="Socio no encontrado o sin acceso")
    return SocioOutput(
        id=str(socio.id), numero_socio=socio.numero_socio,
        nombre=socio.nombre, apellidos=socio.apellidos,
        fecha_nacimiento=socio.fecha_nacimiento, direccion=socio.direccion,
        codigo_postal=socio.codigo_postal, localidad=socio.localidad,
        provincia=socio.provincia, pais=socio.pais,
        telefono_fijo=socio.telefono_fijo, telefono_movil=socio.telefono_movil,
        email=socio.email, fecha_alta=socio.fecha_alta, estado=socio.estado
    )


@router.put("/{socio_id}", response_model=SocioOutput)
def editar_socio(
    socio_id: str,
    datos: SocioUpdate,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session)
):
    """RF.0202 — Edita los datos de un socio si el usuario tiene acceso."""
    socio = get_socio_usuario(socio_id, usuario, session)
    if not socio:
        raise HTTPException(status_code=404, detail="Socio no encontrado o sin acceso")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(socio, campo, valor)
    socio.fecha_actualizacion = datetime.now()
    session.add(socio)
    session.commit()
    session.refresh(socio)
    return SocioOutput(
        id=str(socio.id), numero_socio=socio.numero_socio,
        nombre=socio.nombre, apellidos=socio.apellidos,
        fecha_nacimiento=socio.fecha_nacimiento, direccion=socio.direccion,
        codigo_postal=socio.codigo_postal, localidad=socio.localidad,
        provincia=socio.provincia, pais=socio.pais,
        telefono_fijo=socio.telefono_fijo, telefono_movil=socio.telefono_movil,
        email=socio.email, fecha_alta=socio.fecha_alta, estado=socio.estado
    )


@router.patch("/{socio_id}/baja", response_model=SocioOutput)
def dar_baja_socio(
    socio_id: str,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session)
):
    """RF.0203 — Solo el administrador puede dar de baja a un socio."""
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
    return SocioOutput(
        id=str(socio.id), numero_socio=socio.numero_socio,
        nombre=socio.nombre, apellidos=socio.apellidos,
        fecha_nacimiento=socio.fecha_nacimiento, direccion=socio.direccion,
        codigo_postal=socio.codigo_postal, localidad=socio.localidad,
        provincia=socio.provincia, pais=socio.pais,
        telefono_fijo=socio.telefono_fijo, telefono_movil=socio.telefono_movil,
        email=socio.email, fecha_alta=socio.fecha_alta, estado=socio.estado
    )


@router.post("/{socio_id}/asignar/{usuario_id}", status_code=status.HTTP_201_CREATED)
def asignar_permiso(
    socio_id: str,
    usuario_id: str,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session)
):
    """RF.0205 — El administrador asigna un socio a un usuario normal."""
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


@router.patch("/{socio_id}/revocar/{usuario_id}")
def revocar_permiso(
    socio_id: str,
    usuario_id: str,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session)
):
    """RF.0205 — El administrador revoca el permiso de un usuario sobre un socio."""
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

    relacion.fecha_revocacion = datetime.now()
    relacion.usuario_revocacion = usuario.id
    session.add(relacion)
    session.commit()
    return {"mensaje": "Permiso revocado correctamente"}

@router.get("/{socio_id}/permisos")
def listar_permisos(
    socio_id: str,
    usuario: Usuario = Depends(get_usuario_actual),
    session: Session = Depends(get_session)
):
    """RF.0205 — Lista los permisos vigentes de un socio. Solo administrador."""
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