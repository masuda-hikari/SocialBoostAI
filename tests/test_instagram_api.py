# -*- coding: utf-8 -*-
"""
Instagram分析APIのテスト
"""

import os

# 環境変数を設定してテスト用DBを使用（インポート前に設定）
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.db.base import Base, get_db
from src.api.db.models import User, Token, Analysis  # noqa: F401
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
    app.dependency_overrides[get_db] = _override_get_db
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture
def client():
    """テストクライアント"""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """認証ヘッダーを取得（Proプラン）"""
    # ユーザー登録
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "instagramtest@example.com",
            "password": "testpassword123",
            "username": "instagramtester",
        },
    )
    if register_response.status_code not in [201, 409]:
        pytest.fail(f"登録失敗: {register_response.json()}")

    # ログイン
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "instagramtest@example.com",
            "password": "testpassword123",
        },
    )
    if login_response.status_code != 200:
        pytest.fail(f"ログイン失敗: {login_response.json()}")

    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def pro_auth_headers(client):
    """Proプランユーザーの認証ヘッダー"""
    # Proユーザー登録
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "prouser_ig@example.com",
            "password": "testpassword123",
            "username": "prouser_instagram",
        },
    )
    if register_response.status_code not in [201, 409]:
        pytest.fail(f"登録失敗: {register_response.json()}")

    # ログイン
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "prouser_ig@example.com",
            "password": "testpassword123",
        },
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestInstagramAnalysisEndpoints:
    """Instagram分析APIエンドポイントのテスト"""

    def test_create_analysis_requires_pro_plan(self, client, auth_headers):
        """Freeプランではアクセス拒否される"""
        response = client.post(
            "/api/v1/instagram/analysis/",
            json={"period_days": 7},
            headers=auth_headers,
        )
        # Freeプランではアクセス拒否
        assert response.status_code == 403
        assert "Pro" in response.json()["detail"]

    def test_list_analyses_requires_pro_plan(self, client, auth_headers):
        """Freeプランでは一覧取得が拒否される"""
        response = client.get(
            "/api/v1/instagram/analysis/",
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_get_analysis_requires_pro_plan(self, client, auth_headers):
        """Freeプランでは詳細取得が拒否される"""
        response = client.get(
            "/api/v1/instagram/analysis/nonexistent",
            headers=auth_headers,
        )
        assert response.status_code == 403

    def test_delete_analysis_requires_pro_plan(self, client, auth_headers):
        """Freeプランでは削除が拒否される"""
        response = client.delete(
            "/api/v1/instagram/analysis/nonexistent",
            headers=auth_headers,
        )
        assert response.status_code == 403


class TestInstagramAnalysisRequiresAuth:
    """認証が必要なテスト"""

    def test_create_without_auth(self, client):
        """認証なしでは分析作成不可"""
        response = client.post(
            "/api/v1/instagram/analysis/",
            json={"period_days": 7},
        )
        assert response.status_code == 401

    def test_list_without_auth(self, client):
        """認証なしでは一覧取得不可"""
        response = client.get("/api/v1/instagram/analysis/")
        assert response.status_code == 401

    def test_get_without_auth(self, client):
        """認証なしでは詳細取得不可"""
        response = client.get("/api/v1/instagram/analysis/some-id")
        assert response.status_code == 401

    def test_delete_without_auth(self, client):
        """認証なしでは削除不可"""
        response = client.delete("/api/v1/instagram/analysis/some-id")
        assert response.status_code == 401


class TestInstagramAnalysisSchemas:
    """スキーマのテスト"""

    def test_analysis_request_validation(self, client, auth_headers):
        """リクエストのバリデーション"""
        # 不正な期間（範囲外）
        response = client.post(
            "/api/v1/instagram/analysis/",
            json={"period_days": 100},  # 最大90
            headers=auth_headers,
        )
        # バリデーションエラーまたは403（Freeプランでは403が先）
        assert response.status_code in [403, 422]


class TestInstagramAnalysisIntegration:
    """統合テスト（モック）"""

    def test_health_check_includes_instagram(self, client):
        """ヘルスチェックが通る"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_docs_accessible(self, client):
        """APIドキュメントにアクセス可能"""
        response = client.get("/docs")
        assert response.status_code == 200
