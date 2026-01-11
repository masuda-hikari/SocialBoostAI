"""
006: ユーザーオンボーディングフィールド追加

Revision ID: 006
Revises: 005
Create Date: 2026-01-11
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """ユーザーテーブルにオンボーディングフィールドを追加"""
    # オンボーディング完了フラグ
    op.add_column(
        "users",
        sa.Column(
            "onboarding_completed",
            sa.Boolean,
            default=False,
            nullable=False,
            server_default="0",
        ),
    )
    # オンボーディングステップ（JSON: 完了したステップを記録）
    op.add_column(
        "users",
        sa.Column(
            "onboarding_steps",
            sa.Text,
            default="{}",
            nullable=False,
            server_default="{}",
        ),
    )
    # オンボーディング開始日時
    op.add_column(
        "users",
        sa.Column(
            "onboarding_started_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    # オンボーディング完了日時
    op.add_column(
        "users",
        sa.Column(
            "onboarding_completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """オンボーディングフィールドを削除"""
    op.drop_column("users", "onboarding_completed_at")
    op.drop_column("users", "onboarding_started_at")
    op.drop_column("users", "onboarding_steps")
    op.drop_column("users", "onboarding_completed")
