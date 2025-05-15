from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from app.models import User
from app.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/profile", response_class=HTMLResponse)
async def profile_form(request: Request, db: Session = Depends(get_db)):
    session_user = request.session.get("user")
    if not session_user:
        return RedirectResponse("/login")

    user = db.get(User, session_user["id"])
    return templates.TemplateResponse("profile.html", {"request": request, "user": user})

@router.post("/profile", response_class=HTMLResponse)
async def profile_submit(
    request: Request,
    company_name: str = Form(...),
    industry: str = Form(...),
    location: str = Form(...),
    employee_count: str = Form(...),
    founded_date: str = Form(...),
    company_type: str = Form(...),
    tax_location: str = Form(...),
    capital: str = Form(...),
    has_gbizid: bool = Form(False),
    db: Session = Depends(get_db)
):
    session_user = request.session.get("user")
    if not session_user:
        return RedirectResponse("/login")

    user = db.get(User, session_user["id"])
    user.company_name = company_name
    user.industry = industry
    user.location = location
    user.employee_count = employee_count
    user.founded_date = founded_date
    user.company_type = company_type
    user.tax_location = tax_location
    user.capital = capital
    user.has_gbizid = has_gbizid

    db.add(user)
    db.commit()

    # セッションにも反映
    session_user.update({
        "company_name": company_name,
        "industry": industry,
        "location": location,
        "employee_count": employee_count,
        "founded_date": founded_date,
        "company_type": company_type,
        "tax_location": tax_location,
        "capital": capital,
        "has_gbizid": has_gbizid
    })
    request.session["user"] = session_user

    return RedirectResponse("/mypage", status_code=303)
