from sqlmodel import SQLModel, create_engine
import os

if os.environ.get("DB_URL") is None:
    raise Exception('DB_URL is empty!')

engine = create_engine(os.environ.get("DB_URL"))

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)