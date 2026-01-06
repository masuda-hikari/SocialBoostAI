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
