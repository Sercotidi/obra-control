from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session, obtener_o_404
from app.models import Contrato, ContratoBase, Corte

router = APIRouter(prefix="/contratos", tags=["Contratos"])


def revisar_datos(datos: ContratoBase, session: Session, id_actual: Optional[int] = None):
    """Reglas al crear o editar un contrato."""
    if datos.fecha_fin < datos.fecha_inicio:
        raise HTTPException(status_code=422, detail="fecha_fin no puede ser anterior a fecha_inicio")
    repetido = session.exec(select(Contrato).where(Contrato.numero_contrato == datos.numero_contrato)).all()
    if any(c.id != id_actual for c in repetido):
        raise HTTPException(status_code=409, detail=f"Ya existe el contrato {datos.numero_contrato}")


# CREATE
@router.post("", response_model=Contrato, status_code=201)
def crear_contrato(datos: ContratoBase, session: Session = Depends(get_session)):
    revisar_datos(datos, session)
    contrato = Contrato(**datos.model_dump())
    session.add(contrato)
    session.commit()
    session.refresh(contrato)
    return contrato


# READ (lista) + FILTROS: por nombre del contratista y por activo
@router.get("", response_model=list[Contrato])
def listar_contratos(nombre_contratista: Optional[str] = None, activo: Optional[bool] = None,
                     session: Session = Depends(get_session)):
    consulta = select(Contrato)
    if nombre_contratista:
        consulta = consulta.where(Contrato.nombre_contratista.contains(nombre_contratista))
    if activo is not None:
        consulta = consulta.where(Contrato.activo == activo)
    return session.exec(consulta).all()


# BÚSQUEDA por un atributo que NO es el ID
@router.get("/numero/{numero_contrato}", response_model=Contrato)
def buscar_por_numero(numero_contrato: str, session: Session = Depends(get_session)):
    contrato = session.exec(select(Contrato).where(Contrato.numero_contrato == numero_contrato)).first()
    if contrato is None:
        raise HTTPException(status_code=404, detail=f"No existe el contrato número {numero_contrato}")
    return contrato


# READ (uno por ID)
@router.get("/{contrato_id}", response_model=Contrato)
def obtener_contrato(contrato_id: int, session: Session = Depends(get_session)):
    return obtener_o_404(session, Contrato, contrato_id)


# UPDATE
@router.put("/{contrato_id}", response_model=Contrato)
def actualizar_contrato(contrato_id: int, datos: ContratoBase, session: Session = Depends(get_session)):
    contrato = obtener_o_404(session, Contrato, contrato_id)
    revisar_datos(datos, session, id_actual=contrato_id)
    for campo, valor in datos.model_dump().items():
        setattr(contrato, campo, valor)
    session.add(contrato)
    session.commit()
    session.refresh(contrato)
    return contrato


# DELETE lógico: no se borra, pasa a activo=False (queda en el histórico)
@router.delete("/{contrato_id}")
def eliminar_contrato(contrato_id: int, session: Session = Depends(get_session)):
    contrato = obtener_o_404(session, Contrato, contrato_id)
    # Regla de eliminación: no se elimina un contrato que tenga cortes activos
    cortes = session.exec(select(Corte).where(Corte.contrato_id == contrato_id, Corte.activo == True)).all()  # noqa: E712
    if cortes:
        raise HTTPException(status_code=409, detail="No se puede eliminar: el contrato tiene cortes activos")
    contrato.activo = False
    session.add(contrato)
    session.commit()
    return {"mensaje": f"Contrato {contrato_id} eliminado (queda en el histórico)"}