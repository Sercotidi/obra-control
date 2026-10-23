from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.errors import ReglaNegocioError
from app.repositories.errors import DatosCorruptos, RegistroNoEncontrado
from app.routers import actividades, contratos, cortes

app = FastAPI(title="ObraControl", description="Avances, cortes y cobros de obra (CSV)", version="0.1.0")
app.include_router(contratos.router)
app.include_router(actividades.router)
app.include_router(cortes.router)


@app.exception_handler(RegistroNoEncontrado)
async def no_encontrado(request: Request, exc: RegistroNoEncontrado):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ReglaNegocioError)
async def regla_negocio(request: Request, exc: ReglaNegocioError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(DatosCorruptos)
async def datos_corruptos(request: Request, exc: DatosCorruptos):
    return JSONResponse(status_code=500, content={"detail": "Error leyendo los archivos CSV"})


@app.get("/", tags=["Inicio"])
def inicio():
    return {"proyecto": "ObraControl", "docs": "/docs"}
