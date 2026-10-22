from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class ActividadObra(BaseModel):
    id: Optional[int] = Field(default=None, ge=1)
    contrato_id: int = Field(ge=1)
    nombre_actividad: str = Field(min_length=2, max_length=100)
    unidad_medida: str = Field(min_length=1, max_length=20)
    cantidad_contratada: Decimal = Field(gt=0, max_digits=14, decimal_places=3)
    precio_unitario: Decimal = Field(gt=0, max_digits=16, decimal_places=2)
    cantidad_ejecutada: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=3)
    observaciones: Optional[str] = Field(default=None, max_length=500)
    activo: bool = True  # borrado lógico: False = inactivo (histórico)

    @model_validator(mode="after")
    def _ejecutada_no_excede(self):
        if self.cantidad_ejecutada > self.cantidad_contratada:
            raise ValueError("la cantidad ejecutada no puede superar la contratada")
        return self

    @property
    def valor_contratado(self) -> Decimal:
        return self.cantidad_contratada * self.precio_unitario

    @property
    def valor_ejecutado(self) -> Decimal:
        return self.cantidad_ejecutada * self.precio_unitario
