import pytest
from fastapi.testclient import TestClient
from sqlmodel import create_engine

from app import dependencies
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    # base SQLite temporal: las pruebas no tocan control.db
    monkeypatch.setattr(dependencies, "ENGINE", create_engine(f"sqlite:///{tmp_path / 'test.db'}"))
    return TestClient(app)


CONTRATO = {"numero_contrato": "C-001", "nombre_obra": "Campus FUCS", "empresa_cliente": "Cliente SA",
            "nombre_contratista": "Muros Ltda", "fecha_inicio": "2026-01-01", "fecha_fin": "2026-12-31",
            "valor_contrato": "5000000"}
ACTIVIDAD = {"contrato_id": 1, "nombre_actividad": "Muro", "unidad_medida": "und",
             "cantidad_contratada": "5", "precio_unitario": "1000000"}
CORTE = {"contrato_id": 1, "numero_corte": 1, "fecha_corte": "2026-03-01",
         "periodo_inicio": "2026-02-01", "periodo_fin": "2026-02-28",
         "detalles": [{"actividad_id": 1, "cantidad": "2"}]}


def preparar(client, ejecutada="3"):
    """Crea contrato C-001 + actividad (5 muros a 1.000.000) con avance registrado."""
    client.post("/contratos", json=CONTRATO)
    client.post("/actividades", json=ACTIVIDAD)
    client.patch("/actividades/1/avance", json={"cantidad_ejecutada": ejecutada})
