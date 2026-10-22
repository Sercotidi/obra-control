from models.ActividadObra import id contrato_obra nombre_actividad unidad_medida
from sqlmodel import SQLModel, Session, select
from actividad import engine
from app.models import ActividadObra, contrato


def create_actividad_obra_db(new_actividad_obra:ActividadBase):
    session: Session(engine)
    actividad = ActividadObra.model_validate(new_actividad_obra)
    session.add(actividad)
    session.commit()
    session.refresh(actividad)
    session.close()

    return actividad
