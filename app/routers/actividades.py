from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session, obtener_o_404
from app.models import Actividad, ActividadBase, Contrato

router = APIRouter(prefix="/actividades", tags=["Actividades"])


def revisar_datos(datos: ActividadBase, session: Session):
    """Reglas al crear o editar una actividad."""
    contrato = obtener_o_404(session, Contrato, datos.contrato_id)  # el contrato debe existir
    if not contrato.activo:
        raise HTTPException(status_code=409, detail="El contrato está inactivo")
    if datos.cantidad_ejecutada > datos.cantidad_contratada:
        raise HTTPException(status_code=422, detail="cantidad_ejecutada no puede superar cantidad_contratada")


# CREATE
@router.post("", response_model=Actividad, status_code=201)
def crear_actividad(datos: ActividadBase, session: Session = Depends(get_session)):
    revisar_datos(datos, session)
    actividad = Actividad(**datos.model_dump())
    session.add(actividad)
    session.commit()
    session.refresh(actividad)
    return actividad


# READ (lista) + FILTROS: por contrato, por nombre y por activo
@router.get("", response_model=list[Actividad])
def listar_actividades(contrato_id: Optional[int] = None, nombre_actividad: Optional[str] = None,
                       activo: Optional[bool] = None, session: Session = Depends(get_session)):
    consulta = select(Actividad)
    if contrato_id is not None:
        consulta = consulta.where(Actividad.contrato_id == contrato_id)
    if nombre_actividad:
        consulta = consulta.where(Actividad.nombre_actividad.contains(nombre_actividad))
    if activo is not None:
        consulta = consulta.where(Actividad.activo == activo)
    return session.exec(consulta).all()


# READ (uno por ID)
@router.get("/{actividad_id}", response_model=Actividad)
def obtener_actividad(actividad_id: int, session: Session = Depends(get_session)):
    return obtener_o_404(session, Actividad, actividad_id)


# UPDATE
@router.put("/{actividad_id}", response_model=Actividad)
def actualizar_actividad(actividad_id: int, datos: ActividadBase, session: Session = Depends(get_session)):
    actividad = obtener_o_404(session, Actividad, actividad_id)
    revisar_datos(datos, session)
    for campo, valor in datos.model_dump().items():
        setattr(actividad, campo, valor)
    session.add(actividad)
    session.commit()
    session.refresh(actividad)
    return actividad


# DELETE lógico
@router.delete("/{actividad_id}")
def eliminar_actividad(actividad_id: int, session: Session = Depends(get_session)):
    actividad = obtener_o_404(session, Actividad, actividad_id)
    # Regla de eliminación: no se elimina una actividad que ya tiene avance ejecutado
    if actividad.cantidad_ejecutada > 0:
        raise HTTPException(status_code=409, detail="No se puede eliminar: la actividad ya tiene avance ejecutado")
    actividad.activo = False
    session.add(actividad)
    session.commit()
    return {"mensaje": f"Actividad {actividad_id} eliminada (queda en el histórico)"}