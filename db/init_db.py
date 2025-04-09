# db/init_db.py
from sqlmodel import SQLModel
from app.models import User, ConversationLog
from app.database import engine

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    create_db_and_tables()
