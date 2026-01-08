"""
API スキーマ定義
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# 認証関連
class UserRole(str, Enum):
    """ユーザーロール"""

    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class UserCreate(BaseModel):
    """ユーザー作成リクエスト"""

    email: EmailStr
    password: str = Field(min_length=8)
    username: str = Field(min_length=3, max_length=50)


class UserResponse(BaseModel):
    """ユーザーレスポンス"""

    id: str
    email: str
    username: str
    role: UserRole
    created_at: datetime
    is_active: bool


class TokenResponse(BaseModel):
    """トークンレスポンス"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    """ログインリクエスト"""

    email: EmailStr
    password: str


# 分析関連
class AnalysisRequest(BaseModel):
    """分析リクエスト"""

    platform: str = "twitter"
    period_days: int = Field(default=7, ge=1, le=90)


class AnalysisSummary(BaseModel):
    """分析サマリー"""

    total_posts: int
    total_likes: int
    total_retweets: int
    engagement_rate: float
    best_hour: Optional[int] = None
    top_hashtags: list[str] = []


class AnalysisResponse(BaseModel):
    """分析レスポンス"""

    id: str
    user_id: str
    platform: str
    period_start: datetime
    period_end: datetime
    summary: AnalysisSummary
    created_at: datetime


# レポート関連
class ReportType(str, Enum):
    """レポートタイプ"""

    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class ReportRequest(BaseModel):
    """レポートリクエスト"""

    report_type: ReportType
    platform: str = "twitter"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ReportResponse(BaseModel):
    """レポートレスポンス"""

    id: str
    user_id: str
    report_type: ReportType
    platform: str
    period_start: datetime
    period_end: datetime
    html_url: Optional[str] = None
    created_at: datetime


# エラーレスポンス
class ErrorResponse(BaseModel):
    """エラーレスポンス"""

    error: str
    detail: Optional[str] = None
    code: str


# ページネーション
class PaginationParams(BaseModel):
    """ページネーションパラメータ"""

    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """ページネーション付きレスポンス"""

    items: list
    total: int
    page: int
    per_page: int
    pages: int
