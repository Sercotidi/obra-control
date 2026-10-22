from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Response

from app.dependencies import repo_actividades, repo_contratos
from app.errors import ReglaNegocioError
from app.models import ActividadObra
from data.db.operations_db import create_actividad_obra_db

router = APIRouter(prefix="/actividades", tags=["Actividades"])


def _validar_contrato_y_valor(act: ActividadObra, contratos, actividades, excluir_id=None):
    contrato = contratos.obtener(act.contrato_id)  # 404 si no existe
    if not contrato.activo:
        raise ReglaNegocioError("El contrato está inactivo")
    total = sum((a.valor_contratado for a in actividades.listar()
                 if a.contrato_id == act.contrato_id and a.activo and a.id != excluir_id), Decimal("0"))
    if total + act.valor_contratado > contrato.valor_contrato:
        raise ReglaNegocioError("Las actividades superan el valor del contrato,verifica")


@router.post("", response_model=ActividadObra, status_code=201)
def crear_actividad(act: ActividadObra, repo=Depends(repo_actividades), contratos=Depends(repo_contratos)):
    return create_actividad_obra_db((new_actividad_obra)



@router.get("", response_model=list[ActividadObra])
def listar_actividades(contrato_id: Optional[int] = None, nombre: Optional[str] = None,
                       activo: Optional[bool] = None, repo=Depends(repo_actividades)):
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


@router.put("/{actividad_id}", response_model=ActividadObra)
def actualizar_actividad(actividad_id: int, act: ActividadObra, repo=Depends(repo_actividades),
                         contratos=Depends(repo_contratos)):
    repo.obtener(actividad_id)
    _validar_contrato_y_valor(act, contratos, repo, excluir_id=actividad_id)
    return repo.actualizar(actividad_id, act)


@router.delete("/{actividad_id}", status_code=204)
def eliminar_actividad(actividad_id: int, repo=Depends(repo_actividades)):
