from typing import Optional

from fastapi import APIRouter, Depends, Response

from app.dependencies import repo_cortes, servicio_obra
from app.models import CorteObra, EstadoCorte
from app.schemas import CorteCrear, CorteDetallado

router = APIRouter(prefix="/cortes", tags=["Cortes"])


def _detallado(corte: CorteObra, svc) -> CorteDetallado:
    return CorteDetallado(**corte.model_dump(), detalles=svc.detalles_de_corte(corte.id),
                          valor_total=svc.valor_corte(corte.id))


@router.post("", response_model=CorteDetallado, status_code=201)
def crear_corte(body: CorteCrear, svc=Depends(servicio_obra)):
    """Crea el corte en borrador junto con sus detalles (actividad y cantidad)."""
    datos = body.model_dump(exclude={"detalles", "id", "activo"})
    corte = CorteObra(**datos)
    items = [(d.actividad_id, d.cantidad) for d in body.detalles]
    return _detallado(svc.crear_corte(corte, items), svc)


@router.get("", response_model=list[CorteObra])
def listar_cortes(contrato_id: Optional[int] = None, estado: Optional[EstadoCorte] = None,
                  activo: Optional[bool] = None, repo=Depends(repo_cortes)):
    """Filtros: contrato_id, estado y activo."""
    res = repo.listar()
    if contrato_id is not None:
        res = [c for c in res if c.contrato_id == contrato_id]
    if estado:
        res = [c for c in res if c.estado == estado]
    if activo is not None:
        res = [c for c in res if c.activo == activo]
    return res


@router.get("/historico", response_model=list[CorteObra])
def historico_cortes(repo=Depends(repo_cortes)):
    """Registros eliminados (activo=False)."""
    return [x for x in repo.listar() if not x.activo]


@router.get("/{corte_id}", response_model=CorteDetallado)
def obtener_corte(corte_id: int, repo=Depends(repo_cortes), svc=Depends(servicio_obra)):
    return _detallado(repo.obtener(corte_id), svc)


@router.put("/{corte_id}", response_model=CorteObra)
def actualizar_corte(corte_id: int, corte: CorteObra, svc=Depends(servicio_obra)):
    """Solo se editan los datos de un corte en borrador. El estado cambia con PATCH /cortes/{id}/estado."""
    return svc.actualizar_corte(corte_id, corte)


@router.patch("/{corte_id}/estado", response_model=CorteObra)
def cambiar_estado(corte_id: int, nuevo_estado: EstadoCorte, svc=Depends(servicio_obra)):
    return svc.cambiar_estado_corte(corte_id, nuevo_estado)


@router.delete("/{corte_id}", status_code=204)
def eliminar_corte(corte_id: int, svc=Depends(servicio_obra)):
    """Borrado lógico. Solo en borrador; libera las cantidades del corte."""
    svc.eliminar_corte(corte_id)
    return Response(status_code=204)