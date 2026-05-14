from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, socios

app = FastAPI(
    title='Seareiros API',
    version='1.0.0',
    description='Plataforma de gestión para peñas deportivas'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173'], 
    allow_methods=['*'],
    allow_headers=['*']
)

app.include_router(auth.router)
app.include_router(socios.router)
