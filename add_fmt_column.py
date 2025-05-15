import sqlite3

conn = sqlite3.connect("app/database.db")  # ← パスを実際のDBファイルに合わせて修正！
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE upload ADD COLUMN fmt_filename TEXT")
    print("fmt_filename カラムを追加しました。")
except Exception as e:
    print("すでにカラムが存在するか、エラーです:", e)

conn.commit()
conn.close()
