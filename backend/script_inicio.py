import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))) 

from sqlmodel import Session
from app.database import engine
from app.models.usuario import Usuario
from app.services.auth import hash_password

def crear_usuarios():
    with Session(engine) as session:
        admin = Usuario(
            codigo_usuario     = "ADM001",
            email              = "admin@seareiros.local",
            contrasena_cifrada = hash_password("admin123"),
            nombre             = "Administrador",
            apellidos          = "Seareiros",
            rol                = "administrador",
            estado             = "activa",
        )
        normal = Usuario(
            codigo_usuario     = "USR001",
            email              = "usuario@seareiros.local",
            contrasena_cifrada = hash_password("user123"),
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

