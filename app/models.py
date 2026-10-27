from datetime import date
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class EstadoCorte(str, Enum):
    presentado = "presentado"
    aprobado = "aprobado"
    rechazado = "rechazado"



class ContratoBase(SQLModel):
    """Campos que escribe el usuario (con sus validaciones)."""
    numero_contrato: str = Field(min_length=1, max_length=30)
    nombre_obra: str = Field(min_length=3, max_length=80)
    empresa_cliente: str = Field(min_length=2, max_length=80)
    nombre_contratista: str = Field(min_length=2, max_length=80)
    fecha_inicio: date
    fecha_fin: date
    valor_contrato: int = Field(gt=0)  # en pesos COP
    activo: bool = True


class Contrato(ContratoBase, table=True):
    """La tabla: los mismos campos + el id que genera la base de datos."""
    id: Optional[int] = Field(default=None, primary_key=True)



class ActividadBase(SQLModel):
    contrato_id: int = Field(foreign_key="contrato.id")
    nombre_actividad: str = Field(min_length=2, max_length=80)
    unidad_medida: str = Field(min_length=1, max_length=20)
    cantidad_contratada: float = Field(gt=0)
    precio_unitario: int = Field(gt=0)  # en pesos COP
    cantidad_ejecutada: float = Field(default=0, ge=0)
    activo: bool = True


class Actividad(ActividadBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)



class CorteBase(SQLModel):
    contrato_id: int = Field(foreign_key="contrato.id")
    numero_corte: int = Field(ge=1)
    fecha_corte: date
    valor_bruto: int = Field(gt=0)  # en pesos COP
    estado: EstadoCorte = EstadoCorte.presentado
    observaciones: Optional[str] = Field(default=None, max_length=300)
    activo: bool = True


class Corte(CorteBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
