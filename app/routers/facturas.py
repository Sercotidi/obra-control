from typing import Optional

from fastapi import APIRouter, Depends, Response

from app.dependencies import repo_facturas, servicio_obra
from app.models import FacturaObra
from app.repositories.errors import RegistroNoEncontrado
from app.schemas import FacturaDetallada

router = APIRouter(prefix="/facturas", tags=["Facturas"])


def _detallada(f: FacturaObra, svc) -> FacturaDetallada:
    pagado = svc.valor_pagado_factura(f.id)
    return FacturaDetallada(**f.model_dump(), valor_pagado=pagado, saldo=f.valor - pagado)


@router.post("", response_model=FacturaDetallada, status_code=201)
def crear_factura(factura: FacturaObra, svc=Depends(servicio_obra)):
    """Solo se factura un corte aprobado y sin pasar el valor del corte."""
    return _detallada(svc.crear_factura(factura), svc)


@router.get("", response_model=list[FacturaObra])
def listar_facturas(contrato_id: Optional[int] = None, corte_id: Optional[int] = None,
                    activo: Optional[bool] = None, repo=Depends(repo_facturas)):
    """Filtros: contrato_id, corte_id y activo."""
    res = repo.listar()
    if contrato_id is not None:
        res = [f for f in res if f.contrato_id == contrato_id]
    if corte_id is not None:
        res = [f for f in res if f.corte_id == corte_id]
    if activo is not None:
        res = [f for f in res if f.activo == activo]
    return res


@router.get("/historico", response_model=list[FacturaObra])
def historico_facturas(repo=Depends(repo_facturas)):
    """Facturas eliminadas (activo=False)."""
    return [f for f in repo.listar() if not f.activo]


@router.get("/numero/{numero_factura}", response_model=FacturaDetallada)
def buscar_por_numero(numero_factura: str, repo=Depends(repo_facturas), svc=Depends(servicio_obra)):
    """Búsqueda por un atributo distinto al ID."""
    for f in repo.listar():
        if f.numero_factura == numero_factura and f.activo:
            return _detallada(f, svc)
    raise RegistroNoEncontrado(f"No existe la factura {numero_factura}")


@router.get("/{factura_id}", response_model=FacturaDetallada)
def obtener_factura(factura_id: int, repo=Depends(repo_facturas), svc=Depends(servicio_obra)):
    """Incluye valor pagado y saldo pendiente de recaudo."""
    return _detallada(repo.obtener(factura_id), svc)


@router.put("/{factura_id}", response_model=FacturaDetallada)
def actualizar_factura(factura_id: int, factura: FacturaObra, svc=Depends(servicio_obra)):
    return _detallada(svc.actualizar_factura(factura_id, factura), svc)


@router.delete("/{factura_id}", status_code=204)
def eliminar_factura(factura_id: int, svc=Depends(servicio_obra)):
    """Borrado lógico. No se permite si la factura ya tiene pagos."""
    svc.eliminar_factura(factura_id)
    return Response(status_code=204)