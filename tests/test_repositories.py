import csv
from datetime import date
from decimal import Decimal

import pytest

from app.models import ActividadObra, ContratoObra, CorteObra, EstadoContrato, EstadoCorte
from app.repositories.csv_repository import CsvRepository
from app.repositories.errors import DatosCorruptos, RegistroNoEncontrado


def nuevo_contrato(num="C-001"):
    return ContratoObra(numero_contrato=num, nombre_obra="Campus FUCS", empresa_cliente="Cliente SA",
                        nombre_contratista="Muros Ltda", fecha_inicio=date(2026, 1, 1),
                        fecha_fin=date(2026, 12, 31), valor_contrato=Decimal("5000000.50"))


@pytest.fixture
def repo(tmp_path):
    return CsvRepository(tmp_path / "contratos.csv", ContratoObra)


def test_crea_archivo_con_encabezados(tmp_path):
    ruta = tmp_path / "sub" / "c.csv"
    CsvRepository(ruta, ContratoObra)
    with open(ruta, newline="", encoding="utf-8") as f:
        assert next(csv.reader(f)) == list(ContratoObra.model_fields)


def test_ids_autoincrementales_y_no_se_reutilizan_el_maximo(repo):
    a, b = repo.crear(nuevo_contrato("A")), repo.crear(nuevo_contrato("B"))
    assert (a.id, b.id) == (1, 2)
    repo.eliminar(1)
    assert repo.crear(nuevo_contrato("C")).id == 3


def test_roundtrip_tipos(repo):
    c = repo.crear(nuevo_contrato())
    repo2 = CsvRepository(repo.ruta, ContratoObra)  # releer desde disco
    leido = repo2.obtener(c.id)
    assert leido == c
    assert leido.valor_contrato == Decimal("5000000.50")
    assert leido.fecha_inicio == date(2026, 1, 1)
    assert leido.estado == EstadoContrato.BORRADOR


def test_opcional_none_y_texto_con_comas_y_saltos(tmp_path):
    r = CsvRepository(tmp_path / "a.csv", ActividadObra)
    sin = r.crear(ActividadObra(contrato_id=1, nombre_actividad="Muro", unidad_medida="m2",
                                cantidad_contratada=Decimal("5.5"), precio_unitario=Decimal("100")))
    con = r.crear(ActividadObra(contrato_id=1, nombre_actividad='Piso, "pulido"', unidad_medida="m2",
                                cantidad_contratada=Decimal("1"), precio_unitario=Decimal("1"),
                                observaciones="línea1\nlínea2, con coma"))
    assert r.obtener(sin.id).observaciones is None
    assert r.obtener(con.id).observaciones == "línea1\nlínea2, con coma"
    assert r.obtener(con.id).nombre_actividad == 'Piso, "pulido"'


def test_actualizar_y_eliminar(repo):
    c = repo.crear(nuevo_contrato())
    mod = c.model_copy(update={"estado": EstadoContrato.ACTIVO})
    assert repo.actualizar(c.id, mod).estado == EstadoContrato.ACTIVO
    assert repo.obtener(c.id).estado == EstadoContrato.ACTIVO
    repo.eliminar(c.id)
    assert repo.listar() == []


def test_no_encontrado(repo):
    for f in (lambda: repo.obtener(9), lambda: repo.eliminar(9),
              lambda: repo.actualizar(9, nuevo_contrato())):
        with pytest.raises(RegistroNoEncontrado):
            f()


def test_encabezados_corruptos(tmp_path):
    ruta = tmp_path / "x.csv"
    ruta.write_text("id,otra\n1,2\n", encoding="utf-8")
    with pytest.raises(DatosCorruptos):
        CsvRepository(ruta, ContratoObra).listar()


def test_fila_invalida(tmp_path):
    ruta = tmp_path / "c.csv"
    r = CsvRepository(ruta, ContratoObra)
    r.crear(nuevo_contrato())
    ruta.write_text(ruta.read_text(encoding="utf-8").replace("5000000.50", "-1"), encoding="utf-8")
    with pytest.raises(DatosCorruptos):
        r.listar()


def test_archivo_borrado_se_recrea(repo):
    repo.crear(nuevo_contrato())
    repo.ruta.unlink()
    assert repo.listar() == []


def test_corte_enum_y_no_deja_temporales(tmp_path):
    r = CsvRepository(tmp_path / "cortes.csv", CorteObra)
    c = r.crear(CorteObra(contrato_id=1, numero_corte=1, fecha_corte=date(2026, 2, 1),
                          periodo_inicio=date(2026, 1, 1), periodo_fin=date(2026, 1, 31),
                          estado=EstadoCorte.RECHAZADO))