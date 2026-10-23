"""Modelos de entrada o salida de la API (no se guardan tal cual en el CSV)."""
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models import CorteObra, DetalleCorteObra


class DetalleEntrada(BaseModel):
    actividad_id: int = Field(ge=1)
    cantidad: Decimal = Field(gt=0, max_digits=14, decimal_places=3)


class CorteCrear(CorteObra):
    detalles: list[DetalleEntrada] = Field(min_length=1)


class CorteDetallado(CorteObra):
    detalles: list[DetalleCorteObra]
    valor_total: Decimal


class AvanceEntrada(BaseModel):
    cantidad_ejecutada: Decimal = Field(ge=0, max_digits=14, decimal_places=3)


class CantidadesActividad(BaseModel):
    contratada: Decimal
    ejecutada: Decimal
    en_cortes_activos: Decimal
    aprobada: Decimal
    disponible_para_cobrar: Decimal
    pendiente_ejecutar: Decimal


class ResumenContrato(BaseModel):
    valor_contratado: Decimal
    valor_ejecutado: Decimal
    valor_en_cortes_activos: Decimal
    valor_aprobado: Decimal
    valor_disponible_para_cobrar: Decimal
    valor_pendiente_ejecutar: Decimal
