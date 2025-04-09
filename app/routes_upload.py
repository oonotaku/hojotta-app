# app/routes_upload.py
from fastapi import APIRouter, Request, UploadFile, File, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session
from datetime import datetime
import os

from app.database import get_session
from app.models import Upload
from app.utils import extract_text_from_pdf
from app.auth import get_current_user
from fastapi.templating import Jinja2Templates
from openai import OpenAI
from app.config import OPENAI_API_KEY

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

UPLOAD_DIR = "uploaded_pdfs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_class=HTMLResponse)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    username = user["username"]
    user_id = user["id"]

    # ファイル保存
    save_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(save_path, "wb") as f:
        f.write(await file.read())

    # テキスト抽出
    parsed_text = extract_text_from_pdf(save_path)

    # ✅ 送信トークン対策：先頭3000文字だけ使う
    summary_input = parsed_text[:3000]

    client = OpenAI(api_key=OPENAI_API_KEY)

    # AIプロンプト（summary）
    prompt_summary = f"""
以下は補助金の公募要領の抜粋です。
この補助金の申請に必要な書類や手続き、条件を要約してください。

【要領本文】
{summary_input}

【出力形式】
- 申請に必要な書類や手続きの一覧を簡潔にリスト形式で出力してください。
"""
    response_summary = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt_summary}],
        temperature=0.3,
    )
    requirements_summary = response_summary.choices[0].message.content.strip()

    # AIプロンプト（判定）
    prompt_eligibility = f"""
以下は補助金の公募要領の抜粋です。
この補助金の申請対象になれるのは、どのような事業者ですか？
また、私の企業が対象かどうかを判定し、その理由を述べてください。

【要領本文】
{summary_input}

【私の企業情報】
- 業種: 不明（今後登録予定）
- 所在地: 不明（今後登録予定）
- 従業員数: 不明（今後登録予定）

【出力形式】
- 対象 or 対象外（1行）
- 理由（簡潔に）
"""
    response_eligibility = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt_eligibility}],
        temperature=0.3,
    )
    eligibility_text = response_eligibility.choices[0].message.content.strip()

    # 1行目をステータス、残りを詳細として分離
    lines = eligibility_text.splitlines()
    eligibility_status = lines[0] if lines else "未判定"
    eligibility_result = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

    # Uploadテーブルに保存
    upload = Upload(
        user_id=user_id,
        filename=file.filename,
        title=file.filename,
        upload_time=datetime.now().isoformat(),
        parsed_text=parsed_text,
        requirements_summary=requirements_summary,
        eligibility_result=eligibility_result,
        eligibility_status=eligibility_status,
        extracted_by_ai=True
    )
    session.add(upload)
    session.commit()
    session.refresh(upload)

    return RedirectResponse(url=f"/upload/{upload.id}", status_code=303)

@router.get("/upload/{upload_id}", response_class=HTMLResponse)
async def upload_detail(
    request: Request,
    upload_id: int,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    upload = session.get(Upload, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    if upload.user_id != user["id"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="アクセス権がありません")

    return templates.TemplateResponse("upload_detail.html", {
        "request": request,
        "upload": upload
    })

@router.post("/upload/{upload_id}/edit", response_class=HTMLResponse)
async def edit_upload_title(
    request: Request,
    upload_id: int,
    new_title: str = Form(...),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    upload = session.get(Upload, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    if upload.user_id != user["id"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="アクセス権がありません")

    upload.title = new_title
    session.add(upload)
    session.commit()

    return RedirectResponse(url=f"/upload/{upload_id}", status_code=303)
