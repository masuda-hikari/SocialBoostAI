"""
Alembic マイグレーション環境設定
"""

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# モデルのインポート
from src.api.db.base import Base
from src.api.db.models import Analysis, Report, Token, User  # noqa: F401

# Alembic Config オブジェクト
config = context.config

# ログ設定
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# メタデータ（自動生成用）
target_metadata = Base.metadata


def get_url() -> str:
    """データベースURL取得（環境変数優先）"""
    return os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))


def run_migrations_offline() -> None:
    """
    オフラインマイグレーション実行（SQL生成のみ）
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    オンラインマイグレーション実行（DB接続）
    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
