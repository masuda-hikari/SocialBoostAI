"""
008: API使用量追跡テーブル追加

Revision ID: 008
Revises: 007
Create Date: 2026-01-12
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """API使用量追跡テーブル作成"""
    # 日次使用量テーブル
    op.create_table(
        "daily_usage",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(32),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # 日付（UTC）
        sa.Column("date", sa.Date(), nullable=False),
        # 使用量カウント
        sa.Column("api_calls", sa.Integer(), default=0, nullable=False),
        sa.Column("analyses_run", sa.Integer(), default=0, nullable=False),
        sa.Column("reports_generated", sa.Integer(), default=0, nullable=False),
        sa.Column("scheduled_posts", sa.Integer(), default=0, nullable=False),
        sa.Column("ai_generations", sa.Integer(), default=0, nullable=False),
        # プラットフォーム別使用量（JSON形式）
        sa.Column(
            "platform_usage",
            sa.Text(),
            default="{}",
            nullable=False,
        ),  # {"twitter": 10, "instagram": 5, ...}
        # タイムスタンプ
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        # ユーザー+日付でユニーク
        sa.UniqueConstraint("user_id", "date", name="uq_daily_usage_user_date"),
    )

    # 月次使用量サマリーテーブル
    op.create_table(
        "monthly_usage_summary",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(32),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # 年月（YYYY-MM形式の文字列）
        sa.Column("year_month", sa.String(7), nullable=False),
        # 使用量合計
        sa.Column("total_api_calls", sa.Integer(), default=0, nullable=False),
        sa.Column("total_analyses", sa.Integer(), default=0, nullable=False),
        sa.Column("total_reports", sa.Integer(), default=0, nullable=False),
        sa.Column("total_scheduled_posts", sa.Integer(), default=0, nullable=False),
        sa.Column("total_ai_generations", sa.Integer(), default=0, nullable=False),
        # ピーク使用量
        sa.Column("peak_daily_api_calls", sa.Integer(), default=0, nullable=False),
        sa.Column("peak_date", sa.Date(), nullable=True),
        # プラットフォーム別使用量（JSON形式）
        sa.Column(
            "platform_usage",
            sa.Text(),
            default="{}",
            nullable=False,
        ),
        # タイムスタンプ
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        # ユーザー+年月でユニーク
        sa.UniqueConstraint(
            "user_id", "year_month", name="uq_monthly_usage_user_month"
        ),
    )

    # API呼び出しログテーブル（詳細ログ）
    op.create_table(
        "api_call_logs",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(32),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # リクエスト情報
        sa.Column("endpoint", sa.String(255), nullable=False),
        sa.Column("method", sa.String(10), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        # パフォーマンス情報
        sa.Column("response_time_ms", sa.Float(), nullable=True),
        # メタデータ
        sa.Column("ip_address", sa.String(45), nullable=True),  # IPv6対応
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("request_id", sa.String(36), nullable=True),  # UUID
        # タイムスタンプ
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # インデックス作成
    op.create_index(
        "ix_daily_usage_user_id",
        "daily_usage",
        ["user_id"],
    )
    op.create_index(
        "ix_daily_usage_date",
        "daily_usage",
        ["date"],
    )
    op.create_index(
        "ix_daily_usage_user_date",
        "daily_usage",
        ["user_id", "date"],
    )
    op.create_index(
        "ix_monthly_usage_summary_user_id",
        "monthly_usage_summary",
        ["user_id"],
    )
    op.create_index(
        "ix_monthly_usage_summary_year_month",
        "monthly_usage_summary",
        ["year_month"],
    )
    op.create_index(
        "ix_api_call_logs_user_id",
        "api_call_logs",
        ["user_id"],
    )
    op.create_index(
        "ix_api_call_logs_endpoint",
        "api_call_logs",
        ["endpoint"],
    )
    op.create_index(
        "ix_api_call_logs_created_at",
        "api_call_logs",
        ["created_at"],
    )
    op.create_index(
        "ix_api_call_logs_user_created",
        "api_call_logs",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    """テーブル削除"""
    op.drop_index("ix_api_call_logs_user_created")
    op.drop_index("ix_api_call_logs_created_at")
    op.drop_index("ix_api_call_logs_endpoint")
    op.drop_index("ix_api_call_logs_user_id")
    op.drop_index("ix_monthly_usage_summary_year_month")
    op.drop_index("ix_monthly_usage_summary_user_id")
    op.drop_index("ix_daily_usage_user_date")
    op.drop_index("ix_daily_usage_date")
    op.drop_index("ix_daily_usage_user_id")
    op.drop_table("api_call_logs")
    op.drop_table("monthly_usage_summary")
    op.drop_table("daily_usage")
