import csv
import os
import tempfile
import threading
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ValidationError

from app.repositories.errors import DatosCorruptos, RegistroNoEncontrado

T = TypeVar("T", bound=BaseModel)


def _a_texto(valor) -> str:
    if valor is None:
        return ""
    if isinstance(valor, Enum):
        return str(valor.value)
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    if isinstance(valor, Decimal):
        return format(valor, "f")
    return str(valor)


class CsvRepository(Generic[T]):
    """CRUD genérico sobre un CSV. Escritura atómica (archivo temporal + os.replace)."""

    def __init__(self, ruta, modelo: type[T]):
        self.ruta = Path(ruta)
        self.modelo = modelo
        self.campos = list(modelo.model_fields.keys())
        self._lock = threading.RLock()
        self._inicializar()

    # --- infraestructura ---
    def _inicializar(self) -> None:
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        if not self.ruta.exists():
            self._escribir([])

    def _leer(self) -> list[T]:
        try:
            with open(self.ruta, newline="", encoding="utf-8") as f:
                lector = csv.DictReader(f)
                if lector.fieldnames != self.campos:
                    raise DatosCorruptos(
                        f"Encabezados inválidos en {self.ruta.name}: {lector.fieldnames} != {self.campos}")
                registros = []
                for n, fila in enumerate(lector, start=2):
                    datos = {k: (v if v != "" else None) for k, v in fila.items()}
                    try:
                        registros.append(self.modelo.model_validate(datos))
                    except ValidationError as e:
                        raise DatosCorruptos(f"Fila {n} inválida en {self.ruta.name}: {e}") from e
                return registros
        except FileNotFoundError:
            self._escribir([])
            return []

    def _escribir(self, registros: list[T]) -> None:
        fd, tmp = tempfile.mkstemp(dir=self.ruta.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
                escritor = csv.DictWriter(f, fieldnames=self.campos)
                escritor.writeheader()
                for r in registros:
                    escritor.writerow({c: _a_texto(getattr(r, c)) for c in self.campos})
            os.replace(tmp, self.ruta)
        except Exception:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise

    # --- CRUD ---
    def listar(self) -> list[T]:
        with self._lock:
            return self._leer()

    def obtener(self, id_: int) -> T:
        for r in self.listar():
            if r.id == id_:
                return r
        raise RegistroNoEncontrado(f"{self.modelo.__name__} {id_} no existe")

    def crear(self, obj: T) -> T:
        with self._lock:
            registros = self._leer()
            nuevo_id = max((r.id for r in registros), default=0) + 1
            nuevo = obj.model_copy(update={"id": nuevo_id})
            registros.append(nuevo)
            self._escribir(registros)
            return nuevo

    def actualizar(self, id_: int, obj: T) -> T:
        with self._lock:
            registros = self._leer()
            for i, r in enumerate(registros):
                if r.id == id_:
                    registros[i] = obj.model_copy(update={"id": id_})
                    self._escribir(registros)
                    return registros[i]
            raise RegistroNoEncontrado(f"{self.modelo.__name__} {id_} no existe")

    def eliminar(self, id_: int) -> None:
        with self._lock:
            registros = self._leer()
            restantes = [r for r in registros if r.id != id_]
            if len(restantes) == len(registros):
                raise RegistroNoEncontrado(f"{self.modelo.__name__} {id_} no existe")
            self._escribir(restantes)