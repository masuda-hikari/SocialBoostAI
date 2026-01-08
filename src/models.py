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
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
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

    @classmethod
    def from_tiktok_video(cls, video: "TikTokVideo") -> "UnifiedPost":
        """TikTokVideoからUnifiedPostに変換"""
        total_engagement = video.likes + video.comments + video.shares
        engagement_rate = 0.0
        if video.views and video.views > 0:
            engagement_rate = (total_engagement / video.views) * 100

        return cls(
            id=video.id,
            platform=PlatformType.TIKTOK,
            content=video.description,
            media_type="video",
            created_at=video.create_time,
            likes=video.likes,
            comments=video.comments,
            shares=video.shares,
            impressions=video.impressions,
            reach=video.reach,
            engagement_rate=engagement_rate,
            permalink=video.share_url,
            author_id=video.author_id,
        )

    @classmethod
    def from_youtube_video(cls, video: "YouTubeVideo") -> "UnifiedPost":
        """YouTubeVideoからUnifiedPostに変換"""
        total_engagement = video.likes + video.comments
        engagement_rate = 0.0
        if video.views and video.views > 0:
            engagement_rate = (total_engagement / video.views) * 100

        return cls(
            id=video.id,
            platform=PlatformType.YOUTUBE,
            content=video.title,
            media_type="video",
            created_at=video.published_at,
            likes=video.likes,
            comments=video.comments,
            shares=video.shares or 0,
            impressions=video.views,  # YouTubeではviewsをimpressionsに
            engagement_rate=engagement_rate,
            permalink=video.video_url,
            author_id=video.channel_id,
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


# =============================================================================
# v1.2: クロスプラットフォーム比較モデル
# =============================================================================


class PlatformPerformance(BaseModel):
    """プラットフォーム別パフォーマンス"""

    platform: str
    total_posts: int = 0
    total_engagement: int = 0
    avg_engagement_rate: float = 0.0
    avg_likes_per_post: float = 0.0
    avg_comments_per_post: float = 0.0
    avg_shares_per_post: float = 0.0
    best_hour: Optional[int] = None
    top_hashtags: list[str] = []
    content_insights: list[str] = []


class PlatformComparisonItem(BaseModel):
    """プラットフォーム間比較項目"""

    metric_name: str
    twitter_value: Optional[float] = None
    instagram_value: Optional[float] = None
    difference_percent: Optional[float] = None  # Instagram - Twitter比
    winner: Optional[str] = None  # "twitter", "instagram", "tie"
    insight: str = ""


class CrossPlatformComparison(BaseModel):
    """クロスプラットフォーム比較結果"""

    period_start: datetime
    period_end: datetime
    platforms_analyzed: list[str]
    twitter_performance: Optional[PlatformPerformance] = None
    instagram_performance: Optional[PlatformPerformance] = None
    comparison_items: list[PlatformComparisonItem] = []
    overall_winner: Optional[str] = None  # 総合的に優れているプラットフォーム
    cross_platform_insights: list[str] = []
    strategic_recommendations: list[str] = []
    synergy_opportunities: list[str] = []  # プラットフォーム間連携の機会


class CrossPlatformSummary(BaseModel):
    """クロスプラットフォーム比較サマリー（API用）"""

    comparison_id: str
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
# v1.3: TikTok対応モデル
# =============================================================================


class TikTokVideo(BaseModel):
    """TikTok動画データモデル"""

    id: str
    description: Optional[str] = None
    create_time: datetime
    duration: int = Field(ge=0, default=0)  # 秒
    cover_image_url: Optional[str] = None
    share_url: Optional[str] = None
    # エンゲージメント指標
    likes: int = Field(ge=0, default=0)
    comments: int = Field(ge=0, default=0)
    shares: int = Field(ge=0, default=0)
    views: int = Field(ge=0, default=0)
    # 追加指標（ビジネスアカウントのみ）
    saves: Optional[int] = Field(ge=0, default=None)
    reach: Optional[int] = Field(ge=0, default=None)
    impressions: Optional[int] = Field(ge=0, default=None)
    # サウンド情報
    sound_id: Optional[str] = None
    sound_name: Optional[str] = None
    is_original_sound: bool = False
    # ハッシュタグ・メンション
    hashtags: list[str] = []
    mentions: list[str] = []
    # 動画タイプ
    video_type: str = "video"  # "video", "duet", "stitch", "live"
    author_id: Optional[str] = None


class TikTokAccount(BaseModel):
    """TikTokアカウント情報"""

    id: str
    username: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    followers_count: int = 0
    following_count: int = 0
    likes_count: int = 0  # プロフィールへの総いいね数
    video_count: int = 0
    is_verified: bool = False
    is_business_account: bool = False
    created_at: Optional[datetime] = None


class TikTokEngagementMetrics(BaseModel):
    """TikTokエンゲージメント指標"""

    total_views: int = 0
    total_likes: int = 0
    total_comments: int = 0
    total_shares: int = 0
    total_saves: int = 0
    engagement_rate: float = 0.0  # (likes + comments + shares) / views * 100
    avg_views_per_video: float = 0.0
    avg_likes_per_video: float = 0.0
    avg_comments_per_video: float = 0.0
    avg_shares_per_video: float = 0.0
    view_to_like_ratio: float = 0.0  # いいね率 = likes / views * 100
    completion_rate: Optional[float] = None  # 動画完走率（ビジネスのみ）


class TikTokSoundAnalysis(BaseModel):
    """TikTokサウンド分析"""

    sound_id: str
    sound_name: str
    usage_count: int = 0
    total_views: int = 0
    total_likes: int = 0
    avg_engagement: float = 0.0
    is_trending: bool = False
    effectiveness_score: float = 0.0


class TikTokAnalysisResult(BaseModel):
    """TikTok分析結果"""

    period_start: datetime
    period_end: datetime
    total_videos: int
    metrics: TikTokEngagementMetrics
    hourly_breakdown: list[HourlyEngagement] = []
    top_performing_videos: list[TikTokVideo] = []
    recommendations: Optional[PostRecommendation] = None
    hashtag_analysis: list[HashtagAnalysis] = []
    sound_analysis: list[TikTokSoundAnalysis] = []
    content_patterns: list[ContentPattern] = []
    # TikTok固有の分析
    avg_video_duration: float = 0.0
    best_duration_range: Optional[str] = None  # "0-15s", "15-30s", "30-60s", "60s+"
    duet_performance: Optional[float] = None  # デュエット動画の平均パフォーマンス
    stitch_performance: Optional[float] = None  # スティッチ動画の平均パフォーマンス


# =============================================================================
# v1.4: YouTube対応モデル
# =============================================================================


class YouTubeVideo(BaseModel):
    """YouTube動画データモデル"""

    id: str
    title: str
    description: Optional[str] = None
    published_at: datetime
    thumbnail_url: Optional[str] = None
    duration: int = Field(ge=0, default=0)  # 秒
    # エンゲージメント指標
    views: int = Field(ge=0, default=0)
    likes: int = Field(ge=0, default=0)
    dislikes: int = Field(ge=0, default=0)  # 非公開だが一部取得可能な場合あり
    comments: int = Field(ge=0, default=0)
    # 追加指標
    favorites: Optional[int] = Field(ge=0, default=None)
    shares: Optional[int] = Field(ge=0, default=None)  # YouTube Studio経由
    watch_time_minutes: Optional[float] = None  # 総視聴時間（分）
    avg_view_duration: Optional[float] = None  # 平均視聴時間（秒）
    avg_view_percentage: Optional[float] = None  # 平均視聴率（%）
    # 動画タイプ・カテゴリ
    video_type: str = "video"  # "video", "short", "live", "premiere"
    category_id: Optional[str] = None
    tags: list[str] = []
    # チャンネル情報
    channel_id: Optional[str] = None
    channel_title: Optional[str] = None
    # URL
    video_url: Optional[str] = None


class YouTubeShort(BaseModel):
    """YouTube Shorts動画データモデル"""

    id: str
    title: str
    description: Optional[str] = None
    published_at: datetime
    thumbnail_url: Optional[str] = None
    duration: int = Field(ge=0, le=60, default=0)  # 60秒以下
    views: int = Field(ge=0, default=0)
    likes: int = Field(ge=0, default=0)
    comments: int = Field(ge=0, default=0)
    shares: Optional[int] = Field(ge=0, default=None)
    channel_id: Optional[str] = None


class YouTubeChannel(BaseModel):
    """YouTubeチャンネル情報"""

    id: str
    title: str
    description: Optional[str] = None
    custom_url: Optional[str] = None  # @ハンドル
    thumbnail_url: Optional[str] = None
    banner_url: Optional[str] = None
    country: Optional[str] = None
    published_at: Optional[datetime] = None
    # 統計情報
    subscribers_count: int = 0
    video_count: int = 0
    view_count: int = 0
    # ステータス
    is_verified: bool = False
    is_monetized: Optional[bool] = None


class YouTubeEngagementMetrics(BaseModel):
    """YouTubeエンゲージメント指標"""

    total_views: int = 0
    total_likes: int = 0
    total_comments: int = 0
    total_shares: int = 0
    engagement_rate: float = 0.0  # (likes + comments) / views * 100
    avg_views_per_video: float = 0.0
    avg_likes_per_video: float = 0.0
    avg_comments_per_video: float = 0.0
    view_to_like_ratio: float = 0.0  # いいね率 = likes / views * 100
    # 視聴パフォーマンス
    total_watch_time_hours: float = 0.0
    avg_view_duration_seconds: float = 0.0
    avg_view_percentage: float = 0.0
    # Shorts固有指標
    shorts_view_rate: float = 0.0  # Shortsの視聴比率


class YouTubePlaylist(BaseModel):
    """YouTubeプレイリスト情報"""

    id: str
    title: str
    description: Optional[str] = None
    published_at: datetime
    thumbnail_url: Optional[str] = None
    item_count: int = 0
    privacy_status: str = "public"  # "public", "private", "unlisted"
    channel_id: Optional[str] = None


class YouTubeTagAnalysis(BaseModel):
    """YouTubeタグ分析"""

    tag: str
    usage_count: int = 0
    total_views: int = 0
    total_likes: int = 0
    avg_engagement: float = 0.0
    effectiveness_score: float = 0.0


class YouTubeCategoryAnalysis(BaseModel):
    """YouTubeカテゴリ別分析"""

    category_id: str
    category_name: str
    video_count: int = 0
    total_views: int = 0
    avg_engagement: float = 0.0


class YouTubeAnalysisResult(BaseModel):
    """YouTube分析結果"""

    period_start: datetime
    period_end: datetime
    total_videos: int
    total_shorts: int = 0
    metrics: YouTubeEngagementMetrics
    hourly_breakdown: list[HourlyEngagement] = []
    top_performing_videos: list[YouTubeVideo] = []
    top_performing_shorts: list[YouTubeShort] = []
    recommendations: Optional[PostRecommendation] = None
    tag_analysis: list[YouTubeTagAnalysis] = []
    category_analysis: list[YouTubeCategoryAnalysis] = []
    content_patterns: list[ContentPattern] = []
    # YouTube固有の分析
    avg_video_duration: float = 0.0
    best_duration_range: Optional[str] = None  # "0-5min", "5-10min", "10-20min", "20min+"
    shorts_vs_video_performance: Optional[dict] = None  # Shorts vs 通常動画の比較
    live_performance: Optional[float] = None  # ライブ配信の平均パフォーマンス
