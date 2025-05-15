# create_admin.py（プロジェクト直下に保存）
from sqlmodel import Session, create_engine
from app.models import User
from app.auth import hash_password

engine = create_engine("sqlite:///database.db")

def create_admin():
    admin_user = User(
        username="admin",
        password_hash=hash_password("adminpass"),
        is_admin=True
    )
    with Session(engine) as session:
        session.add(admin_user)
        session.commit()
        print("✅ 管理者(admin) を作成しました。")

if __name__ == "__main__":
    create_admin()
