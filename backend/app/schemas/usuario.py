from pydantic import BaseModel

class LoginInput(BaseModel):
    identificador: str  # Puede ser email o codigo_usuario
    contrasena: str

class TokenOutput(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UsuarioOutput(BaseModel):
    id: str
    codigo_usuario: str
    email: str
    nombre: str
    apellidos: str
    rol: str
    estado: str

class UsuarioListOutput(BaseModel):
    id:             str
    codigo_usuario: str
    nombre:         str
    apellidos:      str
    rol:            str
    estado:         str    
