from fastapi import APIRouter, Request, UploadFile, File, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session
from datetime import datetime
import os
import re
from app.database import get_db
from app.models import Upload, FmtUpload
from app.utils import extract_text_from_pdf
from app.auth import get_current_user
from fastapi.templating import Jinja2Templates
from openai import OpenAI
from app.config import OPENAI_API_KEY
from app.prompt_generator import get_plan_structure
from langchain.text_splitter import RecursiveCharacterTextSplitter

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

UPLOAD_DIR = "uploaded_pdfs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

EXCLUDE_KEYWORDS = [
    "交付", "精査", "報告", "実績", "支払い", "請求",
    "補助金の返還", "完了報告", "経費の明細", "補助事業の終了",
    "会計検査", "検収", "調査協力", "交付決定", "契約締結後"
]

def filter_pre_submission(lines: list[str]) -> list[str]:
    return [line for line in lines if not any(kw in line for kw in EXCLUDE_KEYWORDS)]

def normalize_line(line: str) -> str:
    line = line.strip("・- ・-　").replace("。", "").lower()
    line = re.sub(r"(補助金)?申請書", "申請書", line)
    line = re.sub(r"事業計画書.*", "事業計画書の提出", line)
    line = re.sub(r".*説明資料.*", "説明資料の提出", line)
    line = re.sub(r"提出.*", "提出", line)
    return line.strip()

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

UPLOAD_DIR = "uploaded_pdfs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def split_text_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 100) -> list:
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", "。", "."],
        chunk_size=chunk_size,
        chunk_overlap=overlap
    )
    return splitter.split_text(text)


EXCLUDE_KEYWORDS = [
    "交付", "精査", "報告", "実績", "支払い", "請求",
    "補助金の返還", "完了報告", "経費の明細", "補助事業の終了",
    "会計検査", "検収", "調査協力", "交付決定", "契約締結後"
]

def filter_pre_submission(lines: list[str]) -> list[str]:
    return [line for line in lines if not any(kw in line for kw in EXCLUDE_KEYWORDS)]

def normalize_line(line: str) -> str:
    import re
    line = line.strip("・- ・-　").replace("。", "").lower()
    line = re.sub(r"(補助金)?申請書", "申請書", line)
    line = re.sub(r"事業計画書.*", "事業計画書の提出", line)
    line = re.sub(r".*説明資料.*", "説明資料の提出", line)
    line = re.sub(r"提出.*", "提出", line)
    return line.strip()

def summarize_chunks(chunks: list, client: OpenAI) -> str:
    summaries = []
    for chunk in chunks:
        prompt = f"""以下は補助金の公募要領の一部抜粋です。

このテキストから、採択されるために必要な提出書類・申請手続き（申請時点まで）のみを抽出してください。
「交付申請」「実績報告」「補助金請求」「支払い」など採択後のプロセスに関する内容は含めないでください。
回答は「- ○○の提出」の形式で、一行に一項目を挙げてください。

{chunk}
"""
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        lines = response.choices[0].message.content.strip().splitlines()
        filtered = filter_pre_submission(lines)
        summaries.extend(filtered)

    unique_lines = sorted(set(
        normalize_line(line)
        for line in summaries if line.strip()
    ))

    top_n = 15
    display_lines = unique_lines[:top_n]

    return "✅ 以下を整えれば申請準備OKです（代表項目のみ表示）：
" + "
".join(f"- {line}" for line in display_lines)

"""
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        summaries.append(response.choices[0].message.content.strip())
    return "\n".join(summaries)

def analyze_with_gpt(parsed_text: str, client: OpenAI, user: dict):
    chunks = split_text_into_chunks(parsed_text)
    requirements_summary = summarize_chunks(chunks, client)

    prompt_eligibility = f"""
以下は補助金の公募要領の抜粋です。
この補助金の申請対象になれるのは、どのような事業者ですか？
また、私の企業が対象かどうかを判定し、その理由を述べてください。

【要領本文】
{parsed_text[:3000]}

【私の企業情報】
- 業種: {user.get('industry', '不明')}
- 所在地: {user.get('location', '不明')}
- 従業員数: {user.get('employee_count', '不明')}

【出力形式】
- 申請できます！ or 対象外です（1行）
- 理由（簡潔に）
"""
    print("👤 ユーザー情報:", user)
    print("📝 GPTプロンプト:\n", prompt_eligibility)

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt_eligibility}],
        temperature=0.3
    )
    lines = response.choices[0].message.content.strip().splitlines()
    status = lines[0] if lines else "未判定"
    result = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
    return requirements_summary, status, result

@router.post("/upload", response_class=HTMLResponse)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    user_id = user["id"]
    save_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(save_path, "wb") as f:
        f.write(await file.read())

    parsed_text = extract_text_from_pdf(save_path)
    client = OpenAI(api_key=OPENAI_API_KEY)

    # ✅ 企業プロフィール情報も渡すように修正！
    reqs, status, result = analyze_with_gpt(parsed_text, client, user)

    upload = Upload(
        user_id=user_id,
        filename=file.filename,
        title=file.filename,
        upload_time=datetime.now().isoformat(),
        parsed_text=parsed_text,
        requirements_summary=reqs,
        eligibility_result=result,
        eligibility_status=status,
        extracted_by_ai=True,
        is_active=True
    )
    db.add(upload)
    db.commit()

    return RedirectResponse(url=f"/upload/{upload.id}", status_code=303)

@router.get("/upload/{upload_id}", response_class=HTMLResponse)
async def upload_detail(
    request: Request,
    upload_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    upload = db.get(Upload, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    if upload.user_id != user["id"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="アクセス権がありません")

    has_plan = "事業計画" in (upload.requirements_summary or "")
    return templates.TemplateResponse("upload_detail.html", {
        "request": request,
        "upload": upload,
        "has_plan": has_plan
    })

@router.post("/upload/{upload_id}/edit", response_class=HTMLResponse)
async def edit_upload_title(
    request: Request,
    upload_id: int,
    new_title: str = Form(...),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    upload = db.get(Upload, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    if upload.user_id != user["id"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="アクセス権がありません")

    upload.title = new_title
    db.add(upload)
    db.commit()
    return RedirectResponse(url=f"/upload/{upload_id}", status_code=303)

@router.post("/upload/{upload_id}/delete", response_class=HTMLResponse)
async def delete_upload(
    request: Request,
    upload_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    upload = db.get(Upload, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    if upload.user_id != user["id"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="アクセス権がありません")

    upload.is_active = False
    db.add(upload)
    db.commit()
    return RedirectResponse(url="/mypage", status_code=303)

@router.post("/upload/{upload_id}/reanalyze", response_class=HTMLResponse)
async def reanalyze_upload(
    request: Request,
    upload_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    upload = db.get(Upload, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    if upload.user_id != user["id"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="アクセス権がありません")

    client = OpenAI(api_key=OPENAI_API_KEY)
    reqs, status, result = analyze_with_gpt(upload.parsed_text, client, user)
    upload.requirements_summary = reqs
    upload.eligibility_status = status
    upload.eligibility_result = result
    upload.status = f"判定再実行: {datetime.now().isoformat()}"

    db.add(upload)
    db.commit()
    return RedirectResponse(url=f"/upload/{upload.id}", status_code=303)

@router.post("/upload/{upload_id}/fmt", response_class=HTMLResponse)
async def upload_fmt_file(
    request: Request,
    upload_id: int,
    fmt_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    upload = db.get(Upload, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    if upload.user_id != user["id"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="アクセス権がありません")

    # 保存ディレクトリを作成（必要なら）
    upload_dir = "uploaded_fmt"
    os.makedirs(upload_dir, exist_ok=True)

    # 保存ファイル名を一意に（例：upload_5_fmt_ホジョッタ様式.docx）
    safe_name = f"upload_{upload_id}_fmt_{fmt_file.filename}"
    file_path = os.path.join(upload_dir, safe_name)

    # 保存処理
    with open(file_path, "wb") as buffer:
        buffer.write(await fmt_file.read())

    # DBにファイル名を保存
    upload.fmt_filename = safe_name
    db.add(upload)
    db.commit()

    return RedirectResponse(url=f"/upload/{upload_id}", status_code=303)

@router.post("/upload/{upload_id}/pitch", response_class=HTMLResponse)
async def upload_pitch_file(
    request: Request,
    upload_id: int,
    pitch_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    upload = db.get(Upload, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    if upload.user_id != user["id"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="アクセス権がありません")

    upload_dir = "uploaded_pitch"
    os.makedirs(upload_dir, exist_ok=True)

    safe_name = f"upload_{upload_id}_pitch_{pitch_file.filename}"
    file_path = os.path.join(upload_dir, safe_name)

    with open(file_path, "wb") as f:
        f.write(await pitch_file.read())

    upload.pitch_filename = safe_name
    db.add(upload)
    db.commit()

    return RedirectResponse(url=f"/upload/{upload_id}", status_code=303)


@router.post("/upload/{upload_id}/pitch/delete", response_class=HTMLResponse)
async def delete_pitch_file(
    request: Request,
    upload_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    upload = db.get(Upload, upload_id)
    if not upload or not upload.pitch_filename:
        raise HTTPException(status_code=404, detail="ピッチ資料が見つかりません")
    if upload.user_id != user["id"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="アクセス権がありません")

    file_path = os.path.join("uploaded_pitch", upload.pitch_filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    upload.pitch_filename = None
    db.add(upload)
    db.commit()

    return RedirectResponse(url=f"/upload/{upload_id}", status_code=303)

@router.get("/upload/{upload_id}/fmt", response_class=HTMLResponse)
async def upload_fmt_page(
    request: Request,
    upload_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    upload = db.get(Upload, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    if upload.user_id != user["id"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="アクセス権がありません")

    fmt_files = db.query(FmtUpload).filter(FmtUpload.upload_id == upload_id).all()

    return templates.TemplateResponse("upload_fmt.html", {
        "request": request,
        "upload": upload,
        "fmt_files": fmt_files
    })

@router.post("/upload/{upload_id}/fmt/add", response_class=HTMLResponse)
async def add_fmt_file(
    request: Request,
    upload_id: int,
    fmt_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    upload = db.get(Upload, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    if upload.user_id != user["id"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="アクセス権がありません")

    # 保存ディレクトリ作成
    upload_dir = f"uploaded_fmt/upload_{upload_id}"
    os.makedirs(upload_dir, exist_ok=True)

    # 保存ファイル名とパス
    safe_name = fmt_file.filename
    save_path = os.path.join(upload_dir, safe_name)

    # ファイル書き込み
    with open(save_path, "wb") as f:
        f.write(await fmt_file.read())

    # DBにレコード追加
    new_fmt = FmtUpload(
        upload_id=upload_id,
        filename=fmt_file.filename,
        file_path=save_path,
        uploaded_at=datetime.now().isoformat()
    )
    db.add(new_fmt)
    db.commit()

    return RedirectResponse(url=f"/upload/{upload_id}/fmt", status_code=303)

@router.post("/upload/{upload_id}/fmt/{fmt_id}/delete", response_class=HTMLResponse)
async def delete_fmt_file(
    request: Request,
    upload_id: int,
    fmt_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    fmt = db.get(FmtUpload, fmt_id)
    if not fmt or fmt.upload_id != upload_id:
        raise HTTPException(status_code=404, detail="FMTファイルが見つかりません")

    upload = db.get(Upload, upload_id)
    if upload.user_id != user["id"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="アクセス権がありません")

    # ファイル削除
    if os.path.exists(fmt.file_path):
        os.remove(fmt.file_path)

    db.delete(fmt)
    db.commit()

    return RedirectResponse(url=f"/upload/{upload_id}/fmt", status_code=303)

@router.get("/upload/{upload_id}/fmt/{fmt_id}/generate", response_class=HTMLResponse)
async def show_generated_plan(
    request: Request,
    upload_id: int,
    fmt_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    upload = db.get(Upload, upload_id)
    fmt = db.get(FmtUpload, fmt_id)
    if not upload or not fmt:
        raise HTTPException(status_code=404, detail="データが見つかりません")
    if upload.user_id != user["id"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="アクセスできません")

    import json
    sections = json.loads(fmt.generated_json) if fmt.generated_json else []

    return templates.TemplateResponse("upload_generate.html", {
        "request": request,
        "upload": upload,
        "fmt": fmt,
        "sections": sections
    })


@router.post("/upload/{upload_id}/fmt/{fmt_id}/generate/run", response_class=HTMLResponse)
async def run_generate_plan(
    upload_id: int,
    fmt_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    from app.prompt_generator import get_plan_structure
    import json, os

    upload = db.get(Upload, upload_id)
    fmt = db.get(FmtUpload, fmt_id)
    if not upload or not fmt:
        raise HTTPException(status_code=404, detail="データが見つかりません")
    if upload.user_id != user["id"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="アクセスできません")

    # ピッチ読み込み（最大6000字）
    with open(f"uploaded_pitch/{upload.pitch_filename}", "rb") as f:
        pitch_text = f.read().decode("utf-8", errors="ignore")[:6000]

    template = get_plan_structure(fmt.fmt_type or "monozukuri")
    client = OpenAI(api_key=OPENAI_API_KEY)

    sections = []
    for section in template:
        prompt = f"""
以下は、補助金申請に使うピッチ資料です。
これをもとに、下記の項目「{section['title']}」にふさわしい作文を作成してください。

【制限文字数】：{section['max_chars']}字以内
【ピッチ資料】：
{pitch_text}

【出力形式】
・わかりやすく、簡潔に
・文末は整えること
・補助金の審査員に伝わる表現で
"""
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        sections.append({
            "title": section["title"],
            "content": response.choices[0].message.content.strip()
        })

    fmt.generated_json = json.dumps(sections, ensure_ascii=False)
    fmt.has_generated = True
    db.add(fmt)
    db.commit()

    return RedirectResponse(url=f"/upload/{upload_id}/fmt/{fmt_id}/generate/loading", status_code=303)

@router.get("/upload/{upload_id}/fmt/{fmt_id}/generate/loading", response_class=HTMLResponse)
async def show_loading_page(
    request: Request,
    upload_id: int,
    fmt_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    upload = db.get(Upload, upload_id)
    fmt = db.get(FmtUpload, fmt_id)

    if not upload or not fmt:
        raise HTTPException(status_code=404, detail="データが見つかりません")
    if upload.user_id != user["id"] and not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="アクセスできません")

    return templates.TemplateResponse("upload_generate_loading.html", {
        "request": request,
        "upload": upload,
        "fmt": fmt
    })

@router.get("/api/fmt/{fmt_id}/status")
async def check_fmt_status(fmt_id: int, db: Session = Depends(get_db)):
    fmt = db.get(FmtUpload, fmt_id)
    return {"ready": fmt.has_generated}

