from passlib.context import CryptContext
from fastapi import Request, HTTPException

# パスワードのハッシュ化設定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ハッシュ化
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# 照合
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

from fastapi import Request, HTTPException

def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="未ログインです")
    return user


# 管理者専用のアクセス制限
def admin_only(request: Request):
    user = request.session.get("user")
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="管理者権限が必要です")
    return user
