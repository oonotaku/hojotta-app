# create_tables.py
from app.models import SQLModel
from app.database import engine

print("🛠️ Creating all tables in the DB...")
SQLModel.metadata.create_all(engine)
print("✅ Done!")
