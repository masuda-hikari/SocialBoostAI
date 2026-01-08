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
