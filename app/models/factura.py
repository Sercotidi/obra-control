from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class FacturaObra(BaseModel):
    """Factura emitida por el contratista sobre un corte APROBADO (un corte no es una factura)."""

    id: Optional[int] = Field(default=None, ge=1)
    contrato_id: int = Field(ge=1)
    corte_id: int = Field(ge=1)
    numero_factura: str = Field(min_length=1, max_length=30)
    fecha_factura: date
    valor: Decimal = Field(gt=0, max_digits=16, decimal_places=2)
    observaciones: Optional[str] = Field(default=None, max_length=500)
    activo: bool = True


class PagoObra(BaseModel):
    """Dinero efectivamente recibido por una factura (una factura no es un pago)."""

    id: Optional[int] = Field(default=None, ge=1)
    factura_id: int = Field(ge=1)
    fecha_pago: date
    valor: Decimal = Field(gt=0, max_digits=16, decimal_places=2)
    observaciones: Optional[str] = Field(default=None, max_length=500)
    activo: bool = True