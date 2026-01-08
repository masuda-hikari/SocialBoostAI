"""サブスクリプションテーブル追加

Revision ID: 002
Revises: 001
Create Date: 2026-01-08

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # usersテーブルにstripe_customer_idカラム追加
    op.add_column(
        "users",
        sa.Column("stripe_customer_id", sa.String(255), unique=True, nullable=True),
    )

    # subscriptionsテーブル作成
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(32),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "stripe_subscription_id", sa.String(255), unique=True, nullable=False
        ),
        sa.Column("stripe_customer_id", sa.String(255), nullable=False),
        sa.Column("plan", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), default="active", nullable=False),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cancel_at_period_end", sa.Boolean, default=False, nullable=False),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # インデックス作成
    op.create_index(
        "ix_subscriptions_user_id", "subscriptions", ["user_id"], unique=False
    )
    op.create_index(
        "ix_subscriptions_status", "subscriptions", ["status"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_subscriptions_status", table_name="subscriptions")
    op.drop_index("ix_subscriptions_user_id", table_name="subscriptions")
    op.drop_table("subscriptions")
    op.drop_column("users", "stripe_customer_id")
