# app/models.py
from sqlmodel import SQLModel, Field
from typing import Optional

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    is_admin: bool = False
    profile_info: Optional[str] = None

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
    status: Optional[str] = None  # 対象判定済みなど
    requirements_summary: Optional[str] = None  # 申請に必要なものの要約
    eligibility_result: Optional[str] = None    # 対象かどうかの判定（文章）
    eligibility_status: Optional[str] = None    # "対象" or "対象外" など
    extracted_by_ai: Optional[bool] = Field(default=False)  # AIで要約済みかどうか

