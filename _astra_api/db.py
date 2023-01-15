from sqlmodel import SQLModel, create_engine

from _astra_api.settings import cfg

engine = create_engine(cfg.db.database_uri)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)