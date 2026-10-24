from typing import Generic, TypeVar

from pydantic import BaseModel
from sqlmodel import Session, SQLModel, select

# Importar las tablas para que SQLModel las registre antes de create_all
from app.models.actividad_db import ActividadObraDB  # noqa: F401
from app.models.contrato_db import ContratoObraDB  # noqa: F401
from app.models.corte_db import CorteObraDB, DetalleCorteObraDB  # noqa: F401
from app.models.factura_db import FacturaObraDB, PagoObraDB  # noqa: F401
from app.repositories.errors import RegistroNoEncontrado

T = TypeVar("T", bound=BaseModel)


class SqlRepository(Generic[T]):
    """CRUD genérico sobre SQLite con SQLModel. Misma interfaz que CsvRepository."""

    def __init__(self, engine, tabla, modelo: type[T]):
        self.engine = engine
        self.tabla = tabla
        self.modelo = modelo
        SQLModel.metadata.create_all(engine)

    def _a_modelo(self, fila) -> T:
        return self.modelo(**fila.model_dump())

    def listar(self) -> list[T]:
        with Session(self.engine) as s:
            return [self._a_modelo(f) for f in s.exec(select(self.tabla).order_by(self.tabla.id)).all()]

    def obtener(self, id_: int) -> T:
        with Session(self.engine) as s:
            fila = s.get(self.tabla, id_)
            if fila is None:
                raise RegistroNoEncontrado(f"{self.modelo.__name__} {id_} no existe")
            return self._a_modelo(fila)

    def crear(self, obj: T) -> T:
        with Session(self.engine) as s:
            fila = self.tabla(**obj.model_dump(exclude={"id"}))
            s.add(fila)
            s.commit()
            s.refresh(fila)
            return self._a_modelo(fila)

    def actualizar(self, id_: int, obj: T) -> T:
        with Session(self.engine) as s:
            fila = s.get(self.tabla, id_)
            if fila is None:
                raise RegistroNoEncontrado(f"{self.modelo.__name__} {id_} no existe")
            for campo, valor in obj.model_dump(exclude={"id"}).items():
                setattr(fila, campo, valor)
            s.add(fila)
            s.commit()
            s.refresh(fila)
            return self._a_modelo(fila)

    def eliminar(self, id_: int) -> None:
        with Session(self.engine) as s:
            fila = s.get(self.tabla, id_)
            if fila is None:
                raise RegistroNoEncontrado(f"{self.modelo.__name__} {id_} no existe")
            s.delete(fila)
            s.commit()