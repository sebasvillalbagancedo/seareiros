import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))) 

from sqlmodel import Session, select
from app.database import engine
from app.models.usuario import Usuario
from app.services.auth import hash_password

def crear_usuarios():
    with Session(engine) as session:
        # Solo inserta si la tabla está vacía
        if session.exec(select(Usuario)).first():
            print("Los usuarios ya existen, no se hace nada.")
            return
        admin = Usuario(
            codigo_usuario     = "u_admin",
            email              = "admin@seareiros.local",
            contrasena_cifrada = hash_password("l0str3g0."),
            nombre             = "Administrador",
            apellidos          = "Seareiros",
            rol                = "administrador",
            estado             = "activa",
        )
        normal = Usuario(
            codigo_usuario     = "u_normal",
            email              = "normal@seareiros.local",
            contrasena_cifrada = hash_password("tr3b04dA."),
            nombre             = "Usuario",
            apellidos          = "Normal",
            rol                = "normal",
            estado             = "activa",
        )
        session.add(admin)
        session.add(normal)
        session.commit()
        print("✓ Usuarios creados correctamente")

if __name__ == "__main__":
    crear_usuarios()

