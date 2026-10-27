from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import crear_tablas
from app.routers import actividades, contratos, cortes, vista


@asynccontextmanager
async def lifespan(app: FastAPI):
    crear_tablas()  # al arrancar el servidor, se crea control.db con sus tablas
    yield


app = FastAPI(title="ObraControl", description="Contratos, actividades y cortes de obra", lifespan=lifespan)

app.include_router(contratos.router)
app.include_router(actividades.router)
app.include_router(cortes.router)
app.include_router(vista.router)


@app.get("/", tags=["Inicio"])
def inicio():
    return {"proyecto": "ObraControl", "documentacion": "/docs", "ver_base_de_datos": "/base-de-datos"}

