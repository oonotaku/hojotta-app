from app.database import get_session
from app.models import User
from app.auth import hash_password

session = get_session()
admin_user = User(
    username="admin",
    password_hash=hash_password("adminpass"),
    is_admin=True
)
session.add(admin_user)
session.commit()
session.close()
print("✅ 管理者ユーザー作成完了！")
