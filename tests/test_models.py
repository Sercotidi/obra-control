from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models import (ActividadObra, ContratoObra, CorteObra,
                        DetalleCorteObra, EstadoContrato, EstadoCorte)


def contrato(**kw):
    base = dict(numero_contrato="C-001", nombre_obra="Campus FUCS", empresa_cliente="Serviconstrucciones FI S.A.S.",
                nombre_contratista="Muros Ltda", fecha_inicio=date(2026, 1, 1),
                fecha_fin=date(2026, 12, 31), valor_contrato=Decimal("5000000"))
    base.update(kw)
    return ContratoObra(**base)


def actividad(**kw):
    base = dict(contrato_id=1, nombre_actividad="Muro", unidad_medida="und",
                cantidad_contratada=Decimal("5"), precio_unitario=Decimal("1000000"))
    base.update(kw)
    return ActividadObra(**base)


def corte(**kw):
    base = dict(contrato_id=1, numero_corte=1, fecha_corte=date(2026, 2, 1),
                periodo_inicio=date(2026, 1, 1), periodo_fin=date(2026, 1, 31))
    base.update(kw)
    return CorteObra(**base)


def test_contrato_valido_estado_por_defecto():
    c = contrato()
    assert c.estado == EstadoContrato.BORRADOR and c.id is None


def test_contrato_fechas_invalidas():
    with pytest.raises(ValidationError):
        contrato(fecha_fin=date(2025, 1, 1))


@pytest.mark.parametrize("v", ["0", "-5"])
def test_contrato_valor_no_positivo(v):
    with pytest.raises(ValidationError):
        contrato(valor_contrato=Decimal(v))


def test_contrato_estado_invalido():
    with pytest.raises(ValidationError):
        contrato(estado="inventado")


def test_actividad_valores_calculados():
    a = actividad(cantidad_ejecutada=Decimal("3"))
    assert a.valor_contratado == Decimal("5000000")
    assert a.valor_ejecutado == Decimal("3000000")


def test_actividad_ejecutada_excede_contratada():
    with pytest.raises(ValidationError):
        actividad(cantidad_ejecutada=Decimal("6"))


def test_actividad_cantidad_cero():
    with pytest.raises(ValidationError):
        actividad(cantidad_contratada=Decimal("0"))


def test_corte_valido_y_estado_enum():
    assert corte(estado="aprobado").estado == EstadoCorte.APROBADO


def test_corte_periodo_invertido():
    with pytest.raises(ValidationError):
        corte(periodo_fin=date(2025, 12, 1))


def test_corte_fecha_antes_del_periodo():
    with pytest.raises(ValidationError):
        corte(fecha_corte=date(2026, 1, 15))


def test_detalle_valor_y_cantidad_positiva():
    d = DetalleCorteObra(corte_id=1, actividad_id=1, cantidad=Decimal("2"), precio_unitario=Decimal("1000000"))
    assert d.valor == Decimal("2000000")
    with pytest.raises(ValidationError):