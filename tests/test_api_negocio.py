from decimal import Decimal as D

from tests.conftest import CORTE, preparar


def test_ejemplo_del_enunciado_por_api(client):
    preparar(client, ejecutada="2")
    client.post("/cortes", json=CORTE)
    client.patch("/cortes/1/estado", params={"nuevo_estado": "presentado"})
    client.patch("/cortes/1/estado", params={"nuevo_estado": "aprobado"})
    client.patch("/actividades/1/avance", json={"cantidad_ejecutada": "3"})
    r = client.get("/contratos/1/resumen").json()
    assert D(r["valor_contratado"]) == D("5000000")
    assert D(r["valor_ejecutado"]) == D("3000000")
    assert D(r["valor_en_cortes_activos"]) == D("2000000")
    assert D(r["valor_aprobado"]) == D("2000000")
    assert D(r["valor_disponible_para_cobrar"]) == D("1000000")
    assert D(r["valor_pendiente_ejecutar"]) == D("2000000")


def test_no_duplica_cantidades_por_api(client):
    preparar(client, ejecutada="2")
    assert client.post("/cortes", json=CORTE).status_code == 201
    otro = {**CORTE, "numero_corte": 2, "detalles": [{"actividad_id": 1, "cantidad": "1"}]}
    assert client.post("/cortes", json=otro).status_code == 409  # ya se cobraron los 2


def test_rechazado_libera_cantidad(client):
    preparar(client, ejecutada="2")
    client.post("/cortes", json=CORTE)
    client.patch("/cortes/1/estado", params={"nuevo_estado": "presentado"})
    client.patch("/cortes/1/estado", params={"nuevo_estado": "rechazado"})
    q = client.get("/actividades/1/cantidades").json()
    assert D(q["aprobada"]) == 0 and D(q["disponible_para_cobrar"]) == 2
    assert client.post("/cortes", json={**CORTE, "numero_corte": 2}).status_code == 201


def test_borrar_corte_borrador_libera_cantidad_y_deja_historico(client):
    preparar(client, ejecutada="2")
    client.post("/cortes", json=CORTE)
    assert client.delete("/cortes/1").status_code == 204
    assert D(client.get("/actividades/1/cantidades").json()["disponible_para_cobrar"]) == 2
    assert client.get("/cortes/1").json()["activo"] is False
    assert len(client.get("/cortes", params={"activo": False}).json()) == 1


def test_validaciones_de_corte(client):
    preparar(client, ejecutada="1")
    assert client.post("/cortes", json=CORTE).status_code == 409  # pide 2, solo hay 1
    assert client.get("/cortes").json() == []  # no dejó basura
    assert client.post("/cortes", json={**CORTE, "detalles": []}).status_code == 422
    dup = {**CORTE, "detalles": [{"actividad_id": 1, "cantidad": "1"}, {"actividad_id": 1, "cantidad": "1"}]}
    assert client.post("/cortes", json=dup).status_code == 409
    assert client.post("/cortes", json={**CORTE, "detalles": [{"actividad_id": 99, "cantidad": "1"}]}).status_code == 404
    assert client.post("/cortes", json={**CORTE, "fecha_corte": "2026-01-01"}).status_code == 422


def test_avance_no_baja_de_lo_cortado_ni_supera_contratado(client):
    preparar(client, ejecutada="3")
    client.post("/cortes", json=CORTE)
    assert client.patch("/actividades/1/avance", json={"cantidad_ejecutada": "1"}).status_code == 409
    assert client.patch("/actividades/1/avance", json={"cantidad_ejecutada": "9"}).status_code == 409