import sqlite3

conn = sqlite3.connect("database.db")  # 必要に応じてパス変更！
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE upload ADD COLUMN pitch_filename TEXT")
    print("✅ pitch_filename カラムを追加しました。")
except Exception as e:
    print("⚠️ すでに追加済みか、エラーがあります：", e)

conn.commit()
conn.close()
