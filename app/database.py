# Conexión a la base de datos (SQLite). Todo se guarda en el archivo control.db
from fastapi import HTTPException
from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = "sqlite:///control.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def crear_tablas():
    """Crea las tablas en control.db si todavía no existen."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Entrega una sesión para hablar con la base. FastAPI la usa con Depends."""
    with Session(engine) as session:
        yield session


def obtener_o_404(session: Session, modelo, id_: int):
    """Busca un registro por ID. Si no existe, responde 404 sin que el servidor falle."""
    fila = session.get(modelo, id_)
    if fila is None:
        raise HTTPException(status_code=404, detail=f"{modelo.__name__} {id_} no existe")
    return fila