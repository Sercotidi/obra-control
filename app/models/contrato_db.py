from datetime import date
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel

from app.models.enums import EstadoContrato


class ContratoObraDB(SQLModel, table=True):
    __tablename__ = "contrato_obra"

    id: Optional[int] = Field(default=None, primary_key=True)
    numero_contrato: str = Field(max_length=30, index=True)
    nombre_obra: str = Field(max_length=80)
    empresa_cliente: str = Field(max_length=100)
    nombre_contratista: str = Field(max_length=100)
    fecha_inicio: date
    fecha_fin: date
    valor_contrato: Decimal = Field(max_digits=16, decimal_places=2)
    estado: EstadoContrato = EstadoContrato.BORRADOR
    activo: bool = True
