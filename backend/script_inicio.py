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

        usuarios = [
            # Usuarios administradores
            Usuario(
                codigo_usuario="u_admin_01",
                email="maria.garcia@seareiros.local",
                contrasena_cifrada=hash_password("Maria123."),
                nombre="María",
                apellidos="García López",
                rol="administrador",
                estado="activa",
            ),
            Usuario(
                codigo_usuario="u_admin_02",
                email="jose.rodriguez@seareiros.local",
                contrasena_cifrada=hash_password("Jose123."),
                nombre="José",
                apellidos="Rodríguez Pérez",
                rol="administrador",
                estado="activa",
            ),
            Usuario(
                codigo_usuario="u_admin_03",
                email="ana.martinez@seareiros.local",
                contrasena_cifrada=hash_password("Ana123."),
                nombre="Ana",
                apellidos="Martínez Sánchez",
                rol="administrador",
                estado="activa",
            ),
            Usuario(
                codigo_usuario="u_admin_04",
                email="manuel.fernandez@seareiros.local",
                contrasena_cifrada=hash_password("Manuel123."),
                nombre="Manuel",
                apellidos="Fernández Gómez",
                rol="administrador",
                estado="activa",
            ),
            Usuario(
                codigo_usuario="u_admin_05",
                email="carmen.lopez@seareiros.local",
                contrasena_cifrada=hash_password("Carmen123."),
                nombre="Carmen",
                apellidos="López Martínez",
                rol="administrador",
                estado="activa",
            ),

            # Usuarios normales
            Usuario(
                codigo_usuario="u_normal_01",
                email="antonio.sanchez@seareiros.local",
                contrasena_cifrada=hash_password("Antonio123."),
                nombre="Antonio",
                apellidos="Sánchez Fernández",
                rol="normal",
                estado="activa",
            ),
            Usuario(
                codigo_usuario="u_normal_02",
                email="laura.gonzalez@seareiros.local",
                contrasena_cifrada=hash_password("Laura123."),
                nombre="Laura",
                apellidos="González Ruiz",
                rol="normal",
                estado="activa",
            ),
            Usuario(
                codigo_usuario="u_normal_03",
                email="david.perez@seareiros.local",
                contrasena_cifrada=hash_password("David123."),
                nombre="David",
                apellidos="Pérez Martín",
                rol="normal",
                estado="activa",
            ),
            Usuario(
                codigo_usuario="u_normal_04",
                email="marta.gomez@seareiros.local",
                contrasena_cifrada=hash_password("Marta123."),
                nombre="Marta",
                apellidos="Gómez Díaz",
                rol="normal",
                estado="activa",
            ),
            Usuario(
                codigo_usuario="u_normal_05",
                email="pablo.moreno@seareiros.local",
                contrasena_cifrada=hash_password("Pablo123."),
                nombre="Pablo",
                apellidos="Moreno Romero",
                rol="normal",
                estado="activa",
            ),
        ]

        session.add_all(usuarios)
        session.commit()
        print("✓ Usuarios creados correctamente")

if __name__ == "__main__":
    crear_usuarios()

