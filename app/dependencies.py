import os
from pathlib import Path

from app.models import ActividadObra, ContratoObra, CorteObra, DetalleCorteObra
from app.repositories.csv_repository import CsvRepository
from app.services.obra_service import ObraService

DATA_DIR = Path(os.getenv("OBRA_DATA_DIR", "data"))


def repo_contratos() -> CsvRepository:
    return CsvRepository(DATA_DIR / "contratos.csv", ContratoObra)


def repo_actividades() -> CsvRepository:
    return CsvRepository(DATA_DIR / "actividades.csv", ActividadObra)


def repo_cortes() -> CsvRepository:
    return CsvRepository(DATA_DIR / "cortes.csv", CorteObra)


def repo_detalles() -> CsvRepository:
    return CsvRepository(DATA_DIR / "detalles_corte.csv", DetalleCorteObra)


def servicio_obra() -> ObraService:
    return ObraService(repo_contratos(), repo_actividades(), repo_cortes(), repo_detalles())
