from app.models import (ActividadObra, ContratoObra, CorteObra, DetalleCorteObra,
                        FacturaObra, PagoObra)
from app.models.actividad_db import ActividadObraDB
from app.models.contrato_db import ContratoObraDB
from app.models.corte_db import CorteObraDB, DetalleCorteObraDB
from app.models.factura_db import FacturaObraDB, PagoObraDB
from app.repositories.sql_repository import SqlRepository
from app.services.obra_service import ObraService
from data.db.control_de_obra import engine

ENGINE = engine  # SQLite (control.db). Las pruebas lo reemplazan por una base temporal.


def repo_contratos() -> SqlRepository:
    return SqlRepository(ENGINE, ContratoObraDB, ContratoObra)


def repo_actividades() -> SqlRepository:
    return SqlRepository(ENGINE, ActividadObraDB, ActividadObra)


def repo_cortes() -> SqlRepository:
    return SqlRepository(ENGINE, CorteObraDB, CorteObra)


def repo_detalles() -> SqlRepository:
    return SqlRepository(ENGINE, DetalleCorteObraDB, DetalleCorteObra)


def repo_facturas() -> SqlRepository:
    return SqlRepository(ENGINE, FacturaObraDB, FacturaObra)


def repo_pagos() -> SqlRepository:
    return SqlRepository(ENGINE, PagoObraDB, PagoObra)


def servicio_obra() -> ObraService:
    return ObraService(repo_contratos(), repo_actividades(), repo_cortes(), repo_detalles(),
                       repo_facturas(), repo_pagos())
