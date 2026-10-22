from decimal import Decimal
from typing import Optional

 from pydantic import BaseModel, Field, model_validator

 class ActividadObra (BaseModel):
    id: Optional[int]
    contrato_id: int
    nombre_actividad: str
    unidad_medida: str
    cantidad_contratada: Decimal
    cantidad_ejecutada: Decimal
    observaciones: Optional[str]
