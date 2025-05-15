from sqlmodel import create_engine, Session
from contextlib import contextmanager

DATABASE_URL = "sqlite:///./database.db"

engine = create_engine(DATABASE_URL, echo=True)

# FastAPI の Depends で使えるように yield を使う
def get_db():
    with Session(engine) as session:
        yield session
