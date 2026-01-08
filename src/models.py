"""
データモデル定義
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Tweet(BaseModel):
    """ツイートデータモデル"""

    id: str
    text: str
    created_at: datetime
    likes: int = Field(ge=0, default=0)
    retweets: int = Field(ge=0, default=0)
    replies: int = Field(ge=0, default=0)
    impressions: Optional[int] = Field(ge=0, default=None)
    author_id: Optional[str] = None


class EngagementMetrics(BaseModel):
    """エンゲージメント指標"""

    total_likes: int = 0
    total_retweets: int = 0
    total_replies: int = 0
    engagement_rate: float = 0.0
    avg_likes_per_post: float = 0.0
    avg_retweets_per_post: float = 0.0


class HourlyEngagement(BaseModel):
    """時間帯別エンゲージメント"""

    hour: int = Field(ge=0, le=23)
    avg_likes: float
    avg_retweets: float
    post_count: int
    total_engagement: float


class PostRecommendation(BaseModel):
    """投稿レコメンデーション"""

    best_hours: list[int]
    suggested_hashtags: list[str]
    content_ideas: list[str]
    reasoning: str


class HashtagAnalysis(BaseModel):
    """ハッシュタグ分析結果"""

    hashtag: str
    usage_count: int = 0
    total_likes: int = 0
    total_retweets: int = 0
    avg_engagement: float = 0.0
    effectiveness_score: float = Field(ge=0.0, default=0.0)


class KeywordAnalysis(BaseModel):
    """キーワード分析結果"""

    keyword: str
    frequency: int = 0
    avg_engagement: float = 0.0
    correlation_score: float = Field(ge=-1.0, le=1.0, default=0.0)


class ContentPattern(BaseModel):
    """コンテンツパターン分析"""

    pattern_type: str  # "question", "tip", "announcement", "engagement_bait"
    count: int = 0
    avg_engagement: float = 0.0
    example_posts: list[str] = []


class AnalysisResult(BaseModel):
    """分析結果"""

    period_start: datetime
    period_end: datetime
    total_posts: int
    metrics: EngagementMetrics
    hourly_breakdown: list[HourlyEngagement]
    top_performing_posts: list[Tweet]
    recommendations: Optional[PostRecommendation] = None
    # v0.2追加: コンテンツ分析
    hashtag_analysis: list[HashtagAnalysis] = []
    keyword_analysis: list[KeywordAnalysis] = []
    content_patterns: list[ContentPattern] = []


class UserAccount(BaseModel):
    """ユーザーアカウント"""

    id: str
    platform: str
    username: str
    follower_count: int = 0
    following_count: int = 0
    created_at: Optional[datetime] = None


# v0.4: サマリー関連モデル
class PeriodComparison(BaseModel):
    """期間比較データ"""

    metric_name: str
    current_value: float
    previous_value: float
    change_percent: float
    trend: str  # "up", "down", "stable"


class WeeklySummary(BaseModel):
    """週次サマリー"""

    week_number: int
    year: int
    period_start: datetime
    period_end: datetime
    total_posts: int
    metrics: EngagementMetrics
    best_performing_day: str  # 曜日名
    top_post: Optional[Tweet] = None
    comparison: Optional[list[PeriodComparison]] = None
    insights: list[str] = []


class MonthlySummary(BaseModel):
    """月次サマリー"""

    month: int
    year: int
    period_start: datetime
    period_end: datetime
    total_posts: int
    metrics: EngagementMetrics
    weekly_summaries: list[WeeklySummary] = []
    best_performing_week: Optional[int] = None
    top_posts: list[Tweet] = []
    comparison: Optional[list[PeriodComparison]] = None
    insights: list[str] = []
    growth_rate: Optional[float] = None  # 前月比成長率


# =============================================================================
# v1.0: Instagram対応モデル
# =============================================================================


class InstagramPost(BaseModel):
    """Instagram投稿データモデル"""

    id: str
    caption: Optional[str] = None
    media_type: str  # "IMAGE", "VIDEO", "CAROUSEL_ALBUM"
    media_url: Optional[str] = None
    thumbnail_url: Optional[str] = None  # 動画の場合
    permalink: Optional[str] = None
    created_at: datetime
    likes: int = Field(ge=0, default=0)
    comments: int = Field(ge=0, default=0)
    saves: Optional[int] = Field(ge=0, default=None)  # ビジネスアカウントのみ
    shares: Optional[int] = Field(ge=0, default=None)  # ビジネスアカウントのみ
    impressions: Optional[int] = Field(ge=0, default=None)
    reach: Optional[int] = Field(ge=0, default=None)
    engagement: Optional[int] = Field(ge=0, default=None)
    author_id: Optional[str] = None


class InstagramStory(BaseModel):
    """Instagramストーリーデータモデル"""

    id: str
    media_type: str  # "IMAGE", "VIDEO"
    media_url: Optional[str] = None
    created_at: datetime
    expires_at: datetime  # 24時間後
    impressions: Optional[int] = Field(ge=0, default=None)
    reach: Optional[int] = Field(ge=0, default=None)
    replies: int = Field(ge=0, default=0)
    taps_forward: Optional[int] = Field(ge=0, default=None)
    taps_back: Optional[int] = Field(ge=0, default=None)
    exits: Optional[int] = Field(ge=0, default=None)


class InstagramReel(BaseModel):
    """Instagramリールデータモデル"""

    id: str
    caption: Optional[str] = None
    media_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    permalink: Optional[str] = None
    created_at: datetime
    likes: int = Field(ge=0, default=0)
    comments: int = Field(ge=0, default=0)
    saves: Optional[int] = Field(ge=0, default=None)
    shares: Optional[int] = Field(ge=0, default=None)
    plays: Optional[int] = Field(ge=0, default=None)
    reach: Optional[int] = Field(ge=0, default=None)
    author_id: Optional[str] = None


class InstagramEngagementMetrics(BaseModel):
    """Instagramエンゲージメント指標"""

    total_likes: int = 0
    total_comments: int = 0
    total_saves: int = 0
    total_shares: int = 0
    total_impressions: int = 0
    total_reach: int = 0
    engagement_rate: float = 0.0
    avg_likes_per_post: float = 0.0
    avg_comments_per_post: float = 0.0
    avg_saves_per_post: float = 0.0


class InstagramAccount(BaseModel):
    """Instagramアカウント情報"""

    id: str
    username: str
    name: Optional[str] = None
    biography: Optional[str] = None
    profile_picture_url: Optional[str] = None
    website: Optional[str] = None
    followers_count: int = 0
    following_count: int = 0
    media_count: int = 0
    is_business_account: bool = False
    is_verified: bool = False
    created_at: Optional[datetime] = None


class InstagramAnalysisResult(BaseModel):
    """Instagram分析結果"""

    period_start: datetime
    period_end: datetime
    total_posts: int
    total_stories: int = 0
    total_reels: int = 0
    metrics: InstagramEngagementMetrics
    hourly_breakdown: list[HourlyEngagement] = []
    top_performing_posts: list[InstagramPost] = []
    top_performing_reels: list[InstagramReel] = []
    recommendations: Optional[PostRecommendation] = None
    hashtag_analysis: list[HashtagAnalysis] = []
    content_patterns: list[ContentPattern] = []


# =============================================================================
# プラットフォーム共通インターフェース
# =============================================================================


class PlatformType(str):
    """サポートするプラットフォーム"""

    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"  # 将来対応
    YOUTUBE = "youtube"  # 将来対応
    LINKEDIN = "linkedin"  # 将来対応


class UnifiedPost(BaseModel):
    """統一投稿モデル（クロスプラットフォーム比較用）"""

    id: str
    platform: str
    content: Optional[str] = None  # テキスト/キャプション
    media_type: Optional[str] = None  # text, image, video, carousel
    created_at: datetime
    likes: int = 0
    comments: int = 0  # replies/comments
    shares: int = 0  # retweets/shares
    impressions: Optional[int] = None
    reach: Optional[int] = None
    engagement_rate: float = 0.0
    permalink: Optional[str] = None
    author_id: Optional[str] = None

    @classmethod
    def from_tweet(cls, tweet: "Tweet") -> "UnifiedPost":
        """TweetからUnifiedPostに変換"""
        total_engagement = tweet.likes + tweet.retweets + tweet.replies
        engagement_rate = 0.0
        if tweet.impressions and tweet.impressions > 0:
            engagement_rate = (total_engagement / tweet.impressions) * 100

        return cls(
            id=tweet.id,
            platform=PlatformType.TWITTER,
            content=tweet.text,
            media_type="text",
            created_at=tweet.created_at,
            likes=tweet.likes,
            comments=tweet.replies,
            shares=tweet.retweets,
            impressions=tweet.impressions,
            engagement_rate=engagement_rate,
            author_id=tweet.author_id,
        )

    @classmethod
    def from_instagram_post(cls, post: "InstagramPost") -> "UnifiedPost":
        """InstagramPostからUnifiedPostに変換"""
        total_engagement = post.likes + post.comments + (post.saves or 0)
        engagement_rate = 0.0
        if post.reach and post.reach > 0:
            engagement_rate = (total_engagement / post.reach) * 100

        return cls(
            id=post.id,
            platform=PlatformType.INSTAGRAM,
            content=post.caption,
            media_type=post.media_type.lower(),
            created_at=post.created_at,
            likes=post.likes,
            comments=post.comments,
            shares=post.shares or 0,
            impressions=post.impressions,
            reach=post.reach,
            engagement_rate=engagement_rate,
            permalink=post.permalink,
            author_id=post.author_id,
        )


class CrossPlatformMetrics(BaseModel):
    """クロスプラットフォーム統合指標"""

    platforms: list[str]
    period_start: datetime
    period_end: datetime
    total_posts: int = 0
    total_engagement: int = 0
    avg_engagement_rate: float = 0.0
    platform_breakdown: dict[str, dict] = {}  # platform -> metrics
    best_performing_platform: Optional[str] = None
    recommendations: list[str] = []
