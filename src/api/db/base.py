"""
SQLAlchemy データベース設定
"""

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# データベースURL（環境変数またはデフォルト）
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./socialboostai.db",
)

# SQLiteの場合のconnect_args設定
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# エンジン作成
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=os.getenv("DB_ECHO", "false").lower() == "true",
)

# セッションファクトリ
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """SQLAlchemy宣言的ベースクラス"""

    pass


def get_db() -> Generator[Session, None, None]:
    """
    データベースセッション取得（FastAPI依存性注入用）

    Yields:
        Session: データベースセッション
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    データベース初期化（テーブル作成）
    """
    Base.metadata.create_all(bind=engine)
