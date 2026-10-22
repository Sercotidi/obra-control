from sqlmodel import SQLModel, create_engine , Session

database_name = "control.db"
database_url = f"sqlite:///{database_name}"

engine = create_engine(database_url)

def create_db_tables()
    SQLModel.metadata.create_all(engine)

def get_session()
    with session(engine) as session:
        yield session
        