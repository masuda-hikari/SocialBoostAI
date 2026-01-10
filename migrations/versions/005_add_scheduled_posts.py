"""
005: スケジュール投稿テーブル追加

Revision ID: 005
Revises: 004
Create Date: 2026-01-11
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """スケジュール投稿テーブルを追加"""
    op.create_table(
        "scheduled_posts",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(32),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # プラットフォーム情報
        sa.Column("platform", sa.String(20), nullable=False),
        # 投稿内容
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("hashtags", sa.Text, default="[]", nullable=False),  # JSON配列
        sa.Column("media_urls", sa.Text, default="[]", nullable=False),  # JSON配列
        sa.Column("media_type", sa.String(20), nullable=True),  # image, video, none
        # スケジュール設定
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timezone", sa.String(50), default="Asia/Tokyo", nullable=False),
        # ステータス
        sa.Column(
            "status",
            sa.String(20),
            default="pending",
            nullable=False,
        ),  # pending, published, failed, cancelled
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("retry_count", sa.Integer, default=0, nullable=False),
        # メタデータ
        sa.Column("external_post_id", sa.String(255), nullable=True),  # 投稿後のID
        sa.Column("post_metadata", sa.Text, default="{}", nullable=False),  # JSON
        # タイムスタンプ
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    # インデックス
    op.create_index(
        "ix_scheduled_posts_user_id",
        "scheduled_posts",
        ["user_id"],
    )
    op.create_index(
        "ix_scheduled_posts_platform",
        "scheduled_posts",
        ["platform"],
    )
    op.create_index(
        "ix_scheduled_posts_status",
        "scheduled_posts",
        ["status"],
    )
    op.create_index(
        "ix_scheduled_posts_scheduled_at",
        "scheduled_posts",
        ["scheduled_at"],
    )
    # 複合インデックス：ペンディング投稿の高速検索用
    op.create_index(
        "ix_scheduled_posts_pending_lookup",
        "scheduled_posts",
        ["status", "scheduled_at"],
    )


def downgrade() -> None:
    """スケジュール投稿テーブルを削除"""
    op.drop_index("ix_scheduled_posts_pending_lookup", table_name="scheduled_posts")
    op.drop_index("ix_scheduled_posts_scheduled_at", table_name="scheduled_posts")
    op.drop_index("ix_scheduled_posts_status", table_name="scheduled_posts")
    op.drop_index("ix_scheduled_posts_platform", table_name="scheduled_posts")
    op.drop_index("ix_scheduled_posts_user_id", table_name="scheduled_posts")
    op.drop_table("scheduled_posts")
