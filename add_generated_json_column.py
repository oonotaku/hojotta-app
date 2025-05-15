import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE fmtupload ADD COLUMN generated_json TEXT")
    print("✅ generated_json カラムを追加しました。")
except Exception as e:
    print("⚠️ すでに追加済みか、エラーがあります：", e)

conn.commit()
conn.close()
