"""
SQLAlchemy データベースモデル
"""

import secrets
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def _generate_id(prefix: str = "") -> str:
    """ユニークID生成"""
    return f"{prefix}{secrets.token_hex(8)}"


def _now_utc() -> datetime:
    """UTC現在時刻"""
    return datetime.now(timezone.utc)


class User(Base):
    """ユーザーテーブル"""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=lambda: _generate_id("user_"),
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(20),
        default="free",
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    stripe_customer_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True
    )
    # オンボーディング関連
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    onboarding_steps: Mapped[str] = mapped_column(
        Text, default="{}", nullable=False
    )  # JSON形式
    onboarding_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    onboarding_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now_utc,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now_utc,
        onupdate=_now_utc,
        nullable=False,
    )

    # リレーション
    analyses: Mapped[list["Analysis"]] = relationship(
        "Analysis",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    reports: Mapped[list["Report"]] = relationship(
        "Report",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    tokens: Mapped[list["Token"]] = relationship(
        "Token",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    scheduled_posts: Mapped[list["ScheduledPost"]] = relationship(
        "ScheduledPost",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    push_subscriptions: Mapped[list["PushSubscription"]] = relationship(
        "PushSubscription",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    push_notification_logs: Mapped[list["PushNotificationLog"]] = relationship(
        "PushNotificationLog",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Token(Base):
    """認証トークンテーブル"""

    __tablename__ = "tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    user_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now_utc,
        nullable=False,
    )

    # リレーション
    user: Mapped["User"] = relationship("User", back_populates="tokens")


class Analysis(Base):
    """分析結果テーブル"""

    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=lambda: _generate_id("analysis_"),
    )
    user_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    platform: Mapped[str] = mapped_column(String(50), default="twitter", nullable=False)
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # サマリーデータ（JSON形式で保存）
    total_posts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_likes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_retweets: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    engagement_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    best_hour: Mapped[int | None] = mapped_column(Integer, nullable=True)
    top_hashtags: Mapped[str] = mapped_column(
        Text,
        default="[]",
        nullable=False,
    )  # JSON配列文字列

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now_utc,
        nullable=False,
    )

    # リレーション
    user: Mapped["User"] = relationship("User", back_populates="analyses")


class Report(Base):
    """レポートテーブル"""

    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=lambda: _generate_id("report_"),
    )
    user_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    report_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # weekly, monthly, custom
    platform: Mapped[str] = mapped_column(String(50), default="twitter", nullable=False)
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    html_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now_utc,
        nullable=False,
    )

    # リレーション
    user: Mapped["User"] = relationship("User", back_populates="reports")


class Subscription(Base):
    """サブスクリプションテーブル"""

    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=lambda: _generate_id("sub_"),
    )
    user_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    stripe_subscription_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    stripe_customer_id: Mapped[str] = mapped_column(String(255), nullable=False)
    plan: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # free, pro, business, enterprise
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False,
    )  # active, canceled, past_due, trialing
    current_period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    current_period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    canceled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now_utc,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now_utc,
        onupdate=_now_utc,
        nullable=False,
    )

    # リレーション
    user: Mapped["User"] = relationship("User", back_populates="subscriptions")


class ScheduledPost(Base):
    """スケジュール投稿テーブル"""

    __tablename__ = "scheduled_posts"

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=lambda: _generate_id("sched_"),
    )
    user_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # プラットフォーム情報
    platform: Mapped[str] = mapped_column(String(20), nullable=False)

    # 投稿内容
    content: Mapped[str] = mapped_column(Text, nullable=False)
    hashtags: Mapped[str] = mapped_column(Text, default="[]", nullable=False)  # JSON配列
    media_urls: Mapped[str] = mapped_column(
        Text, default="[]", nullable=False
    )  # JSON配列
    media_type: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # image, video, none

    # スケジュール設定
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    timezone: Mapped[str] = mapped_column(
        String(50), default="Asia/Tokyo", nullable=False
    )

    # ステータス
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )  # pending, published, failed, cancelled
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # メタデータ
    external_post_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # 投稿後のID
    post_metadata: Mapped[str] = mapped_column(Text, default="{}", nullable=False)  # JSON

    # タイムスタンプ
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now_utc,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now_utc,
        onupdate=_now_utc,
        nullable=False,
    )

    # リレーション
    user: Mapped["User"] = relationship("User", back_populates="scheduled_posts")


class PushSubscription(Base):
    """プッシュ通知サブスクリプションテーブル"""

    __tablename__ = "push_subscriptions"

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=lambda: _generate_id("push_"),
    )
    user_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Web Push サブスクリプション情報
    endpoint: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    p256dh_key: Mapped[str] = mapped_column(String(255), nullable=False)
    auth_key: Mapped[str] = mapped_column(String(255), nullable=False)
    # デバイス情報
    device_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    browser: Mapped[str | None] = mapped_column(String(50), nullable=True)
    os: Mapped[str | None] = mapped_column(String(50), nullable=True)
    device_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 通知設定
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notification_types: Mapped[str] = mapped_column(
        Text, default="[]", nullable=False
    )  # JSON配列
    # タイムスタンプ
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now_utc,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now_utc,
        onupdate=_now_utc,
        nullable=False,
    )

    # リレーション
    user: Mapped["User"] = relationship("User", back_populates="push_subscriptions")
    notification_logs: Mapped[list["PushNotificationLog"]] = relationship(
        "PushNotificationLog",
        back_populates="subscription",
        cascade="all, delete-orphan",
    )


class PushNotificationLog(Base):
    """プッシュ通知ログテーブル"""

    __tablename__ = "push_notification_logs"

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=lambda: _generate_id("notif_"),
    )
    user_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    subscription_id: Mapped[str | None] = mapped_column(
        String(32),
        ForeignKey("push_subscriptions.id", ondelete="SET NULL"),
        nullable=True,
    )
    # 通知内容
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    data: Mapped[str] = mapped_column(Text, default="{}", nullable=False)  # JSON
    icon: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # ステータス
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )  # pending/sent/failed/clicked
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    clicked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # タイムスタンプ
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now_utc,
        nullable=False,
    )

    # リレーション
    user: Mapped["User"] = relationship("User", back_populates="push_notification_logs")
    subscription: Mapped["PushSubscription"] = relationship(
        "PushSubscription", back_populates="notification_logs"
    )


class CrossPlatformComparison(Base):
    """クロスプラットフォーム比較テーブル"""

    __tablename__ = "cross_platform_comparisons"

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=lambda: _generate_id("comparison_"),
    )
    user_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    platforms_analyzed: Mapped[str] = mapped_column(
        Text, default="[]", nullable=False
    )  # JSON配列
    twitter_analysis_id: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )
    instagram_analysis_id: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )
    # パフォーマンスデータ（JSON形式）
    twitter_performance: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON
    instagram_performance: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON
    comparison_items: Mapped[str] = mapped_column(
        Text, default="[]", nullable=False
    )  # JSON配列
    overall_winner: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # twitter, instagram, tie
    cross_platform_insights: Mapped[str] = mapped_column(
        Text, default="[]", nullable=False
    )  # JSON配列
    strategic_recommendations: Mapped[str] = mapped_column(
        Text, default="[]", nullable=False
    )  # JSON配列
    synergy_opportunities: Mapped[str] = mapped_column(
        Text, default="[]", nullable=False
    )  # JSON配列
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now_utc,
        nullable=False,
    )


class DailyUsage(Base):
    """日次使用量テーブル"""

    __tablename__ = "daily_usage"

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=lambda: _generate_id("usage_"),
    )
    user_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    # 使用量カウント
    api_calls: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    analyses_run: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reports_generated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    scheduled_posts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ai_generations: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # プラットフォーム別使用量（JSON形式）
    platform_usage: Mapped[str] = mapped_column(
        Text, default="{}", nullable=False
    )  # JSON
    # タイムスタンプ
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now_utc,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now_utc,
        onupdate=_now_utc,
        nullable=False,
    )


class MonthlyUsageSummary(Base):
    """月次使用量サマリーテーブル"""

    __tablename__ = "monthly_usage_summary"

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=lambda: _generate_id("musage_"),
    )
    user_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    year_month: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
    )  # YYYY-MM形式
    # 使用量合計
    total_api_calls: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_analyses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_reports: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_scheduled_posts: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    total_ai_generations: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    # ピーク使用量
    peak_daily_api_calls: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    peak_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # プラットフォーム別使用量（JSON形式）
    platform_usage: Mapped[str] = mapped_column(
        Text, default="{}", nullable=False
    )  # JSON
    # タイムスタンプ
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now_utc,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now_utc,
        onupdate=_now_utc,
        nullable=False,
    )


class ApiCallLog(Base):
    """API呼び出しログテーブル"""

    __tablename__ = "api_call_logs"

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=lambda: _generate_id("log_"),
    )
    user_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # リクエスト情報
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    # パフォーマンス情報
    response_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    # メタデータ
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    # タイムスタンプ
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now_utc,
        nullable=False,
    )
