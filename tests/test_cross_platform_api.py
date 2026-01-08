"""
クロスプラットフォーム比較API テスト
"""

import os

# 環境変数を設定してテスト用DBを使用（インポート前に設定）
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.db.base import Base, get_db
from src.api.db.models import CrossPlatformComparison, User  # noqa: F401
from src.api.dependencies import get_current_user
from src.api.main import app

# テスト用のSQLiteデータベース（独自エンジン）
_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

_TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


def _override_get_db():
    """テスト用データベースセッション"""
    db = _TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_test_db():
    """各テスト関数の前にデータベースをセットアップ"""
    # 依存性をオーバーライド
    app.dependency_overrides[get_db] = _override_get_db
    # テーブル作成
    Base.metadata.create_all(bind=_test_engine)
    yield
    # テーブル削除
    Base.metadata.drop_all(bind=_test_engine)
    # オーバーライドをクリア（get_current_userのオーバーライドは個別テストで管理）


@pytest.fixture
def client():
    """テストクライアント"""
    return TestClient(app)


# =============================================================================
# モックユーザー
# =============================================================================


def create_mock_user(role: str = "business") -> User:
    """モックユーザー作成"""
    return User(
        id="test_user_123",
        email="test@example.com",
        username="testuser",
        password_hash="hashed",
        role=role,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def override_current_user_business():
    """Businessユーザーとして認証をオーバーライド"""
    return create_mock_user("business")


def override_current_user_free():
    """Freeユーザーとして認証をオーバーライド"""
    return create_mock_user("free")


def override_current_user_pro():
    """Proユーザーとして認証をオーバーライド"""
    return create_mock_user("pro")


# =============================================================================
# プラン制限テスト
# =============================================================================


class TestComparisonPlanRestrictions:
    """プラン制限テスト"""

    def test_Freeユーザーは比較作成不可(self, client: TestClient):
        """Freeユーザーは比較を作成できない"""
        app.dependency_overrides[get_current_user] = override_current_user_free

        response = client.post(
            "/api/v1/cross-platform/comparisons",
            json={"period_days": 7},
        )

        assert response.status_code == 403
        assert "Businessプラン以上" in response.json()["detail"]

        app.dependency_overrides.clear()

    def test_Proユーザーは比較作成不可(self, client: TestClient):
        """Proユーザーは比較を作成できない"""
        app.dependency_overrides[get_current_user] = override_current_user_pro

        response = client.post(
            "/api/v1/cross-platform/comparisons",
            json={"period_days": 7},
        )

        assert response.status_code == 403
        assert "Businessプラン以上" in response.json()["detail"]

        app.dependency_overrides.clear()

    def test_Businessユーザーは比較作成可能(self, client: TestClient):
        """Businessユーザーは比較を作成できる（ただしデータなしでエラー）"""
        app.dependency_overrides[get_current_user] = override_current_user_business

        response = client.post(
            "/api/v1/cross-platform/comparisons",
            json={"period_days": 7},
        )

        # データがないので400エラー
        assert response.status_code == 400
        assert "分析データが必要" in response.json()["detail"]

        app.dependency_overrides.clear()


# =============================================================================
# 比較一覧APIテスト
# =============================================================================


class TestComparisonListAPI:
    """比較一覧APIテスト"""

    def test_一覧取得_Freeユーザー(self, client: TestClient):
        """Freeユーザーは一覧取得不可"""
        app.dependency_overrides[get_current_user] = override_current_user_free

        response = client.get("/api/v1/cross-platform/comparisons")

        assert response.status_code == 403

        app.dependency_overrides.clear()

    def test_一覧取得_Businessユーザー(self, client: TestClient):
        """Businessユーザーは一覧取得可能"""
        app.dependency_overrides[get_current_user] = override_current_user_business

        response = client.get("/api/v1/cross-platform/comparisons")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

        app.dependency_overrides.clear()

    def test_一覧取得_ページネーション(self, client: TestClient):
        """ページネーションパラメータ"""
        app.dependency_overrides[get_current_user] = override_current_user_business

        response = client.get(
            "/api/v1/cross-platform/comparisons",
            params={"page": 1, "per_page": 10},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 10

        app.dependency_overrides.clear()


# =============================================================================
# 比較詳細APIテスト
# =============================================================================


class TestComparisonDetailAPI:
    """比較詳細APIテスト"""

    def test_存在しない比較取得(self, client: TestClient):
        """存在しない比較は404"""
        app.dependency_overrides[get_current_user] = override_current_user_business

        response = client.get("/api/v1/cross-platform/comparisons/nonexistent_id")

        assert response.status_code == 404

        app.dependency_overrides.clear()


# =============================================================================
# 比較削除APIテスト
# =============================================================================


class TestComparisonDeleteAPI:
    """比較削除APIテスト"""

    def test_存在しない比較削除(self, client: TestClient):
        """存在しない比較の削除は404"""
        app.dependency_overrides[get_current_user] = override_current_user_business

        response = client.delete("/api/v1/cross-platform/comparisons/nonexistent_id")

        assert response.status_code == 404

        app.dependency_overrides.clear()

    def test_Freeユーザーは削除不可(self, client: TestClient):
        """Freeユーザーは削除できない"""
        app.dependency_overrides[get_current_user] = override_current_user_free

        response = client.delete("/api/v1/cross-platform/comparisons/any_id")

        assert response.status_code == 403

        app.dependency_overrides.clear()


# =============================================================================
# リクエストバリデーションテスト
# =============================================================================


class TestComparisonRequestValidation:
    """リクエストバリデーションテスト"""

    def test_期間_最小値(self, client: TestClient):
        """期間の最小値バリデーション"""
        app.dependency_overrides[get_current_user] = override_current_user_business

        response = client.post(
            "/api/v1/cross-platform/comparisons",
            json={"period_days": 0},
        )

        assert response.status_code == 422  # バリデーションエラー

        app.dependency_overrides.clear()

    def test_期間_最大値(self, client: TestClient):
        """期間の最大値バリデーション"""
        app.dependency_overrides[get_current_user] = override_current_user_business

        response = client.post(
            "/api/v1/cross-platform/comparisons",
            json={"period_days": 100},
        )

        assert response.status_code == 422  # バリデーションエラー

        app.dependency_overrides.clear()

    def test_有効な期間(self, client: TestClient):
        """有効な期間でリクエスト"""
        app.dependency_overrides[get_current_user] = override_current_user_business

        response = client.post(
            "/api/v1/cross-platform/comparisons",
            json={"period_days": 30},
        )

        # データなしで400だが、バリデーションは通る
        assert response.status_code == 400
        assert "分析データが必要" in response.json()["detail"]

        app.dependency_overrides.clear()
