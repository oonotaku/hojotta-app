import sqlite3

conn = sqlite3.connect("database.db")  # 必要に応じてパス修正
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE fmtupload ADD COLUMN fmt_type TEXT DEFAULT 'monozukuri'")
    print("✅ fmt_type カラムを追加しました。")
except Exception as e:
    print("⚠️ すでに追加済みか、エラーがあります：", e)

conn.commit()
conn.close()
