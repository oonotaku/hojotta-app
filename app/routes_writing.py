from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.models import Writing
from app.database import get_db
from app.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/writing/{writing_id}")
def writing_detail(
    request: Request,
    writing_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    writing = db.query(Writing).filter(Writing.id == writing_id, Writing.user_id == user["id"]).first()
    if not writing:
        raise HTTPException(status_code=404, detail="作文が見つかりません")

    return templates.TemplateResponse("writing_detail.html", {
        "request": request,
        "writing": writing
    })
