from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, socios, sorteos, usuarios, chats, eventos
from app.scheduler import iniciar_scheduler, scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona el ciclo de vida de la aplicación.
    Al arrancar: inicia el planificador de sorteos.
    Al apagar: detiene el planificador limpiamente.
    """
    iniciar_scheduler()
    yield
    if scheduler.running:
        scheduler.shutdown()


app = FastAPI(
    title="Seareiros API",
    version="1.0.0",
    description="Plataforma de gestión para peñas deportivas",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(socios.router)
app.include_router(sorteos.router)
app.include_router(chats.router)
app.include_router(eventos.router)
