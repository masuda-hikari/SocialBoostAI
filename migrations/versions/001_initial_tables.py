"""初期テーブル作成

Revision ID: 001
Revises:
Create Date: 2026-01-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Revision 識別子
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """アップグレード処理"""
    # users テーブル
    op.create_table(
        "users",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, default="free"),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # tokens テーブル
    op.create_table(
        "tokens",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("token", sa.String(64), unique=True, nullable=False),
        sa.Column(
            "user_id",
            sa.String(32),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tokens_token", "tokens", ["token"])
    op.create_index("ix_tokens_user_id", "tokens", ["user_id"])

    # analyses テーブル
    op.create_table(
        "analyses",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(32),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("platform", sa.String(50), nullable=False, default="twitter"),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_posts", sa.Integer, nullable=False, default=0),
        sa.Column("total_likes", sa.Integer, nullable=False, default=0),
        sa.Column("total_retweets", sa.Integer, nullable=False, default=0),
        sa.Column("engagement_rate", sa.Float, nullable=False, default=0.0),
        sa.Column("best_hour", sa.Integer, nullable=True),
        sa.Column("top_hashtags", sa.Text, nullable=False, default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_analyses_user_id", "analyses", ["user_id"])

    # reports テーブル
    op.create_table(
        "reports",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(32),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("report_type", sa.String(20), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False, default="twitter"),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("html_url", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_reports_user_id", "reports", ["user_id"])


def downgrade() -> None:
    """ダウングレード処理"""
    op.drop_table("reports")
    op.drop_table("analyses")
    op.drop_table("tokens")
    op.drop_table("users")
