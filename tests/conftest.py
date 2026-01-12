"""
テスト設定 - データベースセットアップ
"""

import os

# 環境変数を設定してテスト用DBを使用（インポート前に設定）
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
# テスト環境ではレート制限を無効化
os.environ["RATE_LIMIT_ENABLED"] = "false"
# テスト環境ではCSRF保護を無効化
os.environ["CSRF_ENABLED"] = "false"

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.db.base import Base, get_db
from src.api.db.models import (  # noqa: F401
    Analysis,
    ApiCallLog,
    CrossPlatformComparison,
    DailyUsage,
    MonthlyUsageSummary,
    PushNotificationLog,
    PushSubscription,
    Report,
    ScheduledPost,
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


@pytest.fixture
def test_user(db_session):
    """テスト用ユーザー"""
    from datetime import datetime, timezone
    import secrets
    import bcrypt

    password_hash = bcrypt.hashpw("testpassword123".encode(), bcrypt.gensalt()).decode()
    user = User(
        id=f"user_{secrets.token_hex(8)}",
        email="test@example.com",
        username="testuser",
        password_hash=password_hash,
        role="free",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_pro(db_session):
    """Pro版テスト用ユーザー"""
    from datetime import datetime, timezone
    import secrets
    import bcrypt

    password_hash = bcrypt.hashpw("testpassword123".encode(), bcrypt.gensalt()).decode()
    user = User(
        id=f"user_{secrets.token_hex(8)}",
        email="pro@example.com",
        username="prouser",
        password_hash=password_hash,
        role="pro",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_business(db_session):
    """Business版テスト用ユーザー"""
    from datetime import datetime, timezone
    import secrets
    import bcrypt

    password_hash = bcrypt.hashpw("testpassword123".encode(), bcrypt.gensalt()).decode()
    user = User(
        id=f"user_{secrets.token_hex(8)}",
        email="business@example.com",
        username="businessuser",
        password_hash=password_hash,
        role="business",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def client():
    """テストクライアント"""
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture
def auth_token(db_session, test_user):
    """認証トークン（Free版）"""
    from datetime import datetime, timedelta, timezone
    import secrets

    token_str = secrets.token_hex(32)
    token = Token(
        token=token_str,
        user_id=test_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(token)
    db_session.commit()
    return token_str


@pytest.fixture
def auth_headers_free(auth_token):
    """認証ヘッダー（Free版）"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def auth_token_pro(db_session, test_user_pro):
    """認証トークン（Pro版）"""
    from datetime import datetime, timedelta, timezone
    import secrets

    token_str = secrets.token_hex(32)
    token = Token(
        token=token_str,
        user_id=test_user_pro.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(token)
    db_session.commit()
    return token_str


@pytest.fixture
def auth_headers_pro(auth_token_pro):
    """認証ヘッダー（Pro版）"""
    return {"Authorization": f"Bearer {auth_token_pro}"}


@pytest.fixture
def auth_token_business(db_session, test_user_business):
    """認証トークン（Business版）"""
    from datetime import datetime, timedelta, timezone
    import secrets

    token_str = secrets.token_hex(32)
    token = Token(
        token=token_str,
        user_id=test_user_business.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(token)
    db_session.commit()
    return token_str


@pytest.fixture
def auth_headers_business(auth_token_business):
    """認証ヘッダー（Business版）"""
    return {"Authorization": f"Bearer {auth_token_business}"}


# 互換性用エイリアス（一部テストファイルで使用）
@pytest.fixture
def auth_headers(auth_token):
    """認証ヘッダー（Free版のエイリアス）"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def admin_user(db_session):
    """管理者テスト用ユーザー"""
    from datetime import datetime, timezone
    import secrets
    import bcrypt

    password_hash = bcrypt.hashpw("adminpassword123".encode(), bcrypt.gensalt()).decode()
    user = User(
        id=f"user_{secrets.token_hex(8)}",
        email="admin@example.com",
        username="adminuser",
        password_hash=password_hash,
        role="admin",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(db_session, admin_user):
    """管理者認証トークン"""
    from datetime import datetime, timedelta, timezone
    import secrets

    token_str = secrets.token_hex(32)
    token = Token(
        token=token_str,
        user_id=admin_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(token)
    db_session.commit()
    return token_str


@pytest.fixture
def admin_headers(admin_token):
    """管理者認証ヘッダー"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def authenticated_client(client, auth_headers):
    """認証済みテストクライアント"""
    client.headers.update(auth_headers)
    return client
