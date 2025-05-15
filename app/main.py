from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlmodel import Session, select
import json

from app.database import get_db
from app.models import User, Upload

from app.routes_auth import router as auth_router
from app.routes_admin import router as admin_router
from app.routes_upload import router as upload_router
from app.routes_profile import router as profile_router
from app.routes_writing import router as writing_router

app = FastAPI()

# ルーターの読み込み
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(upload_router)
app.include_router(profile_router)
app.include_router(writing_router)

# ミドルウェア設定
app.add_middleware(SessionMiddleware, secret_key="super-secret-key")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# テンプレート設定
templates = Jinja2Templates(directory="app/templates")
templates.env.auto_reload = True
templates.env.cache = {}

# 静的ファイル設定
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# トップページ
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("index.html", {"request": request})

# マイページ
@app.get("/mypage", response_class=HTMLResponse)
async def mypage(request: Request, db: Session = Depends(get_db)):
    user_session = request.session.get("user")
    if not user_session:
        return RedirectResponse(url="/login")

    user = db.get(User, user_session["id"])

    # 🔁 JSON文字列 → 辞書に変換
    raw_profile = json.loads(user.profile_info) if user.profile_info else {}

    # ✅ プロフィールキーを日本語に変換
    keymap = {
        "industry": "業種",
        "location": "所在地",
        "employees": "従業員数",
        "established_year": "設立年",
        "capital": "資本金",
        "gbiz_id": "GビズID",
        "invoice_registered": "インボイス登録"
    }
    profile = {keymap.get(k, k): v for k, v in raw_profile.items()}

    # ✅ 必須項目がすべて揃っているか
    required_keys = ["業種", "所在地", "従業員数", "設立年", "資本金", "GビズID", "インボイス登録"]
    profile_complete = all(profile.get(k) for k in required_keys)

    # アップロード情報
    uploads = db.exec(
        select(Upload).where(Upload.user_id == user.id, Upload.is_active == True)
    ).all()

    return templates.TemplateResponse("mypage.html", {
        "request": request,
        "username": user.username,
        "uploads": uploads,
        "profile_complete": profile_complete
    })
