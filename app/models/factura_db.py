"""Tablas SQL de FacturaObra y PagoObra (SQLModel)."""
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel


class FacturaObraDB(SQLModel, table=True):
    __tablename__ = "factura_obra"

    id: Optional[int] = Field(default=None, primary_key=True)
    contrato_id: int = Field(foreign_key="contrato_obra.id", index=True)
    corte_id: int = Field(foreign_key="corte_obra.id", index=True)
    numero_factura: str = Field(max_length=30, index=True)
    fecha_factura: date
    valor: Decimal = Field(max_digits=16, decimal_places=2)
    observaciones: Optional[str] = Field(default=None, max_length=500)
    activo: bool = True


class PagoObraDB(SQLModel, table=True):
    __tablename__ = "pago_obra"

    id: Optional[int] = Field(default=None, primary_key=True)
    factura_id: int = Field(foreign_key="factura_obra.id", index=True)
    fecha_pago: date
    valor: Decimal = Field(max_digits=16, decimal_places=2)
    observaciones: Optional[str] = Field(default=None, max_length=500)
    activo: bool = True
