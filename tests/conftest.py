"""
テスト設定 - データベースセットアップ
"""

import os

# 環境変数を設定してテスト用DBを使用（インポート前に設定）
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.db.base import Base, get_db
from src.api.db.models import (  # noqa: F401
    Analysis,
    CrossPlatformComparison,
    Report,
    Subscription,
    Token,
    User,
)
from src.api.main import app

# テスト用のSQLiteデータベース（インメモリ、StaticPoolで接続維持）
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


# 同一接続を維持するためのイベントリスナー
@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """外部キー制約を有効化"""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """テスト用データベースセッション"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# 依存性をオーバーライド
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """
    各テスト関数の前にデータベースを作成し、後にクリーンアップ
    """
    # 依存性オーバーライドを再設定（他テストファイルで上書きされた場合の対策）
    app.dependency_overrides[get_db] = override_get_db

    # テーブル作成
    Base.metadata.create_all(bind=test_engine)

    # WebSocketシングルトンをリセット（テスト間で干渉しないように）
    try:
        import src.api.websocket.connection_manager as cm_module
        import src.api.websocket.service as svc_module
        cm_module._connection_manager = None
        svc_module._notification_service = None
    except ImportError:
        pass  # WebSocketモジュールがない場合は無視

    yield

    # テーブル削除（全データクリア）
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    """テスト用データベースセッション"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
