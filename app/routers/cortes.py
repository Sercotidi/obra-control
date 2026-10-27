from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session, obtener_o_404
from app.models import Contrato, Corte, CorteBase, EstadoCorte

router = APIRouter(prefix="/cortes", tags=["Cortes"])


def revisar_datos(datos: CorteBase, session: Session, id_actual: Optional[int] = None):
    """Reglas al crear o editar un corte."""
    contrato = obtener_o_404(session, Contrato, datos.contrato_id)  # el contrato debe existir
    if not contrato.activo:
        raise HTTPException(status_code=409, detail="El contrato está inactivo")
    if datos.valor_bruto > contrato.valor_contrato:
        raise HTTPException(status_code=409, detail="El corte no puede valer más que el contrato")
    mismos = session.exec(select(Corte).where(Corte.contrato_id == datos.contrato_id,
                                              Corte.numero_corte == datos.numero_corte,
                                              Corte.activo == True)).all()  # noqa: E712
    if any(c.id != id_actual for c in mismos):
        raise HTTPException(status_code=409, detail="Ya existe ese número de corte en el contrato")


# CREATE
@router.post("", response_model=Corte, status_code=201)
def crear_corte(datos: CorteBase, session: Session = Depends(get_session)):
    revisar_datos(datos, session)
    corte = Corte(**datos.model_dump())
    session.add(corte)
    session.commit()
    session.refresh(corte)
    return corte


# READ (lista) + FILTROS: por contrato, por estado y por activo
@router.get("", response_model=list[Corte])
def listar_cortes(contrato_id: Optional[int] = None, estado: Optional[EstadoCorte] = None,
                  activo: Optional[bool] = None, session: Session = Depends(get_session)):
    consulta = select(Corte)
    if contrato_id is not None:
        consulta = consulta.where(Corte.contrato_id == contrato_id)
    if estado:
        consulta = consulta.where(Corte.estado == estado)
    if activo is not None:
        consulta = consulta.where(Corte.activo == activo)
    return session.exec(consulta).all()


# READ (uno por ID)
@router.get("/{corte_id}", response_model=Corte)
def obtener_corte(corte_id: int, session: Session = Depends(get_session)):
    return obtener_o_404(session, Corte, corte_id)


# UPDATE
@router.put("/{corte_id}", response_model=Corte)
def actualizar_corte(corte_id: int, datos: CorteBase, session: Session = Depends(get_session)):
    corte = obtener_o_404(session, Corte, corte_id)
    # Regla: un corte aprobado ya no se modifica
    if corte.estado == EstadoCorte.aprobado:
        raise HTTPException(status_code=409, detail="Un corte aprobado no se puede modificar")
    revisar_datos(datos, session, id_actual=corte_id)
    for campo, valor in datos.model_dump().items():
        setattr(corte, campo, valor)
    session.add(corte)
    session.commit()
    session.refresh(corte)
    return corte


# DELETE lógico
@router.delete("/{corte_id}")
def eliminar_corte(corte_id: int, session: Session = Depends(get_session)):
    corte = obtener_o_404(session, Corte, corte_id)
    # Regla de eliminación: un corte aprobado no se elimina
    if corte.estado == EstadoCorte.aprobado:
        raise HTTPException(status_code=409, detail="No se puede eliminar un corte aprobado")
    corte.activo = False
    session.add(corte)
    session.commit()
    return {"mensaje": f"Corte {corte_id} eliminado (queda en el histórico)"}