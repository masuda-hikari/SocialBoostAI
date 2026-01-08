"""クロスプラットフォーム比較テーブル追加

Revision ID: 003
Revises: 002
Create Date: 2026-01-09

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # cross_platform_comparisonsテーブル作成
    op.create_table(
        "cross_platform_comparisons",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(32),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("platforms_analyzed", sa.Text, default="[]", nullable=False),
        sa.Column("twitter_analysis_id", sa.String(32), nullable=True),
        sa.Column("instagram_analysis_id", sa.String(32), nullable=True),
        sa.Column("twitter_performance", sa.Text, nullable=True),
        sa.Column("instagram_performance", sa.Text, nullable=True),
        sa.Column("comparison_items", sa.Text, default="[]", nullable=False),
        sa.Column("overall_winner", sa.String(20), nullable=True),
        sa.Column("cross_platform_insights", sa.Text, default="[]", nullable=False),
        sa.Column("strategic_recommendations", sa.Text, default="[]", nullable=False),
        sa.Column("synergy_opportunities", sa.Text, default="[]", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # インデックス作成
    op.create_index(
        "ix_cross_platform_comparisons_user_id",
        "cross_platform_comparisons",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_cross_platform_comparisons_created_at",
        "cross_platform_comparisons",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_cross_platform_comparisons_created_at",
        table_name="cross_platform_comparisons",
    )
    op.drop_index(
        "ix_cross_platform_comparisons_user_id",
        table_name="cross_platform_comparisons",
    )
    op.drop_table("cross_platform_comparisons")
