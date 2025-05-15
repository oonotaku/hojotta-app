from fastapi import APIRouter, Request, UploadFile, File, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session
from datetime import datetime
import os
import re
import json
from app.database import get_db
from app.models import Upload, FmtUpload, User
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

def split_text_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 100) -> list:
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", "。", "."],
        chunk_size=chunk_size,
        chunk_overlap=overlap
    )
    return splitter.split_text(text)

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

    return "✅ 以下を整えれば申請準備OKです（代表項目のみ表示）：\n" + "\n".join(f"- {line}" for line in display_lines)
