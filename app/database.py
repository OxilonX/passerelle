from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

sqlite_file_name = "stages.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})


@event.listens_for(engine, "connect")
def _fk_on(dbapi_conn, _):
    dbapi_conn.execute("PRAGMA foreign_keys=ON")


import app.models  


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)