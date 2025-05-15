from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    is_admin: bool = False
    profile_info: Optional[str] = None
    industry: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None)
    employee_count: Optional[str] = Field(default=None)
    company_name: Optional[str] = Field(default=None)
    founded_date: Optional[str] = Field(default=None)
    company_type: Optional[str] = Field(default=None)
    tax_location: Optional[str] = Field(default=None)
    capital: Optional[str] = Field(default=None)
    has_gbizid: Optional[bool] = Field(default=False)

class ConversationLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    filename: str
    timestamp: str
    question: str
    answer: str

class Upload(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    filename: str
    title: Optional[str] = None
    upload_time: str
    parsed_text: Optional[str] = None
    status: Optional[str] = None
    requirements_summary: Optional[str] = None
    eligibility_result: Optional[str] = None
    eligibility_status: Optional[str] = None
    extracted_by_ai: Optional[bool] = Field(default=False)
    fmt_filename: Optional[str] = Field(default=None, nullable=True)
    pitch_filename: Optional[str] = Field(default=None, nullable=True)
    is_active: bool = Field(default=True)

# ✅ 追加：Writingモデル
class Writing(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    title: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FmtUpload(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    upload_id: int = Field(foreign_key="upload.id")  # 公募要領（Upload）に紐づく
    filename: str  # 元ファイル名（例：jigyou_keikaku.docx）
    file_path: str  # 保存先パス（例：uploaded_fmt/upload_1/jigyou_keikaku.docx）
    uploaded_at: str  # 日時文字列（ISO形式）
    section: Optional[str] = None  # 種別（事業計画、体制など）※任意
    has_generated: bool = Field(default=False)  # 作文生成済みかどうか
    fmt_type: Optional[str] = Field(default="monozukuri", nullable=True)
    generated_json: Optional[str] = Field(default=None, nullable=True)
