# app/routes_auth.py
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlmodel import Session, select
from app.models import User, Upload
from app.database import get_session
from app.auth import hash_password, verify_password
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/signup", response_class=HTMLResponse)
async def signup_form(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@router.post("/signup", response_class=HTMLResponse)
async def signup(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session)
):
    user_exists = session.exec(select(User).where(User.username == username)).first()
    if user_exists:
        return templates.TemplateResponse("signup.html", {"request": request, "error": "ユーザー名は既に存在します"})

    hashed_pw = hash_password(password)
    user = User(username=username, password_hash=hashed_pw)
    session.add(user)
    session.commit()
    session.refresh(user)
    request.session["user"] = {"id": user.id, "username": user.username, "is_admin": user.is_admin}
    return RedirectResponse(url="/mypage", status_code=302)

@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session)
):
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("login.html", {"request": request, "error": "ログイン失敗しました"})

    request.session["user"] = {"id": user.id, "username": user.username, "is_admin": user.is_admin}
    return RedirectResponse(url="/mypage", status_code=302)

@router.get("/mypage", response_class=HTMLResponse)
async def mypage(request: Request, session: Session = Depends(get_session)):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login")

    uploads = session.exec(
        select(Upload).where(Upload.user_id == user["id"])
    ).all()

    return templates.TemplateResponse("mypage.html", {
        "request": request,
        "username": user["username"],
        "uploads": uploads
    })

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login")
