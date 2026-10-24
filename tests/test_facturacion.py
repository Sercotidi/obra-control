from datetime import date
from decimal import Decimal as D

import pytest
from pydantic import ValidationError

from app.models import FacturaObra, PagoObra
from tests.conftest import CORTE, preparar


def factura(**kw):
    base = {"contrato_id": 1, "corte_id": 1, "numero_factura": "F-001",
            "fecha_factura": "2026-03-10", "valor": "2000000"}
    base.update(kw)
    return base


def pago(**kw):
    base = {"factura_id": 1, "fecha_pago": "2026-04-01", "valor": "500000"}
    base.update(kw)
    return base


def corte_aprobado(client):
    """Contrato + 5 muros (3 ejecutados) + corte 1 de 2 muros = 2.000.000, aprobado."""
    preparar(client, ejecutada="3")
    client.post("/cortes", json=CORTE)
    client.patch("/cortes/1/estado", params={"nuevo_estado": "presentado"})
    client.patch("/cortes/1/estado", params={"nuevo_estado": "aprobado"})


# ---- modelos
def test_modelos_validan_valores():
    with pytest.raises(ValidationError):
        FacturaObra(contrato_id=1, corte_id=1, numero_factura="F", fecha_factura=date(2026, 1, 1), valor=D("0"))
    with pytest.raises(ValidationError):
        PagoObra(factura_id=1, fecha_pago=date(2026, 1, 1), valor=D("-1"))


# ---- facturas
def test_solo_se_factura_corte_aprobado(client):
    preparar(client, ejecutada="3")
    client.post("/cortes", json=CORTE)  # queda en borrador
    assert client.post("/facturas", json=factura()).status_code == 409


def test_crear_factura_y_consultar_saldo(client):
    corte_aprobado(client)
    r = client.post("/facturas", json=factura())
    assert r.status_code == 201
    assert D(r.json()["valor_pagado"]) == 0 and D(r.json()["saldo"]) == D("2000000")


def test_factura_no_supera_valor_del_corte_ni_repite_numero(client):
    corte_aprobado(client)
    assert client.post("/facturas", json=factura(valor="2500000")).status_code == 409
    assert client.post("/facturas", json=factura(valor="1500000")).status_code == 201
    assert client.post("/facturas", json=factura(numero_factura="F-002", valor="600000")).status_code == 409
    assert client.post("/facturas", json=factura(valor="100000")).status_code == 409  # numero repetido
    assert client.post("/facturas", json=factura(numero_factura="F-002", valor="500000")).status_code == 201


def test_factura_validaciones_404_y_422(client):
    corte_aprobado(client)
    assert client.post("/facturas", json=factura(corte_id=99)).status_code == 404
    assert client.post("/facturas", json=factura(valor="-5")).status_code == 422
    assert client.get("/facturas/99").status_code == 404
    assert client.put("/facturas/99", json=factura()).status_code == 404
    assert client.delete("/facturas/99").status_code == 404


def test_buscar_y_filtrar_facturas(client):
    corte_aprobado(client)
    client.post("/facturas", json=factura())
    assert client.get("/facturas/numero/F-001").json()["numero_factura"] == "F-001"
    assert client.get("/facturas/numero/ZZ").status_code == 404
    assert len(client.get("/facturas", params={"contrato_id": 1}).json()) == 1
    assert client.get("/facturas", params={"corte_id": 5}).json() == []


# ---- pagos
def test_pagos_parciales_y_saldo(client):
    corte_aprobado(client)
    client.post("/facturas", json=factura())
    assert client.post("/pagos", json=pago(valor="500000")).status_code == 201
    assert client.post("/pagos", json=pago(valor="1000000")).status_code == 201
    f = client.get("/facturas/1").json()
    assert D(f["valor_pagado"]) == D("1500000") and D(f["saldo"]) == D("500000")
    assert client.post("/pagos", json=pago(valor="500001")).status_code == 409  # supera el saldo
    assert client.post("/pagos", json=pago(valor="500000")).status_code == 201  # lo salda


def test_pago_reglas(client):
    corte_aprobado(client)
    client.post("/facturas", json=factura())
    assert client.post("/pagos", json=pago(fecha_pago="2026-01-01")).status_code == 409  # antes de la factura
    assert client.post("/pagos", json=pago(factura_id=99)).status_code == 404
    assert client.post("/pagos", json=pago(valor="0")).status_code == 422
    assert client.get("/pagos/99").status_code == 404


def test_actualizar_y_filtrar_pagos(client):
    corte_aprobado(client)
    client.post("/facturas", json=factura())
    client.post("/pagos", json=pago())
    assert client.put("/pagos/1", json=pago(valor="700000")).json()["valor"] == "700000.00"
    assert client.put("/pagos/1", json=pago(valor="9999999")).status_code == 409
    assert len(client.get("/pagos", params={"factura_id": 1}).json()) == 1


# ---- histórico y reglas de eliminación
def test_no_elimina_factura_con_pagos_y_pago_borrado_libera_saldo(client):
    corte_aprobado(client)
    client.post("/facturas", json=factura())
    client.post("/pagos", json=pago())
    assert client.delete("/facturas/1").status_code == 409
    assert client.put("/facturas/1", json=factura(valor="2000000")).status_code == 409  # tiene pagos
    assert client.delete("/pagos/1").status_code == 204
    assert D(client.get("/facturas/1").json()["saldo"]) == D("2000000")
    assert len(client.get("/pagos", params={"activo": False}).json()) == 1
    assert client.delete("/facturas/1").status_code == 204
    assert len(client.get("/facturas/historico").json()) == 1


def test_historico_de_contratos_y_actividades(client):
    preparar(client, ejecutada="0")
    client.delete("/actividades/1")
    client.delete("/contratos/1")
    assert [a["id"] for a in client.get("/actividades/historico").json()] == [1]
    assert [c["id"] for c in client.get("/contratos/historico").json()] == [1]
    assert client.get("/contratos", params={"activo": True}).json() == []


def test_historico_de_cortes(client):
    preparar(client, ejecutada="3")
    client.post("/cortes", json=CORTE)
    assert client.get("/cortes/historico").json() == []
    client.delete("/cortes/1")  # borrador -> borrado logico
    assert [c["id"] for c in client.get("/cortes/historico").json()] == [1]


# ---- resumen financiero
def test_resumen_separa_facturado_pagado_y_saldo(client):
    corte_aprobado(client)
    client.post("/facturas", json=factura(valor="1500000"))
    client.post("/pagos", json=pago(valor="400000"))
    r = client.get("/contratos/1/resumen").json()
    assert D(r["valor_aprobado"]) == D("2000000")
    assert D(r["valor_facturado"]) == D("1500000")
    assert D(r["valor_pagado"]) == D("400000")
    assert D(r["saldo_pendiente_recaudo"]) == D("1100000")
    assert D(r["valor_aprobado_sin_facturar"]) == D("500000")


def test_factura_anulada_no_cuenta_en_el_resumen(client):
    corte_aprobado(client)
    client.post("/facturas", json=factura())
    client.delete("/facturas/1")