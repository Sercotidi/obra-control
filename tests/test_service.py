from datetime import date
from decimal import Decimal as D

import pytest
from sqlmodel import create_engine

from app.models import ActividadObra, ContratoObra, CorteObra, EstadoCorte
from app import dependencies
from app.errors import ReglaNegocioError


@pytest.fixture
def svc(tmp_path, monkeypatch):
    monkeypatch.setattr(dependencies, "ENGINE", create_engine(f"sqlite:///{tmp_path / 'svc.db'}"))
    s = dependencies.servicio_obra()
    s.contratos.crear(ContratoObra(numero_contrato="C-1", nombre_obra="Campus", empresa_cliente="Cliente",
                                   nombre_contratista="Muros", fecha_inicio=date(2026, 1, 1),
                                   fecha_fin=date(2026, 12, 31), valor_contrato=D("5000000")))
    s.crear_actividad(ActividadObra(contrato_id=1, nombre_actividad="Muro", unidad_medida="und",
                                    cantidad_contratada=D("5"), precio_unitario=D("1000000")))
    return s


def corte(n=1, estado=EstadoCorte.BORRADOR):
    return CorteObra(contrato_id=1, numero_corte=n, fecha_corte=date(2026, 3, 1),
                     periodo_inicio=date(2026, 2, 1), periodo_fin=date(2026, 2, 28), estado=estado)


def test_ejemplo_del_enunciado(svc):
    svc.registrar_avance(1, D("2"))
    c = svc.crear_corte(corte(1), [(1, D("2"))])
    svc.cambiar_estado_corte(c.id, EstadoCorte.PRESENTADO)
    svc.cambiar_estado_corte(c.id, EstadoCorte.APROBADO)
    svc.registrar_avance(1, D("3"))  # un muro más ejecutado, aún sin cortar
    r = svc.resumen_contrato(1)
    assert r["valor_contratado"] == D("5000000")
    assert r["valor_ejecutado"] == D("3000000")
    assert r["valor_en_cortes_activos"] == D("2000000")
    assert r["valor_aprobado"] == D("2000000")
    assert r["valor_disponible_para_cobrar"] == D("1000000")
    assert r["valor_pendiente_ejecutar"] == D("2000000")


def test_no_duplica_cantidades(svc):
    svc.registrar_avance(1, D("2"))
    svc.crear_corte(corte(1), [(1, D("2"))])
    with pytest.raises(ReglaNegocioError):
        svc.crear_corte(corte(2), [(1, D("1"))])


def test_no_cobra_mas_de_lo_ejecutado(svc):
    svc.registrar_avance(1, D("1"))
    with pytest.raises(ReglaNegocioError):
        svc.crear_corte(corte(1), [(1, D("2"))])
    assert svc.cortes.listar() == []  # no dejó basura


def test_rechazado_libera_cantidad_y_no_cuenta_como_cobrado(svc):
    svc.registrar_avance(1, D("2"))
    c = svc.crear_corte(corte(1), [(1, D("2"))])
    svc.cambiar_estado_corte(c.id, EstadoCorte.PRESENTADO)
    svc.cambiar_estado_corte(c.id, EstadoCorte.RECHAZADO)
    q = svc.cantidades_actividad(1)
    assert q["aprobada"] == 0 and q["en_cortes_activos"] == 0 and q["disponible_para_cobrar"] == 2
    svc.crear_corte(corte(2), [(1, D("2"))])  # se puede volver a cobrar


def test_transiciones_invalidas(svc):
    svc.registrar_avance(1, D("1"))
    c = svc.crear_corte(corte(1), [(1, D("1"))])
    with pytest.raises(ReglaNegocioError):
        svc.cambiar_estado_corte(c.id, EstadoCorte.APROBADO)  # borrador -> aprobado
    svc.cambiar_estado_corte(c.id, EstadoCorte.PRESENTADO)
    svc.cambiar_estado_corte(c.id, EstadoCorte.RECHAZADO)
    with pytest.raises(ReglaNegocioError):
        svc.cambiar_estado_corte(c.id, EstadoCorte.APROBADO)  # rechazado es final


def test_valor_corte_usa_precio_congelado(svc):
    svc.registrar_avance(1, D("2"))
    c = svc.crear_corte(corte(1), [(1, D("2"))])
    act = svc.actividades.obtener(1)
    svc.actividades.actualizar(1, act.model_copy(update={"precio_unitario": D("9999999")}))
    assert svc.valor_corte(c.id) == D("2000000")


def test_no_bajar_avance_por_debajo_de_lo_cortado(svc):
    svc.registrar_avance(1, D("3"))
    svc.crear_corte(corte(1), [(1, D("3"))])
    with pytest.raises(ReglaNegocioError):
        svc.registrar_avance(1, D("2"))


def test_avance_mayor_que_contratado(svc):
    with pytest.raises(ReglaNegocioError):
        svc.registrar_avance(1, D("6"))


def test_actividades_no_superan_valor_contrato(svc):
    with pytest.raises(ReglaNegocioError):
        svc.crear_actividad(ActividadObra(contrato_id=1, nombre_actividad="Piso", unidad_medida="m2",
                                          cantidad_contratada=D("1"), precio_unitario=D("1")))


def test_validaciones_de_creacion_de_corte(svc):
    svc.registrar_avance(1, D("2"))
    with pytest.raises(ReglaNegocioError):
        svc.crear_corte(corte(1), [])
    with pytest.raises(ReglaNegocioError):
        svc.crear_corte(corte(1), [(1, D("1")), (1, D("1"))])
    with pytest.raises(ReglaNegocioError):
        svc.crear_corte(corte(1), [(1, D("0"))])
    svc.crear_corte(corte(1), [(1, D("1"))])
    with pytest.raises(ReglaNegocioError):  # numero_corte repetido
        svc.crear_corte(corte(1), [(1, D("1"))])


def test_actividad_de_otro_contrato(svc):
    svc.contratos.crear(ContratoObra(numero_contrato="C-2", nombre_obra="Otra", empresa_cliente="Cliente",
                                     nombre_contratista="Otro", fecha_inicio=date(2026, 1, 1),
                                     fecha_fin=date(2026, 12, 31), valor_contrato=D("100")))
    svc.crear_actividad(ActividadObra(contrato_id=2, nombre_actividad="Estuco", unidad_medida="und",
                                      cantidad_contratada=D("1"), precio_unitario=D("100")))
    svc.registrar_avance(2, D("1"))
    with pytest.raises(ReglaNegocioError):
        svc.crear_corte(corte(1), [(2, D("1"))])


def test_eliminar_solo_borrador(svc):
    svc.registrar_avance(1, D("2"))
    c = svc.crear_corte(corte(1), [(1, D("2"))])
    svc.eliminar_corte(c.id)
    assert svc.cortes.obtener(c.id).activo is False  # histórico
    assert svc.cantidades_actividad(1)["disponible_para_cobrar"] == 2
    c2 = svc.crear_corte(corte(2), [(1, D("1"))])
    svc.cambiar_estado_corte(c2.id, EstadoCorte.PRESENTADO)