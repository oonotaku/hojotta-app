# app/routes_profile.py
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select
from app.models import User, Upload
from app.database import get_session
from app.auth import get_current_user
from fastapi.templating import Jinja2Templates
from openai import OpenAI
from app.config import OPENAI_API_KEY
import json
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/profile", response_class=HTMLResponse)
async def profile_form(request: Request, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    current_user = session.get(User, user["id"])
    profile_data = json.loads(current_user.profile_info) if current_user.profile_info else {}
    return templates.TemplateResponse("profile.html", {"request": request, "profile": profile_data})

@router.post("/profile", response_class=HTMLResponse)
async def save_profile(
    request: Request,
    industry: str = Form(...),
    location: str = Form(...),
    employees: str = Form(...),
    established_year: str = Form(...),
    capital: str = Form(...),
    gbiz_id: str = Form(...),
    invoice_registered: str = Form(...),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    current_user = session.get(User, user["id"])
    profile_dict = {
        "業種": industry,
        "所在地": location,
        "従業員数": employees,
        "設立年": established_year,
        "資本金": capital,
        "GビズID": gbiz_id,
        "インボイス登録": invoice_registered
    }
    current_user.profile_info = json.dumps(profile_dict, ensure_ascii=False)
    session.add(current_user)
    session.commit()

    uploads = session.exec(select(Upload).where(Upload.user_id == current_user.id)).all()
    client = OpenAI(api_key=OPENAI_API_KEY)

    for upload in uploads:
        if not upload.parsed_text:
            continue

        summary_input = upload.parsed_text[:3000]
        profile_lines = [f"- {k}: {v}" for k, v in profile_dict.items() if v]
        profile_block = "\n".join(profile_lines)

        prompt_eligibility = f"""
以下は補助金の公募要領の抜粋です。
この補助金の申請対象になれるのは、どのような事業者ですか？
私の企業が対象かどうかを判定し、その理由を述べてください。

【要領本文】
{summary_input}

【私の企業情報】
{profile_block}

【出力形式】
- 対象 or 対象外（1行）
- 理由（簡潔に）
"""
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt_eligibility}],
            temperature=0.3,
        )
        eligibility_text = response.choices[0].message.content.strip()
        lines = eligibility_text.splitlines()
        upload.eligibility_status = lines[0] if lines else "未判定"
        upload.eligibility_result = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
        upload.status = f"判定再実行: {datetime.now().isoformat()}"
        session.add(upload)

    session.commit()
    return RedirectResponse(url="/mypage", status_code=303)


@router.post("/upload/{upload_id}/reanalyze", response_class=HTMLResponse)
async def reanalyze_upload(
    request: Request,
    upload_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    upload = session.get(Upload, upload_id)
    if not upload or upload.user_id != user["id"]:
        return RedirectResponse(url="/mypage", status_code=302)

    parsed_text = upload.parsed_text
    if not parsed_text:
        return RedirectResponse(url=f"/upload/{upload_id}", status_code=302)

    current_user = session.get(User, user["id"])
    profile_dict = json.loads(current_user.profile_info) if current_user.profile_info else {}
    summary_input = parsed_text[:3000]
    profile_lines = [f"- {k}: {v}" for k, v in profile_dict.items() if v]
    profile_block = "\n".join(profile_lines)

    prompt_eligibility = f"""
以下は補助金の公募要領の抜粋です。
この補助金の申請対象になれるのは、どのような事業者ですか？
私の企業が対象かどうかを判定し、その理由を述べてください。

【要領本文】
{summary_input}

【私の企業情報】
{profile_block}

【出力形式】
- 対象 or 対象外（1行）
- 理由（簡潔に）
"""
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt_eligibility}],
        temperature=0.3,
    )
    eligibility_text = response.choices[0].message.content.strip()
    lines = eligibility_text.splitlines()
    upload.eligibility_status = lines[0] if lines else "未判定"
    upload.eligibility_result = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
    upload.status = f"判定再実行: {datetime.now().isoformat()}"
    session.add(upload)
    session.commit()
    return RedirectResponse(url=f"/upload/{upload_id}", status_code=303)
