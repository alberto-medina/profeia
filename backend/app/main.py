"""
Punto de entrada del backend de ProfeIA (FastAPI).

Para correr en desarrollo:
    uvicorn app.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import obtener_configuracion
from app.routers import accesibilidad, auth, clases, exportacion, multimedia, pagos, planes, publico

configuracion = obtener_configuracion()
RUTA_GENERATED = "generated"

app = FastAPI(
    title="ProfeIA API",
    description="Backend del copiloto de IA para docentes - ProfeIA",
    version="1.0.0",
)

# CORS abierto en desarrollo. En produccion, restringir a los dominios
# reales del frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(planes.router)
app.include_router(pagos.router)
app.include_router(clases.router)
app.include_router(multimedia.router)
app.include_router(exportacion.router)
app.include_router(accesibilidad.router)
app.include_router(publico.router)
app.mount(
    "/generated",
    StaticFiles(directory=RUTA_GENERATED, check_dir=False),
    name="generated",
)


@app.get("/", tags=["estado"])
async def raiz():
    """Endpoint de salud basico."""
    return {
        "app": "ProfeIA",
        "estado": "ok",
        "entorno": configuracion.entorno,
    }
