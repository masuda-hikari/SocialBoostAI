"""パフォーマンス最適化: インデックス追加

Revision ID: 004
Revises: 003
Create Date: 2026-01-10

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """インデックス追加"""
    # users テーブル
    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=True,
    )
    op.create_index(
        "ix_users_stripe_customer_id",
        "users",
        ["stripe_customer_id"],
        unique=True,
    )
    op.create_index(
        "ix_users_created_at",
        "users",
        ["created_at"],
        unique=False,
    )

    # tokens テーブル
    op.create_index(
        "ix_tokens_token",
        "tokens",
        ["token"],
        unique=True,
    )
    op.create_index(
        "ix_tokens_user_id",
        "tokens",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_tokens_expires_at",
        "tokens",
        ["expires_at"],
        unique=False,
    )

    # analyses テーブル
    op.create_index(
        "ix_analyses_user_id",
        "analyses",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_analyses_platform",
        "analyses",
        ["platform"],
        unique=False,
    )
    op.create_index(
        "ix_analyses_created_at",
        "analyses",
        ["created_at"],
        unique=False,
    )
    # 複合インデックス（ユーザー+プラットフォーム+作成日時）
    op.create_index(
        "ix_analyses_user_platform_created",
        "analyses",
        ["user_id", "platform", "created_at"],
        unique=False,
    )

    # reports テーブル
    op.create_index(
        "ix_reports_user_id",
        "reports",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_reports_report_type",
        "reports",
        ["report_type"],
        unique=False,
    )
    op.create_index(
        "ix_reports_platform",
        "reports",
        ["platform"],
        unique=False,
    )
    op.create_index(
        "ix_reports_created_at",
        "reports",
        ["created_at"],
        unique=False,
    )
    # 複合インデックス
    op.create_index(
        "ix_reports_user_platform_type",
        "reports",
        ["user_id", "platform", "report_type"],
        unique=False,
    )

    # subscriptions テーブル
    op.create_index(
        "ix_subscriptions_user_id",
        "subscriptions",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_subscriptions_stripe_subscription_id",
        "subscriptions",
        ["stripe_subscription_id"],
        unique=True,
    )
    op.create_index(
        "ix_subscriptions_stripe_customer_id",
        "subscriptions",
        ["stripe_customer_id"],
        unique=False,
    )
    op.create_index(
        "ix_subscriptions_status",
        "subscriptions",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_subscriptions_plan",
        "subscriptions",
        ["plan"],
        unique=False,
    )


def downgrade() -> None:
    """インデックス削除"""
    # subscriptions
    op.drop_index("ix_subscriptions_plan", table_name="subscriptions")
    op.drop_index("ix_subscriptions_status", table_name="subscriptions")
    op.drop_index("ix_subscriptions_stripe_customer_id", table_name="subscriptions")
    op.drop_index("ix_subscriptions_stripe_subscription_id", table_name="subscriptions")
    op.drop_index("ix_subscriptions_user_id", table_name="subscriptions")

    # reports
    op.drop_index("ix_reports_user_platform_type", table_name="reports")
    op.drop_index("ix_reports_created_at", table_name="reports")
    op.drop_index("ix_reports_platform", table_name="reports")
    op.drop_index("ix_reports_report_type", table_name="reports")
    op.drop_index("ix_reports_user_id", table_name="reports")

    # analyses
    op.drop_index("ix_analyses_user_platform_created", table_name="analyses")
    op.drop_index("ix_analyses_created_at", table_name="analyses")
    op.drop_index("ix_analyses_platform", table_name="analyses")
    op.drop_index("ix_analyses_user_id", table_name="analyses")

    # tokens
    op.drop_index("ix_tokens_expires_at", table_name="tokens")
    op.drop_index("ix_tokens_user_id", table_name="tokens")
    op.drop_index("ix_tokens_token", table_name="tokens")

    # users
    op.drop_index("ix_users_created_at", table_name="users")
    op.drop_index("ix_users_stripe_customer_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
