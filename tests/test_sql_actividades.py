from decimal import Decimal

from sqlmodel import SQLModel, create_engine

from app.models import ActividadObra
from data.db.operations_db import create_actividad_obra_db, show_actividad_obra


def test_guardar_y_listar_actividad_en_sqlite(tmp_path):
    motor = create_engine(f"sqlite:///{tmp_path / 'prueba.db'}")
    SQLModel.metadata.create_all(motor)
    act = ActividadObra(contrato_id=1, nombre_actividad="Muro", unidad_medida="und",
                        cantidad_contratada=Decimal("5"), precio_unitario=Decimal("1000000"))
    guardada = create_actividad_obra_db(act, db_engine=motor)
    assert guardada.id == 1
    lista = show_actividad_obra(db_engine=motor)
    assert len(lista) == 1 and lista[0].nombre_actividad == "Muro"
    assert lista[0].precio_unitario == Decimal("1000000")
