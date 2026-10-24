from typing import Optional

from fastapi import APIRouter, Depends, Response

from app.dependencies import repo_pagos, servicio_obra
from app.models import PagoObra

router = APIRouter(prefix="/pagos", tags=["Pagos"])


@router.post("", response_model=PagoObra, status_code=201)
def crear_pago(pago: PagoObra, svc=Depends(servicio_obra)):
    """El pago no puede superar el saldo de la factura."""
    return svc.crear_pago(pago)


@router.get("", response_model=list[PagoObra])
def listar_pagos(factura_id: Optional[int] = None, activo: Optional[bool] = None, repo=Depends(repo_pagos)):
    """Filtros: factura_id y activo."""
    res = repo.listar()
    if factura_id is not None:
        res = [p for p in res if p.factura_id == factura_id]
    if activo is not None:
        res = [p for p in res if p.activo == activo]
    return res


@router.get("/{pago_id}", response_model=PagoObra)
def obtener_pago(pago_id: int, repo=Depends(repo_pagos)):
    return repo.obtener(pago_id)


@router.put("/{pago_id}", response_model=PagoObra)
def actualizar_pago(pago_id: int, pago: PagoObra, svc=Depends(servicio_obra)):
    return svc.actualizar_pago(pago_id, pago)


@router.delete("/{pago_id}", status_code=204)
def eliminar_pago(pago_id: int, svc=Depends(servicio_obra)):
    """Borrado lógico (queda en el histórico y deja de contar como recaudado)."""
    svc.eliminar_pago(pago_id)
    return Response(status_code=204)