import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from app.database import get_session
from app.main import app

CONTRATO = {"numero_contrato": "C-001", "nombre_obra": "Campus FUCS", "empresa_cliente": "Cliente SA",
            "nombre_contratista": "Muros Ltda", "fecha_inicio": "2026-01-01", "fecha_fin": "2026-12-31",
            "valor_contrato": 5000000}
ACTIVIDAD = {"contrato_id": 1, "nombre_actividad": "Muro", "unidad_medida": "und",
             "cantidad_contratada": 5, "precio_unitario": 1000000}
CORTE = {"contrato_id": 1, "numero_corte": 1, "fecha_corte": "2026-03-01", "valor_bruto": 2000000}


@pytest.fixture
def client(tmp_path):
    """Cada prueba usa una base de datos temporal (no toca control.db)."""
    engine = create_engine(f"sqlite:///{tmp_path / 'prueba.db'}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    def sesion_de_prueba():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = sesion_de_prueba
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------- CONTRATOS ----------
def test_crud_contrato(client):
    r = client.post("/contratos", json=CONTRATO)
    assert r.status_code == 201 and r.json()["id"] == 1 and r.json()["activo"] is True
    assert client.get("/contratos/1").json()["numero_contrato"] == "C-001"
    r = client.put("/contratos/1", json={**CONTRATO, "nombre_obra": "Campus nuevo"})
    assert r.json()["nombre_obra"] == "Campus nuevo"
    assert client.delete("/contratos/1").status_code == 200


def test_id_que_no_existe_da_404(client):
    assert client.get("/contratos/99").status_code == 404
    assert client.put("/contratos/99", json=CONTRATO).status_code == 404
    assert client.delete("/contratos/99").status_code == 404
    assert client.get("/actividades/99").status_code == 404
    assert client.get("/cortes/99").status_code == 404
    assert client.get("/contratos").status_code == 200  # el servidor sigue funcionando


def test_datos_invalidos_dan_422(client):
    assert client.post("/contratos", json={**CONTRATO, "valor_contrato": -5}).status_code == 422
    assert client.post("/contratos", json={**CONTRATO, "fecha_fin": "2020-01-01"}).status_code == 422


def test_numero_de_contrato_repetido_da_409(client):
    client.post("/contratos", json=CONTRATO)
    assert client.post("/contratos", json=CONTRATO).status_code == 409


def test_filtros_de_contratos(client):
    client.post("/contratos", json=CONTRATO)
    client.post("/contratos", json={**CONTRATO, "numero_contrato": "C-002", "nombre_contratista": "Pisos SAS"})
    assert len(client.get("/contratos").json()) == 2
    assert len(client.get("/contratos", params={"nombre_contratista": "Pisos"}).json()) == 1


def test_busqueda_por_numero_de_contrato(client):
    client.post("/contratos", json=CONTRATO)
    assert client.get("/contratos/numero/C-001").json()["nombre_obra"] == "Campus FUCS"
    assert client.get("/contratos/numero/ZZZ").status_code == 404


def test_historico_con_campo_activo(client):
    client.post("/contratos", json=CONTRATO)
    client.delete("/contratos/1")
    assert client.get("/contratos", params={"activo": True}).json() == []
    inactivos = client.get("/contratos", params={"activo": False}).json()
    assert len(inactivos) == 1 and inactivos[0]["activo"] is False
    assert client.get("/contratos/1").status_code == 200  # no se borró de la base


# ---------- ACTIVIDADES ----------
def test_crud_actividad_y_filtros(client):
    assert client.post("/actividades", json=ACTIVIDAD).status_code == 404  # el contrato no existe
    client.post("/contratos", json=CONTRATO)
    assert client.post("/actividades", json=ACTIVIDAD).status_code == 201
    assert client.get("/actividades/1").json()["nombre_actividad"] == "Muro"
    assert len(client.get("/actividades", params={"contrato_id": 1}).json()) == 1
    assert len(client.get("/actividades", params={"nombre_actividad": "Piso"}).json()) == 0
    r = client.put("/actividades/1", json={**ACTIVIDAD, "cantidad_ejecutada": 2})
    assert r.json()["cantidad_ejecutada"] == 2


def test_actividad_ejecutada_no_supera_contratada(client):
    client.post("/contratos", json=CONTRATO)
    assert client.post("/actividades", json={**ACTIVIDAD, "cantidad_ejecutada": 9}).status_code == 422


def test_no_elimina_actividad_con_avance(client):
    client.post("/contratos", json=CONTRATO)
    client.post("/actividades", json={**ACTIVIDAD, "cantidad_ejecutada": 2})
    assert client.delete("/actividades/1").status_code == 409


def test_elimina_actividad_sin_avance(client):
    client.post("/contratos", json=CONTRATO)
    client.post("/actividades", json=ACTIVIDAD)
    assert client.delete("/actividades/1").status_code == 200
    assert client.get("/actividades/1").json()["activo"] is False


# ---------- CORTES ----------
def test_crud_corte_y_filtros(client):
    client.post("/contratos", json=CONTRATO)
    assert client.post("/cortes", json=CORTE).json()["estado"] == "presentado"
    assert client.post("/cortes", json=CORTE).status_code == 409  # número de corte repetido
    assert client.post("/cortes", json={**CORTE, "numero_corte": 2, "valor_bruto": 99999999}).status_code == 409
    client.put("/cortes/1", json={**CORTE, "estado": "aprobado"})
    assert len(client.get("/cortes", params={"estado": "aprobado"}).json()) == 1
    assert client.get("/cortes", params={"estado": "rechazado"}).json() == []
    assert client.get("/cortes", params={"estado": "inventado"}).status_code == 422


def test_reglas_de_cortes_aprobados(client):
    client.post("/contratos", json=CONTRATO)
    client.post("/cortes", json={**CORTE, "estado": "aprobado"})
    assert client.put("/cortes/1", json=CORTE).status_code == 409
    assert client.delete("/cortes/1").status_code == 409


def test_no_elimina_contrato_con_cortes_activos(client):
    client.post("/contratos", json=CONTRATO)
    client.post("/cortes", json=CORTE)
    assert client.delete("/contratos/1").status_code == 409
    client.delete("/cortes/1")  # el corte pasa a inactivo
    assert client.delete("/contratos/1").status_code == 200


# ---------- VER LA BASE DE DATOS ----------
def test_pagina_que_muestra_la_base_de_datos(client):
    client.post("/contratos", json=CONTRATO)
    r = client.get("/base-de-datos")
    assert r.status_code == 200
    assert "Muros Ltda" in r.text and "Tabla contrato (1 registros)" in r.text