# -*- coding: utf-8 -*-
"""
LinkedIn分析APIのテスト
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
    """認証ヘッダーを取得（Freeプラン）"""
    # ユーザー登録
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "linkedintest@example.com",
            "password": "testpassword123",
            "username": "linkedintester",
        },
    )
    if register_response.status_code not in [201, 409]:
        pytest.fail(f"登録失敗: {register_response.json()}")

    # ログイン
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "linkedintest@example.com",
            "password": "testpassword123",
        },
    )
    if login_response.status_code != 200:
        pytest.fail(f"ログイン失敗: {login_response.json()}")

    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def pro_auth_headers(client):
    """認証ヘッダーを取得（Proプラン）"""
    # ユーザー登録
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "linkedinprotest@example.com",
            "password": "testpassword123",
            "username": "linkedinprotester",
        },
    )
    if register_response.status_code not in [201, 409]:
        pytest.fail(f"登録失敗: {register_response.json()}")

    # DBでロールをproに変更
    db = _TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "linkedinprotest@example.com").first()
        if user:
            user.role = "pro"
            db.commit()
    finally:
        db.close()

    # ログイン
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "linkedinprotest@example.com",
            "password": "testpassword123",
        },
    )
    if login_response.status_code != 200:
        pytest.fail(f"ログイン失敗: {login_response.json()}")

    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestLinkedInAnalysisAccess:
    """LinkedIn分析アクセス制御のテスト"""

    def test_free_user_cannot_access(self, client, auth_headers):
        """Freeプランユーザーはアクセスできない"""
        response = client.get("/api/v1/linkedin/analysis", headers=auth_headers)
        assert response.status_code == 403
        assert "Proプラン以上" in response.json()["detail"]

    def test_pro_user_can_access(self, client, pro_auth_headers):
        """Proプランユーザーはアクセスできる"""
        response = client.get("/api/v1/linkedin/analysis", headers=pro_auth_headers)
        assert response.status_code == 200


class TestLinkedInAnalysisCreate:
    """LinkedIn分析作成のテスト"""

    def test_create_analysis(self, client, pro_auth_headers):
        """分析を作成できる"""
        response = client.post(
            "/api/v1/linkedin/analysis",
            json={"period_days": 7},
            headers=pro_auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["platform"] == "linkedin"
        assert "summary" in data
        assert "total_posts" in data["summary"]
        assert "total_articles" in data["summary"]
        assert "click_through_rate" in data["summary"]
        assert "virality_rate" in data["summary"]

    def test_create_analysis_with_period(self, client, pro_auth_headers):
        """期間指定で分析を作成できる"""
        response = client.post(
            "/api/v1/linkedin/analysis",
            json={"period_days": 30},
            headers=pro_auth_headers,
        )
        assert response.status_code == 201


class TestLinkedInAnalysisList:
    """LinkedIn分析一覧のテスト"""

    def test_list_analyses(self, client, pro_auth_headers):
        """分析一覧を取得できる"""
        # まず分析を作成
        client.post(
            "/api/v1/linkedin/analysis",
            json={"period_days": 7},
            headers=pro_auth_headers,
        )

        # 一覧取得
        response = client.get("/api/v1/linkedin/analysis", headers=pro_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 1


class TestLinkedInAnalysisDetail:
    """LinkedIn分析詳細のテスト"""

    def test_get_analysis_detail(self, client, pro_auth_headers):
        """分析詳細を取得できる"""
        # まず分析を作成
        create_response = client.post(
            "/api/v1/linkedin/analysis",
            json={"period_days": 7},
            headers=pro_auth_headers,
        )
        analysis_id = create_response.json()["id"]

        # 詳細取得
        response = client.get(
            f"/api/v1/linkedin/analysis/{analysis_id}",
            headers=pro_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == analysis_id
        assert "hourly_breakdown" in data
        assert "daily_breakdown" in data
        assert "content_patterns" in data
        assert "media_type_performance" in data

    def test_get_nonexistent_analysis(self, client, pro_auth_headers):
        """存在しない分析は404"""
        response = client.get(
            "/api/v1/linkedin/analysis/nonexistent-id",
            headers=pro_auth_headers,
        )
        assert response.status_code == 404


class TestLinkedInAnalysisDelete:
    """LinkedIn分析削除のテスト"""

    def test_delete_analysis(self, client, pro_auth_headers):
        """分析を削除できる"""
        # まず分析を作成
        create_response = client.post(
            "/api/v1/linkedin/analysis",
            json={"period_days": 7},
            headers=pro_auth_headers,
        )
        analysis_id = create_response.json()["id"]

        # 削除
        response = client.delete(
            f"/api/v1/linkedin/analysis/{analysis_id}",
            headers=pro_auth_headers,
        )
        assert response.status_code == 204

        # 再度取得しようとすると404
        get_response = client.get(
            f"/api/v1/linkedin/analysis/{analysis_id}",
            headers=pro_auth_headers,
        )
        assert get_response.status_code == 404

    def test_delete_nonexistent_analysis(self, client, pro_auth_headers):
        """存在しない分析の削除は404"""
        response = client.delete(
            "/api/v1/linkedin/analysis/nonexistent-id",
            headers=pro_auth_headers,
        )
        assert response.status_code == 404
