from enum import Enum


class EstadoContrato(str, Enum):
    BORRADOR = "borrador"
    ACTIVO = "activo"
    SUSPENDIDO = "suspendido"
    TERMINADO = "terminado"
    CANCELADO = "cancelado"


class EstadoCorte(str, Enum):
    BORRADOR = "borrador"
    PRESENTADO = "presentado"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"