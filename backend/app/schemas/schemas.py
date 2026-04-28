from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


# --- Auth Schemas ---
class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: UUID
    email: str
    username: str
    is_active: bool
    avatar_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Repository Schemas ---
class RepoCreate(BaseModel):
    github_url: Optional[str] = None


class RepoOut(BaseModel):
    id: UUID
    name: str
    source_type: str
    github_url: Optional[str] = None
    status: str
    file_count: int
    chunk_count: int
    language_stats: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Query Schemas ---
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=2000)
    repository_id: UUID
    rewrite_query: bool = True


class CodeChunkRef(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    content: str
    language: str
    score: float


class QueryResponse(BaseModel):
    query_id: UUID
    original_query: str
    rewritten_query: Optional[str] = None
    answer: str
    references: list[CodeChunkRef]
    tokens_used: int
    response_time_ms: int


class FeedbackRequest(BaseModel):
    feedback: str  # "positive" | "negative"


# --- History Schema ---
class QueryHistoryOut(BaseModel):
    id: UUID
    query: str
    response: str
    feedback: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
