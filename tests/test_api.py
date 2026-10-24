from decimal import Decimal

from tests.conftest import ACTIVIDAD, CONTRATO, CORTE, preparar


def test_inicio(client):
    assert client.get("/").status_code == 200


def test_crud_contrato(client):
    r = client.post("/contratos", json=CONTRATO)
    assert r.status_code == 201 and r.json()["id"] == 1 and r.json()["activo"] is True
    assert client.get("/contratos/1").json()["numero_contrato"] == "C-001"
    r = client.put("/contratos/1", json={**CONTRATO, "estado": "activo"})
    assert r.status_code == 200 and r.json()["estado"] == "activo"
    assert client.delete("/contratos/1").status_code == 204


def test_id_inexistente_da_404_sin_romper_servidor(client):
    assert client.get("/contratos/99").status_code == 404
    assert client.put("/contratos/99", json=CONTRATO).status_code == 404
    assert client.delete("/contratos/99").status_code == 404
    assert client.get("/actividades/99").status_code == 404
    assert client.get("/cortes/99").status_code == 404


def test_validacion_pydantic_da_422(client):
    assert client.post("/contratos", json={**CONTRATO, "valor_contrato": "-5"}).status_code == 422
    assert client.post("/contratos", json={**CONTRATO, "fecha_fin": "2020-01-01"}).status_code == 422


def test_numero_contrato_duplicado_409(client):
    client.post("/contratos", json=CONTRATO)
    assert client.post("/contratos", json=CONTRATO).status_code == 409


def test_busqueda_por_numero_y_filtros(client):
    client.post("/contratos", json=CONTRATO)
    client.post("/contratos", json={**CONTRATO, "numero_contrato": "C-002", "nombre_contratista": "Pisos SAS"})
    assert client.get("/contratos/numero/C-002").json()["nombre_contratista"] == "Pisos SAS"
    assert client.get("/contratos/numero/ZZZ").status_code == 404
    assert len(client.get("/contratos", params={"contratista": "muros"}).json()) == 1
    assert len(client.get("/contratos", params={"estado": "borrador"}).json()) == 2
    assert client.get("/contratos", params={"estado": "inventado"}).status_code == 422


def test_borrado_logico_conserva_historico(client):
    client.post("/contratos", json=CONTRATO)
    client.delete("/contratos/1")
    assert client.get("/contratos/1").json()["activo"] is False  # sigue existiendo
    assert client.get("/contratos", params={"activo": True}).json() == []
    assert len(client.get("/contratos", params={"activo": False}).json()) == 1


def test_actividad_crud_y_reglas(client):
    assert client.post("/actividades", json=ACTIVIDAD).status_code == 404  # contrato no existe
    client.post("/contratos", json=CONTRATO)
    assert client.post("/actividades", json=ACTIVIDAD).status_code == 201
    exceso = {**ACTIVIDAD, "precio_unitario": "9999999"}
    assert client.post("/actividades", json=exceso).status_code == 409  # supera valor del contrato
    assert len(client.get("/actividades", params={"contrato_id": 1}).json()) == 1
    assert len(client.get("/actividades", params={"nombre": "mur"}).json()) == 1
    client.put("/actividades/1", json={**ACTIVIDAD, "cantidad_ejecutada": "2"})
    assert client.delete("/actividades/1").status_code == 409  # tiene avance


def test_actividad_sin_avance_se_elimina_logicamente(client):
    client.post("/contratos", json=CONTRATO)
    client.post("/actividades", json=ACTIVIDAD)
    assert client.delete("/actividades/1").status_code == 204
    assert client.get("/actividades/1").json()["activo"] is False


def test_cortes_flujo_estados(client):
    preparar(client)
    r = client.post("/cortes", json=CORTE)
    assert r.status_code == 201
    assert Decimal(r.json()["valor_total"]) == Decimal("2000000") and len(r.json()["detalles"]) == 1
    assert client.post("/cortes", json=CORTE).status_code == 409  # numero repetido
    assert client.patch("/cortes/1/estado", params={"nuevo_estado": "aprobado"}).status_code == 409
    assert client.patch("/cortes/1/estado", params={"nuevo_estado": "presentado"}).status_code == 200
    assert client.put("/cortes/1", json={k: v for k, v in CORTE.items() if k != "detalles"}).status_code == 409
    assert client.delete("/cortes/1").status_code == 409
    assert client.patch("/cortes/1/estado", params={"nuevo_estado": "rechazado"}).json()["estado"] == "rechazado"
    assert len(client.get("/cortes", params={"estado": "rechazado"}).json()) == 1


def test_no_elimina_contrato_con_cortes_vigentes(client):
    preparar(client)
    client.post("/cortes", json=CORTE)
    assert client.delete("/contratos/1").status_code == 409