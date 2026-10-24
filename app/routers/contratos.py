from typing import Optional

from fastapi import APIRouter, Depends, Response

from app.dependencies import repo_contratos, servicio_obra
from app.errors import ReglaNegocioError
from app.models import ContratoObra, EstadoContrato
from app.repositories.errors import RegistroNoEncontrado
from app.schemas import ResumenContrato

router = APIRouter(prefix="/contratos", tags=["Contratos"])


@router.post("", response_model=ContratoObra, status_code=201)
def crear_contrato(contrato: ContratoObra, repo=Depends(repo_contratos)):
    if any(c.numero_contrato == contrato.numero_contrato for c in repo.listar()):
        raise ReglaNegocioError(f"Ya existe el contrato {contrato.numero_contrato}")
    return repo.crear(contrato)


@router.get("", response_model=list[ContratoObra])
def listar_contratos(estado: Optional[EstadoContrato] = None, contratista: Optional[str] = None,
                     activo: Optional[bool] = None, repo=Depends(repo_contratos)):
    """Filtros: estado, contratista (texto parcial) y activo."""
    res = repo.listar()
    if estado:
        res = [c for c in res if c.estado == estado]
    if contratista:
        res = [c for c in res if contratista.lower() in c.nombre_contratista.lower()]
    if activo is not None:
        res = [c for c in res if c.activo == activo]
    return res


@router.get("/historico", response_model=list[ContratoObra])
def historico_contratos(repo=Depends(repo_contratos)):
    """Registros eliminados (activo=False)."""
    return [x for x in repo.listar() if not x.activo]


@router.get("/numero/{numero_contrato}", response_model=ContratoObra)
def buscar_por_numero(numero_contrato: str, repo=Depends(repo_contratos)):
    """Búsqueda por un atributo distinto al ID."""
    for c in repo.listar():
        if c.numero_contrato == numero_contrato:
            return c
    raise RegistroNoEncontrado(f"No existe el contrato número {numero_contrato}")


@router.get("/{contrato_id}", response_model=ContratoObra)
def obtener_contrato(contrato_id: int, repo=Depends(repo_contratos)):
    return repo.obtener(contrato_id)


@router.get("/{contrato_id}/resumen", response_model=ResumenContrato)
def resumen_contrato(contrato_id: int, svc=Depends(servicio_obra)):
    """Valores contratado, ejecutado, en cortes, aprobado, disponible y pendiente."""
    return svc.resumen_contrato(contrato_id)


@router.put("/{contrato_id}", response_model=ContratoObra)
def actualizar_contrato(contrato_id: int, contrato: ContratoObra, repo=Depends(repo_contratos)):
    repo.obtener(contrato_id)
    if any(c.numero_contrato == contrato.numero_contrato and c.id != contrato_id for c in repo.listar()):
        raise ReglaNegocioError(f"Ya existe el contrato {contrato.numero_contrato}")
    return repo.actualizar(contrato_id, contrato)


@router.delete("/{contrato_id}", status_code=204)
def eliminar_contrato(contrato_id: int, svc=Depends(servicio_obra)):
    """Borrado lógico (activo=False). No se permite si tiene cortes vigentes."""
    svc.eliminar_contrato(contrato_id)
    return Response(status_code=204)