from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import create_engine

from app.models import ContratoObra, EstadoContrato
from app.models.contrato_db import ContratoObraDB
from app.repositories.errors import RegistroNoEncontrado
from app.repositories.sql_repository import SqlRepository


@pytest.fixture
def repo(tmp_path):
    return SqlRepository(create_engine(f"sqlite:///{tmp_path / 'r.db'}"), ContratoObraDB, ContratoObra)


def nuevo(num="C-1"):
    return ContratoObra(numero_contrato=num, nombre_obra="Campus FUCS", empresa_cliente="Cliente",
                        nombre_contratista="Muros", fecha_inicio=date(2026, 1, 1),
                        fecha_fin=date(2026, 12, 31), valor_contrato=Decimal("5000000.50"))


def test_crear_y_obtener_conserva_tipos(repo):
    c = repo.crear(nuevo())
    leido = repo.obtener(c.id)
    assert c.id == 1 and leido.valor_contrato == Decimal("5000000.50")
    assert leido.fecha_inicio == date(2026, 1, 1) and leido.estado == EstadoContrato.BORRADOR


def test_actualizar_listar_eliminar(repo):
    c = repo.crear(nuevo())
    repo.actualizar(c.id, c.model_copy(update={"estado": EstadoContrato.ACTIVO}))
    assert repo.listar()[0].estado == EstadoContrato.ACTIVO
    repo.eliminar(c.id)
    assert repo.listar() == []


def test_id_inexistente(repo):
    for f in (lambda: repo.obtener(9), lambda: repo.eliminar(9), lambda: repo.actualizar(9, nuevo())):
        with pytest.raises(RegistroNoEncontrado):
            f()