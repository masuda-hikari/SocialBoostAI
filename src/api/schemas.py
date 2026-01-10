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


# =============================================================================
# TikTok分析関連（v1.3）
# =============================================================================


class TikTokAnalysisRequest(BaseModel):
    """TikTok分析リクエスト"""

    period_days: int = Field(default=7, ge=1, le=90)


class TikTokAnalysisSummary(BaseModel):
    """TikTok分析サマリー"""

    total_videos: int
    total_views: int = 0
    total_likes: int = 0
    total_comments: int = 0
    total_shares: int = 0
    engagement_rate: float = 0.0
    view_to_like_ratio: float = 0.0
    avg_views_per_video: float = 0.0
    best_hour: Optional[int] = None
    best_duration_range: Optional[str] = None
    top_hashtags: list[str] = []


class TikTokAnalysisResponse(BaseModel):
    """TikTok分析レスポンス"""

    id: str
    user_id: str
    platform: str = "tiktok"
    period_start: datetime
    period_end: datetime
    summary: TikTokAnalysisSummary
    created_at: datetime


class TikTokSoundInfo(BaseModel):
    """TikTokサウンド情報"""

    sound_id: str
    sound_name: str
    usage_count: int = 0
    avg_engagement: float = 0.0
    is_trending: bool = False


class TikTokContentPattern(BaseModel):
    """TikTokコンテンツパターン"""

    pattern_type: str
    count: int
    avg_engagement: float


class TikTokAnalysisDetail(BaseModel):
    """TikTok分析詳細レスポンス"""

    id: str
    user_id: str
    platform: str = "tiktok"
    period_start: datetime
    period_end: datetime
    summary: TikTokAnalysisSummary
    hourly_breakdown: list[dict] = []
    content_patterns: list[TikTokContentPattern] = []
    sound_analysis: list[TikTokSoundInfo] = []
    recommendations: Optional[dict] = None
    avg_video_duration: float = 0.0
    duet_performance: Optional[float] = None
    stitch_performance: Optional[float] = None
    created_at: datetime


# =============================================================================
# YouTube分析関連（v1.4）
# =============================================================================


class YouTubeAnalysisRequest(BaseModel):
    """YouTube分析リクエスト"""

    period_days: int = Field(default=7, ge=1, le=90)


class YouTubeAnalysisSummary(BaseModel):
    """YouTube分析サマリー"""

    total_videos: int
    total_shorts: int = 0
    total_views: int = 0
    total_likes: int = 0
    total_comments: int = 0
    engagement_rate: float = 0.0
    view_to_like_ratio: float = 0.0
    avg_views_per_video: float = 0.0
    best_hour: Optional[int] = None
    best_duration_range: Optional[str] = None
    top_tags: list[str] = []


class YouTubeAnalysisResponse(BaseModel):
    """YouTube分析レスポンス"""

    id: str
    user_id: str
    platform: str = "youtube"
    period_start: datetime
    period_end: datetime
    summary: YouTubeAnalysisSummary
    created_at: datetime


class YouTubeTagInfo(BaseModel):
    """YouTubeタグ情報"""

    tag: str
    usage_count: int = 0
    total_views: int = 0
    avg_engagement: float = 0.0
    effectiveness_score: float = 0.0


class YouTubeCategoryInfo(BaseModel):
    """YouTubeカテゴリ情報"""

    category_id: str
    category_name: str
    video_count: int = 0
    total_views: int = 0
    avg_engagement: float = 0.0


class YouTubeContentPattern(BaseModel):
    """YouTubeコンテンツパターン"""

    pattern_type: str
    count: int
    avg_engagement: float


class YouTubeShortsVsVideoComparison(BaseModel):
    """Shorts vs 通常動画比較"""

    shorts_count: int = 0
    shorts_avg_views: float = 0.0
    shorts_avg_engagement: float = 0.0
    regular_count: int = 0
    regular_avg_views: float = 0.0
    regular_avg_engagement: float = 0.0
    views_ratio: float = 0.0
    engagement_ratio: float = 0.0


class YouTubeAnalysisDetail(BaseModel):
    """YouTube分析詳細レスポンス"""

    id: str
    user_id: str
    platform: str = "youtube"
    period_start: datetime
    period_end: datetime
    summary: YouTubeAnalysisSummary
    hourly_breakdown: list[dict] = []
    content_patterns: list[YouTubeContentPattern] = []
    tag_analysis: list[YouTubeTagInfo] = []
    category_analysis: list[YouTubeCategoryInfo] = []
    recommendations: Optional[dict] = None
    avg_video_duration: float = 0.0
    shorts_vs_video: Optional[YouTubeShortsVsVideoComparison] = None
    created_at: datetime


# =============================================================================
# LinkedIn分析関連（v1.5）
# =============================================================================


class LinkedInAnalysisRequest(BaseModel):
    """LinkedIn分析リクエスト"""

    period_days: int = Field(default=7, ge=1, le=90)


class LinkedInAnalysisSummary(BaseModel):
    """LinkedIn分析サマリー"""

    total_posts: int
    total_articles: int = 0
    total_impressions: int = 0
    total_likes: int = 0
    total_comments: int = 0
    total_shares: int = 0
    total_clicks: int = 0
    engagement_rate: float = 0.0
    click_through_rate: float = 0.0
    virality_rate: float = 0.0
    avg_likes_per_post: float = 0.0
    best_hour: Optional[int] = None
    best_days: list[str] = []
    top_hashtags: list[str] = []


class LinkedInAnalysisResponse(BaseModel):
    """LinkedIn分析レスポンス"""

    id: str
    user_id: str
    platform: str = "linkedin"
    period_start: datetime
    period_end: datetime
    summary: LinkedInAnalysisSummary
    created_at: datetime


class LinkedInContentPattern(BaseModel):
    """LinkedInコンテンツパターン"""

    pattern_type: str
    count: int
    avg_engagement: float


class LinkedInDailyBreakdown(BaseModel):
    """曜日別パフォーマンス"""

    weekday: int
    weekday_name: str
    avg_likes: float
    avg_shares: float
    avg_comments: float
    avg_clicks: float
    avg_impressions: float
    post_count: int
    total_engagement: float


class LinkedInMediaTypePerformance(BaseModel):
    """メディアタイプ別パフォーマンス"""

    media_type: str
    avg_engagement: float


class LinkedInAnalysisDetail(BaseModel):
    """LinkedIn分析詳細レスポンス"""

    id: str
    user_id: str
    platform: str = "linkedin"
    period_start: datetime
    period_end: datetime
    summary: LinkedInAnalysisSummary
    hourly_breakdown: list[dict] = []
    daily_breakdown: list[LinkedInDailyBreakdown] = []
    content_patterns: list[LinkedInContentPattern] = []
    recommendations: Optional[dict] = None
    avg_post_length: float = 0.0
    media_type_performance: list[LinkedInMediaTypePerformance] = []
    created_at: datetime


# =============================================================================
# AIコンテンツ生成関連（v1.6）
# =============================================================================


class ContentPlatformType(str, Enum):
    """コンテンツプラットフォーム"""

    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    LINKEDIN = "linkedin"


class ContentTypeEnum(str, Enum):
    """コンテンツタイプ"""

    POST = "post"
    THREAD = "thread"
    STORY = "story"
    REEL = "reel"
    VIDEO = "video"
    ARTICLE = "article"
    CAPTION = "caption"


class ContentToneEnum(str, Enum):
    """コンテンツトーン"""

    PROFESSIONAL = "professional"
    CASUAL = "casual"
    HUMOROUS = "humorous"
    EDUCATIONAL = "educational"
    INSPIRATIONAL = "inspirational"
    PROMOTIONAL = "promotional"


class ContentGoalEnum(str, Enum):
    """コンテンツ目標"""

    ENGAGEMENT = "engagement"
    AWARENESS = "awareness"
    CONVERSION = "conversion"
    TRAFFIC = "traffic"
    COMMUNITY = "community"


class ContentGenerationRequest(BaseModel):
    """コンテンツ生成リクエスト"""

    platform: ContentPlatformType
    content_type: ContentTypeEnum = ContentTypeEnum.POST
    topic: Optional[str] = None
    keywords: list[str] = []
    tone: ContentToneEnum = ContentToneEnum.CASUAL
    goal: ContentGoalEnum = ContentGoalEnum.ENGAGEMENT
    reference_content: Optional[str] = None
    target_audience: Optional[str] = None
    include_hashtags: bool = True
    include_cta: bool = False
    max_length: Optional[int] = None


class GeneratedContentResponse(BaseModel):
    """生成コンテンツレスポンス"""

    id: str
    platform: ContentPlatformType
    content_type: ContentTypeEnum
    main_text: str
    hashtags: list[str] = []
    call_to_action: Optional[str] = None
    media_suggestion: Optional[str] = None
    estimated_engagement: Optional[str] = None
    created_at: datetime


class ContentRewriteRequest(BaseModel):
    """コンテンツリライトリクエスト"""

    original_content: str
    source_platform: ContentPlatformType
    target_platform: ContentPlatformType
    preserve_hashtags: bool = False
    tone: Optional[ContentToneEnum] = None


class ABTestVariationRequest(BaseModel):
    """A/Bテストバリエーション生成リクエスト"""

    base_topic: str
    platform: ContentPlatformType
    variation_count: int = Field(default=3, ge=2, le=5)
    tone: ContentToneEnum = ContentToneEnum.CASUAL


class ContentVariationResponse(BaseModel):
    """コンテンツバリエーションレスポンス"""

    version: str
    text: str
    hashtags: list[str] = []
    focus: str


class ABTestResponse(BaseModel):
    """A/Bテストレスポンス"""

    id: str
    topic: str
    platform: ContentPlatformType
    variations: list[ContentVariationResponse]
    created_at: datetime


class ContentCalendarRequest(BaseModel):
    """コンテンツカレンダー生成リクエスト"""

    platforms: list[ContentPlatformType]
    days: int = Field(default=7, ge=1, le=30)
    posts_per_day: int = Field(default=2, ge=1, le=5)
    topics: list[str] = []
    tone: ContentToneEnum = ContentToneEnum.CASUAL
    goal: ContentGoalEnum = ContentGoalEnum.ENGAGEMENT


class ContentCalendarItemResponse(BaseModel):
    """カレンダーアイテムレスポンス"""

    scheduled_date: datetime
    platform: ContentPlatformType
    content_type: ContentTypeEnum
    topic: str
    draft_content: str
    hashtags: list[str] = []
    optimal_time: str
    rationale: str


class ContentCalendarResponse(BaseModel):
    """コンテンツカレンダーレスポンス"""

    id: str
    user_id: str
    period_start: datetime
    period_end: datetime
    total_items: int
    items: list[ContentCalendarItemResponse]
    created_at: datetime


class TrendingContentRequest(BaseModel):
    """トレンドコンテンツ生成リクエスト"""

    platform: ContentPlatformType
    trend_keywords: list[str] = Field(min_length=1)
    brand_context: Optional[str] = None
    tone: ContentToneEnum = ContentToneEnum.CASUAL


class TrendingContentResponse(BaseModel):
    """トレンドコンテンツレスポンス"""

    id: str
    platform: ContentPlatformType
    trend_keywords: list[str]
    contents: list[GeneratedContentResponse]
    created_at: datetime


class ContentGenerationSummary(BaseModel):
    """コンテンツ生成履歴サマリー"""

    id: str
    user_id: str
    platform: ContentPlatformType
    content_type: str
    preview: str
    created_at: datetime
