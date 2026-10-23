from datetime import date
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel

from app.models.enums import EstadoCorte


class CorteObraDB(SQLModel, table=True):
    __tablename__ = "corte_obra"

    id: Optional[int] = Field(default=None, primary_key=True)
    contrato_id: int = Field(foreign_key="contrato_obra.id", index=True)
    numero_corte: int
    fecha_corte: date
    periodo_inicio: date
    periodo_fin: date
    estado: EstadoCorte = EstadoCorte.BORRADOR
    observaciones: Optional[str] = Field(default=None, max_length=500)
    activo: bool = True


class DetalleCorteObraDB(SQLModel, table=True):
    __tablename__ = "detalle_corte_obra"

    id: Optional[int] = Field(default=None, primary_key=True)
    corte_id: int = Field(foreign_key="corte_obra.id", index=True)
    actividad_id: int = Field(foreign_key="actividad_obra.id", index=True)
    cantidad: Decimal = Field(max_digits=14, decimal_places=3)
    precio_unitario: Decimal = Field(max_digits=16, decimal_places=2)
