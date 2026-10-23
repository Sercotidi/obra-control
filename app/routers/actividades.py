from typing import Optional

from fastapi import APIRouter, Depends, Response

from app.dependencies import repo_actividades, servicio_obra
from app.models import ActividadObra
from app.schemas import AvanceEntrada, CantidadesActividad

router = APIRouter(prefix="/actividades", tags=["Actividades"])


@router.post("", response_model=ActividadObra, status_code=201)
def crear_actividad(act: ActividadObra, svc=Depends(servicio_obra)):
    return svc.crear_actividad(act)


@router.get("", response_model=list[ActividadObra])
def listar_actividades(contrato_id: Optional[int] = None, nombre: Optional[str] = None,
                       activo: Optional[bool] = None, repo=Depends(repo_actividades)):
    """Filtros: contrato_id, nombre (texto parcial) y activo."""
    res = repo.listar()
    if contrato_id is not None:
        res = [a for a in res if a.contrato_id == contrato_id]
    if nombre:
        res = [a for a in res if nombre.lower() in a.nombre_actividad.lower()]
    if activo is not None:
        res = [a for a in res if a.activo == activo]
    return res


@router.get("/{actividad_id}", response_model=ActividadObra)
def obtener_actividad(actividad_id: int, repo=Depends(repo_actividades)):
    return repo.obtener(actividad_id)


@router.get("/{actividad_id}/cantidades", response_model=CantidadesActividad)
def cantidades_actividad(actividad_id: int, svc=Depends(servicio_obra)):
    """Contratada, ejecutada, en cortes, aprobada, disponible para cobrar y pendiente."""
    return svc.cantidades_actividad(actividad_id)


@router.put("/{actividad_id}", response_model=ActividadObra)
def actualizar_actividad(actividad_id: int, act: ActividadObra, svc=Depends(servicio_obra)):
    return svc.actualizar_actividad(actividad_id, act)


@router.patch("/{actividad_id}/avance", response_model=ActividadObra)
def registrar_avance(actividad_id: int, avance: AvanceEntrada, svc=Depends(servicio_obra)):
    """Registra la cantidad total ejecutada hasta hoy."""
    return svc.registrar_avance(actividad_id, avance.cantidad_ejecutada)


@router.delete("/{actividad_id}", status_code=204)
def eliminar_actividad(actividad_id: int, svc=Depends(servicio_obra)):
    """Borrado lógico. No se permite si la actividad ya tiene avance ejecutado."""
    svc.eliminar_actividad(actividad_id)
    return Response(status_code=204)