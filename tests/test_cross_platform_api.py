"""
クロスプラットフォーム比較API テスト
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.db.base import get_db, Base, engine
from src.api.db.models import User, Analysis
from src.api.dependencies import get_current_user


# テスト用データベースセットアップ
@pytest.fixture(scope="function")
def test_db():
    """テスト用データベース"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
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

    def test_Freeユーザーは比較作成不可(self, client: TestClient, test_db):
        """Freeユーザーは比較を作成できない"""
        app.dependency_overrides[get_current_user] = override_current_user_free

        response = client.post(
            "/api/v1/cross-platform/comparisons",
            json={"period_days": 7},
        )

        assert response.status_code == 403
        assert "Businessプラン以上" in response.json()["detail"]

        app.dependency_overrides.clear()

    def test_Proユーザーは比較作成不可(self, client: TestClient, test_db):
        """Proユーザーは比較を作成できない"""
        app.dependency_overrides[get_current_user] = override_current_user_pro

        response = client.post(
            "/api/v1/cross-platform/comparisons",
            json={"period_days": 7},
        )

        assert response.status_code == 403
        assert "Businessプラン以上" in response.json()["detail"]

        app.dependency_overrides.clear()

    def test_Businessユーザーは比較作成可能(self, client: TestClient, test_db):
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

    def test_一覧取得_Freeユーザー(self, client: TestClient, test_db):
        """Freeユーザーは一覧取得不可"""
        app.dependency_overrides[get_current_user] = override_current_user_free

        response = client.get("/api/v1/cross-platform/comparisons")

        assert response.status_code == 403

        app.dependency_overrides.clear()

    def test_一覧取得_Businessユーザー(self, client: TestClient, test_db):
        """Businessユーザーは一覧取得可能"""
        app.dependency_overrides[get_current_user] = override_current_user_business

        response = client.get("/api/v1/cross-platform/comparisons")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

        app.dependency_overrides.clear()

    def test_一覧取得_ページネーション(self, client: TestClient, test_db):
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

    def test_存在しない比較取得(self, client: TestClient, test_db):
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

    def test_存在しない比較削除(self, client: TestClient, test_db):
        """存在しない比較の削除は404"""
        app.dependency_overrides[get_current_user] = override_current_user_business

        response = client.delete("/api/v1/cross-platform/comparisons/nonexistent_id")

        assert response.status_code == 404

        app.dependency_overrides.clear()

    def test_Freeユーザーは削除不可(self, client: TestClient, test_db):
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

    def test_期間_最小値(self, client: TestClient, test_db):
        """期間の最小値バリデーション"""
        app.dependency_overrides[get_current_user] = override_current_user_business

        response = client.post(
            "/api/v1/cross-platform/comparisons",
            json={"period_days": 0},
        )

        assert response.status_code == 422  # バリデーションエラー

        app.dependency_overrides.clear()

    def test_期間_最大値(self, client: TestClient, test_db):
        """期間の最大値バリデーション"""
        app.dependency_overrides[get_current_user] = override_current_user_business

        response = client.post(
            "/api/v1/cross-platform/comparisons",
            json={"period_days": 100},
        )

        assert response.status_code == 422  # バリデーションエラー

        app.dependency_overrides.clear()

    def test_有効な期間(self, client: TestClient, test_db):
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
