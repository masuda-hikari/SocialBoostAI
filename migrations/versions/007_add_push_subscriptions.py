"""
007: プッシュ通知サブスクリプションテーブル追加

Revision ID: 007
Revises: 006
Create Date: 2026-01-11
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """プッシュ通知サブスクリプションテーブル作成"""
    op.create_table(
        "push_subscriptions",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(32),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Web Push サブスクリプション情報
        sa.Column("endpoint", sa.Text(), nullable=False, unique=True),
        sa.Column("p256dh_key", sa.String(255), nullable=False),  # 公開鍵
        sa.Column("auth_key", sa.String(255), nullable=False),  # 認証秘密
        # デバイス情報
        sa.Column("device_type", sa.String(50), nullable=True),  # desktop/mobile/tablet
        sa.Column("browser", sa.String(50), nullable=True),  # chrome/firefox/safari等
        sa.Column("os", sa.String(50), nullable=True),  # windows/macos/android/ios
        sa.Column("device_name", sa.String(100), nullable=True),  # ユーザー識別用名前
        # 通知設定
        sa.Column("enabled", sa.Boolean(), default=True, nullable=False),
        sa.Column(
            "notification_types",
            sa.Text(),
            default="[]",
            nullable=False,
        ),  # JSON配列: 受信する通知タイプ
        # タイムスタンプ
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
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
    )

    # 通知履歴テーブル
    op.create_table(
        "push_notification_logs",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(32),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "subscription_id",
            sa.String(32),
            sa.ForeignKey("push_subscriptions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # 通知内容
        sa.Column("notification_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("data", sa.Text(), default="{}", nullable=False),  # JSON
        sa.Column("icon", sa.String(255), nullable=True),
        sa.Column("url", sa.String(500), nullable=True),  # クリック時の遷移先
        # ステータス
        sa.Column(
            "status", sa.String(20), default="pending", nullable=False
        ),  # pending/sent/failed/clicked
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("clicked_at", sa.DateTime(timezone=True), nullable=True),
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
        "ix_push_subscriptions_user_id",
        "push_subscriptions",
        ["user_id"],
    )
    op.create_index(
        "ix_push_subscriptions_endpoint",
        "push_subscriptions",
        ["endpoint"],
        unique=True,
    )
    op.create_index(
        "ix_push_subscriptions_enabled",
        "push_subscriptions",
        ["enabled"],
    )
    op.create_index(
        "ix_push_notification_logs_user_id",
        "push_notification_logs",
        ["user_id"],
    )
    op.create_index(
        "ix_push_notification_logs_subscription_id",
        "push_notification_logs",
        ["subscription_id"],
    )
    op.create_index(
        "ix_push_notification_logs_notification_type",
        "push_notification_logs",
        ["notification_type"],
    )
    op.create_index(
        "ix_push_notification_logs_status",
        "push_notification_logs",
        ["status"],
    )
    op.create_index(
        "ix_push_notification_logs_created_at",
        "push_notification_logs",
        ["created_at"],
    )


def downgrade() -> None:
    """テーブル削除"""
    op.drop_index("ix_push_notification_logs_created_at")
    op.drop_index("ix_push_notification_logs_status")
    op.drop_index("ix_push_notification_logs_notification_type")
    op.drop_index("ix_push_notification_logs_subscription_id")
    op.drop_index("ix_push_notification_logs_user_id")
    op.drop_index("ix_push_subscriptions_enabled")
    op.drop_index("ix_push_subscriptions_endpoint")
    op.drop_index("ix_push_subscriptions_user_id")
    op.drop_table("push_notification_logs")
    op.drop_table("push_subscriptions")
