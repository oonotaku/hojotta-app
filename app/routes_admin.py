# app/routes_admin.py
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from app.models import User, ConversationLog
from app.database import get_session
from app.auth import verify_password
#from app.routes_auth import admin_only
from app.auth import admin_only 
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/admin/users", response_class=HTMLResponse)
async def admin_user_list(request: Request, user: dict = Depends(admin_only), session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return templates.TemplateResponse("admin_users.html", {"request": request, "users": users})

@router.get("/admin/user/{user_id}", response_class=HTMLResponse)
async def admin_user_detail(request: Request, user_id: int, user: dict = Depends(admin_only), session: Session = Depends(get_session)):
    target_user = session.get(User, user_id)
    if not target_user:
        return HTMLResponse(content="ユーザーが見つかりません", status_code=404)

    logs = session.exec(select(ConversationLog).where(ConversationLog.user_id == user_id)).all()
    return templates.TemplateResponse("admin_user_detail.html", {
        "request": request,
        "target_user": target_user,
        "logs": logs
    })
