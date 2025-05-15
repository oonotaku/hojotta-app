import sqlite3

conn = sqlite3.connect("database.db")  # ← DBファイル名に合わせて変更が必要なら修正
cursor = conn.cursor()

columns = [
    ("company_name", "TEXT"),
    ("founded_date", "TEXT"),
    ("company_type", "TEXT"),
    ("tax_location", "TEXT"),
    ("capital", "TEXT"),
    ("has_gbizid", "BOOLEAN")
]

for column_name, column_type in columns:
    try:
        cursor.execute(f"ALTER TABLE user ADD COLUMN {column_name} {column_type}")
        print(f"✅ {column_name} カラムを追加しました。")
    except Exception as e:
        print(f"⚠️ {column_name} は既に存在するかエラーがあります: {e}")

conn.commit()
conn.close()
