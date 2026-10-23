from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel


class ActividadObraDB(SQLModel, table=True):
    __tablename__ = "actividad_obra"

    id: Optional[int] = Field(default=None, primary_key=True)
    contrato_id: int = Field(ge=1)
    nombre_actividad: str = Field(min_length=2, max_length=100)
    unidad_medida: str = Field(min_length=1, max_length=20)
    cantidad_contratada: Decimal = Field(gt=0, max_digits=14, decimal_places=3)
    precio_unitario: Decimal = Field(gt=0, max_digits=16, decimal_places=2)
    cantidad_ejecutada: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=3)
    observaciones: Optional[str] = Field(default=None, max_length=500)
    activo: bool = True
