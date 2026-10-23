from sqlmodel import Session, select

from app.models import ActividadObra
from app.models.actividad_db import ActividadObraDB
from data.db.control_de_obra import create_db_tables, engine


def create_actividad_obra_db(new_actividad_obra: ActividadObra, db_engine=engine):
    """Guarda una actividad en SQLite. La validación la hace ActividadObra (Pydantic)."""
    create_db_tables() if db_engine is engine else None
    datos = new_actividad_obra.model_dump(exclude={"id"})
    with Session(db_engine) as session:
        actividad = ActividadObraDB(**datos)
        session.add(actividad)
        session.commit()
        session.refresh(actividad)
        return actividad


def show_actividad_obra(db_engine=engine):
    """Lista todas las actividades guardadas en SQLite."""
    create_db_tables() if db_engine is engine else None
    with Session(db_engine) as session:
        return list(session.exec(select(ActividadObraDB)).all())


