import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS fmtupload (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    upload_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    uploaded_at TEXT NOT NULL,
    section TEXT,
    has_generated BOOLEAN DEFAULT 0,
    FOREIGN KEY(upload_id) REFERENCES upload(id)
)
""")

print("✅ fmtupload テーブルを作成しました。")
conn.commit()
conn.close()
