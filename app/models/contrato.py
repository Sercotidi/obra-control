from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.models.enums import EstadoContrato

class ContratoObra(BaseModel):
    id: Optional[int] = Field(default=None, ge=1)
    numero_contrato: str = Field(min_length=1, max_length=30)
    nombre_obra: str = Field(min_length=3, max_length=80)
    empresa_cliente: str = Field(min_length=2, max_length=100)
    nombre_contratista: str = Field(min_length=2, max_length=100)
    fecha_inicio: date
    fecha_fin: date
    valor_contrato: Decimal = Field(gt=0, max_digits=16, decimal_places=2)
    estado: EstadoContrato = EstadoContrato.BORRADOR
    activo: bool = True  # borrado lógico: False = inactivo (histórico)

    @model_validator(mode="after")
    def _fechas_coherentes(self):
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("fecha de el fin del contrato no puede ser anterior a la fecha de inicio")
        return self