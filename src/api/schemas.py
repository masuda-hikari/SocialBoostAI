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


# 課金関連
class PlanTier(str, Enum):
    """プランティア"""

    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class PlanInfo(BaseModel):
    """プラン情報"""

    tier: PlanTier
    name: str
    price_monthly: int  # 月額（円）
    api_calls_per_day: int
    reports_per_month: int  # -1 = 無制限
    platforms: int  # -1 = 無制限
    history_days: int  # -1 = 無制限


class SubscriptionResponse(BaseModel):
    """サブスクリプションレスポンス"""

    id: str
    user_id: str
    plan: PlanTier
    status: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    canceled_at: Optional[datetime] = None
    created_at: datetime


class CheckoutSessionRequest(BaseModel):
    """Checkout Session作成リクエスト"""

    plan: PlanTier
    success_url: str
    cancel_url: str


class CheckoutSessionResponse(BaseModel):
    """Checkout Session作成レスポンス"""

    checkout_url: str


class PortalSessionRequest(BaseModel):
    """Customer Portal Session作成リクエスト"""

    return_url: str


class PortalSessionResponse(BaseModel):
    """Customer Portal Session作成レスポンス"""

    portal_url: str


class CancelSubscriptionRequest(BaseModel):
    """サブスクリプションキャンセルリクエスト"""

    at_period_end: bool = True


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


# Instagram分析関連
class InstagramAnalysisRequest(BaseModel):
    """Instagram分析リクエスト"""

    period_days: int = Field(default=7, ge=1, le=90)


class InstagramAnalysisSummary(BaseModel):
    """Instagram分析サマリー"""

    total_posts: int
    total_reels: int = 0
    total_likes: int
    total_comments: int
    total_saves: int = 0
    engagement_rate: float
    best_hour: Optional[int] = None
    top_hashtags: list[str] = []


class InstagramAnalysisResponse(BaseModel):
    """Instagram分析レスポンス"""

    id: str
    user_id: str
    platform: str = "instagram"
    period_start: datetime
    period_end: datetime
    summary: InstagramAnalysisSummary
    created_at: datetime


class InstagramContentPattern(BaseModel):
    """Instagramコンテンツパターン"""

    pattern_type: str
    count: int
    avg_engagement: float


class InstagramAnalysisDetail(BaseModel):
    """Instagram分析詳細レスポンス"""

    id: str
    user_id: str
    platform: str = "instagram"
    period_start: datetime
    period_end: datetime
    summary: InstagramAnalysisSummary
    hourly_breakdown: list[dict] = []
    content_patterns: list[InstagramContentPattern] = []
    recommendations: Optional[dict] = None
    created_at: datetime


# =============================================================================
# クロスプラットフォーム比較関連（v1.2）
# =============================================================================


class CrossPlatformComparisonRequest(BaseModel):
    """クロスプラットフォーム比較リクエスト"""

    twitter_analysis_id: Optional[str] = None
    instagram_analysis_id: Optional[str] = None
    period_days: int = Field(default=7, ge=1, le=90)


class PlatformPerformanceSummary(BaseModel):
    """プラットフォーム別パフォーマンスサマリー"""

    platform: str
    total_posts: int
    total_engagement: int
    avg_engagement_rate: float
    avg_likes_per_post: float
    avg_comments_per_post: float
    avg_shares_per_post: float
    best_hour: Optional[int] = None
    top_hashtags: list[str] = []


class ComparisonItemResponse(BaseModel):
    """比較項目レスポンス"""

    metric_name: str
    twitter_value: Optional[float] = None
    instagram_value: Optional[float] = None
    difference_percent: Optional[float] = None
    winner: Optional[str] = None
    insight: str = ""


class CrossPlatformComparisonResponse(BaseModel):
    """クロスプラットフォーム比較レスポンス"""

    id: str
    user_id: str
    period_start: datetime
    period_end: datetime
    platforms_analyzed: list[str]
    twitter_performance: Optional[PlatformPerformanceSummary] = None
    instagram_performance: Optional[PlatformPerformanceSummary] = None
    comparison_items: list[ComparisonItemResponse] = []
    overall_winner: Optional[str] = None
    cross_platform_insights: list[str] = []
    strategic_recommendations: list[str] = []
    synergy_opportunities: list[str] = []
    created_at: datetime


class CrossPlatformComparisonSummary(BaseModel):
    """クロスプラットフォーム比較サマリー（一覧用）"""

    id: str
    user_id: str
    period_start: datetime
    period_end: datetime
    platforms: list[str]
    total_posts: int
    total_engagement: int
    best_platform: Optional[str] = None
    key_insight: str = ""
    created_at: datetime
