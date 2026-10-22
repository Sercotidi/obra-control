from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.models.enums import EstadoCorte


class CorteObra(BaseModel):
    id: Optional[int] = Field(default=None, ge=1)
    contrato_id: int = Field(ge=1)
    numero_corte: int = Field(ge=1)
    fecha_corte: date
    periodo_inicio: date
    periodo_fin: date
    estado: EstadoCorte = EstadoCorte.BORRADOR
    observaciones: Optional[str] = Field(default=None, max_length=500)
    activo: bool = True  # borrado lógico: False = inactivo (histórico)

    @model_validator(mode="after")
    def _periodo_coherente(self):
        if self.periodo_fin < self.periodo_inicio:
            raise ValueError("el periodo de fin no puede ser anterior al periodo de inicio")
        if self.fecha_corte < self.periodo_fin:
            raise ValueError("la fecha del corte no puede ser anterior a el periodo de fin")
        return self


class DetalleCorteObra(BaseModel):
    id: Optional[int] = Field(default=None, ge=1)
    corte_id: int = Field(ge=1)
    actividad_id: int = Field(ge=1)
    cantidad: Decimal = Field(gt=0, max_digits=14, decimal_places=3)
    precio_unitario: Decimal = Field(gt=0, max_digits=16, decimal_places=2)

    @property
    def valor(self) -> Decimal:
        return self.cantidad * self.precio_unitario
