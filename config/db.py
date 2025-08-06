from sqlmodel import SQLModel, create_engine, Session
from contextlib import  contextmanager
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# To create the SQLModel compatible engine
engine = create_engine(DATABASE_URL, echo=True)

# # To create tables
# def create_db_and_tables():
#     SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session