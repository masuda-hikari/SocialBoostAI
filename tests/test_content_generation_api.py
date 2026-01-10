# -*- coding: utf-8 -*-
"""
AIコンテンツ生成APIのテスト - v1.6
"""

import os

# 環境変数を設定してテスト用DBを使用（インポート前に設定）
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
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
            "email": "contenttest@example.com",
            "password": "testpassword123",
            "username": "contenttester",
        },
    )
    if register_response.status_code not in [201, 409]:
        pytest.fail(f"登録失敗: {register_response.json()}")

    # ログイン
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "contenttest@example.com",
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
            "email": "contentprotest@example.com",
            "password": "testpassword123",
            "username": "contentprotester",
        },
    )
    if register_response.status_code not in [201, 409]:
        pytest.fail(f"登録失敗: {register_response.json()}")

    # DBでロールをproに変更
    db = _TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "contentprotest@example.com").first()
        if user:
            user.role = "pro"
            db.commit()
    finally:
        db.close()

    # ログイン
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "contentprotest@example.com",
            "password": "testpassword123",
        },
    )
    if login_response.status_code != 200:
        pytest.fail(f"ログイン失敗: {login_response.json()}")

    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestGenerateContentEndpoint:
    """コンテンツ生成エンドポイントのテスト"""

    def test_generate_content_requires_auth(self, client):
        """コンテンツ生成が認証を要求することを確認"""
        response = client.post(
            "/api/v1/content/generate",
            json={
                "platform": "twitter",
                "topic": "テスト",
                "tone": "casual",
                "goal": "engagement",
            },
        )
        assert response.status_code == 401

    @patch("src.api.routers.content_generation.AIContentGenerator")
    def test_generate_content_success(
        self, mock_generator_class, client, auth_headers
    ):
        """コンテンツ生成が成功することを確認"""
        mock_generator = MagicMock()
        mock_result = MagicMock()
        mock_result.id = "gen_123"
        mock_result.main_text = "テスト投稿です"
        mock_result.hashtags = ["テスト"]
        mock_result.call_to_action = None
        mock_result.media_suggestion = None
        mock_result.estimated_engagement = None
        mock_result.created_at = datetime.now(timezone.utc)
        mock_generator.generate_content.return_value = mock_result
        mock_generator_class.return_value = mock_generator

        response = client.post(
            "/api/v1/content/generate",
            json={
                "platform": "twitter",
                "content_type": "post",
                "topic": "テスト",
                "tone": "casual",
                "goal": "engagement",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "gen_123"
        assert data["main_text"] == "テスト投稿です"


class TestRewriteContentEndpoint:
    """リライトエンドポイントのテスト"""

    def test_rewrite_content_requires_auth(self, client):
        """リライトが認証を要求することを確認"""
        response = client.post(
            "/api/v1/content/rewrite",
            json={
                "original_content": "元の投稿",
                "source_platform": "twitter",
                "target_platform": "instagram",
            },
        )
        assert response.status_code == 401

    @patch("src.api.routers.content_generation.AIContentGenerator")
    def test_rewrite_content_success(
        self, mock_generator_class, client, auth_headers
    ):
        """リライトが成功することを確認"""
        mock_generator = MagicMock()
        mock_result = MagicMock()
        mock_result.id = "rewrite_123"
        mock_result.main_text = "リライトされた投稿"
        mock_result.hashtags = ["Instagram"]
        mock_result.call_to_action = None
        mock_result.media_suggestion = None
        mock_result.estimated_engagement = None
        mock_result.created_at = datetime.now(timezone.utc)
        mock_generator.rewrite_for_platform.return_value = mock_result
        mock_generator_class.return_value = mock_generator

        response = client.post(
            "/api/v1/content/rewrite",
            json={
                "original_content": "元の投稿",
                "source_platform": "twitter",
                "target_platform": "instagram",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "rewrite_123"
        assert data["main_text"] == "リライトされた投稿"


class TestABTestEndpoint:
    """A/Bテストエンドポイントのテスト"""

    def test_ab_test_requires_auth(self, client):
        """A/Bテストが認証を要求することを確認"""
        response = client.post(
            "/api/v1/content/ab-test",
            json={
                "base_topic": "テスト",
                "platform": "twitter",
            },
        )
        assert response.status_code == 401

    def test_ab_test_free_plan_forbidden(self, client, auth_headers):
        """A/BテストがFreeプランで拒否されることを確認"""
        response = client.post(
            "/api/v1/content/ab-test",
            json={
                "base_topic": "テスト",
                "platform": "twitter",
                "tone": "casual",
            },
            headers=auth_headers,
        )
        assert response.status_code == 403
        assert "Proプラン以上" in response.json()["detail"]

    @patch("src.api.routers.content_generation.AIContentGenerator")
    def test_ab_test_pro_plan_success(
        self, mock_generator_class, client, pro_auth_headers
    ):
        """A/BテストがProプランで成功することを確認"""
        mock_generator = MagicMock()
        mock_variation = MagicMock()
        mock_variation.version = "A"
        mock_variation.text = "バリエーションA"
        mock_variation.hashtags = ["テスト"]
        mock_variation.focus = "エンゲージメント"
        mock_generator.generate_ab_variations.return_value = [mock_variation]
        mock_generator_class.return_value = mock_generator

        response = client.post(
            "/api/v1/content/ab-test",
            json={
                "base_topic": "テスト",
                "platform": "twitter",
                "tone": "casual",
            },
            headers=pro_auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert "variations" in data
        assert len(data["variations"]) == 1


class TestCalendarEndpoint:
    """カレンダーエンドポイントのテスト"""

    def test_calendar_requires_auth(self, client):
        """カレンダー生成が認証を要求することを確認"""
        response = client.post(
            "/api/v1/content/calendar",
            json={
                "platforms": ["twitter"],
                "days": 7,
            },
        )
        assert response.status_code == 401

    def test_calendar_free_plan_forbidden(self, client, auth_headers):
        """カレンダー生成がFreeプランで拒否されることを確認"""
        response = client.post(
            "/api/v1/content/calendar",
            json={
                "platforms": ["twitter"],
                "days": 7,
                "topics": ["AIについて"],
                "tone": "casual",
                "goal": "engagement",
            },
            headers=auth_headers,
        )
        assert response.status_code == 403


class TestTrendingEndpoint:
    """トレンドエンドポイントのテスト"""

    def test_trending_requires_auth(self, client):
        """トレンドコンテンツ生成が認証を要求することを確認"""
        response = client.post(
            "/api/v1/content/trending",
            json={
                "platform": "twitter",
                "trend_keywords": ["AI", "ChatGPT"],
            },
        )
        assert response.status_code == 401

    def test_trending_free_plan_forbidden(self, client, auth_headers):
        """トレンドコンテンツ生成がFreeプランで拒否されることを確認"""
        response = client.post(
            "/api/v1/content/trending",
            json={
                "platform": "twitter",
                "trend_keywords": ["AI", "ChatGPT"],
                "tone": "casual",
            },
            headers=auth_headers,
        )
        assert response.status_code == 403


class TestHistoryEndpoint:
    """履歴エンドポイントのテスト"""

    def test_history_requires_auth(self, client):
        """履歴取得が認証を要求することを確認"""
        response = client.get("/api/v1/content/history")
        assert response.status_code == 401

    def test_history_success(self, client, auth_headers):
        """履歴取得が成功することを確認"""
        response = client.get(
            "/api/v1/content/history",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data


class TestDeleteHistoryEndpoint:
    """履歴削除エンドポイントのテスト"""

    def test_delete_history_requires_auth(self, client):
        """履歴削除が認証を要求することを確認"""
        response = client.delete("/api/v1/content/history/test_id")
        assert response.status_code == 401

    def test_delete_nonexistent_history(self, client, auth_headers):
        """存在しない履歴の削除で404になることを確認"""
        response = client.delete(
            "/api/v1/content/history/nonexistent_id",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestRequestValidation:
    """リクエストバリデーションのテスト"""

    def test_generate_invalid_platform(self, client, auth_headers):
        """無効なプラットフォームでエラーになることを確認"""
        response = client.post(
            "/api/v1/content/generate",
            json={
                "platform": "invalid_platform",
                "topic": "テスト",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_ab_test_invalid_variation_count(self, client, pro_auth_headers):
        """無効なバリエーション数でエラーになることを確認"""
        response = client.post(
            "/api/v1/content/ab-test",
            json={
                "base_topic": "テスト",
                "platform": "twitter",
                "variation_count": 10,  # 最大5
                "tone": "casual",
            },
            headers=pro_auth_headers,
        )
        assert response.status_code == 422

    def test_calendar_invalid_days(self, client, pro_auth_headers):
        """無効な日数でエラーになることを確認"""
        response = client.post(
            "/api/v1/content/calendar",
            json={
                "platforms": ["twitter"],
                "days": 100,  # 最大30
                "topics": ["テスト"],
                "tone": "casual",
                "goal": "engagement",
            },
            headers=pro_auth_headers,
        )
        assert response.status_code == 422

    def test_trending_empty_keywords(self, client, pro_auth_headers):
        """空のキーワードでエラーになることを確認"""
        response = client.post(
            "/api/v1/content/trending",
            json={
                "platform": "twitter",
                "trend_keywords": [],
                "tone": "casual",
            },
            headers=pro_auth_headers,
        )
        assert response.status_code == 422


class TestSchemaValidation:
    """スキーマバリデーションのテスト"""

    def test_content_platform_enum(self, client, auth_headers):
        """ContentPlatformType enumが有効な値のみ受け付けることを確認"""
        valid_platforms = ["twitter", "instagram", "tiktok", "youtube", "linkedin"]
        for platform in valid_platforms:
            response = client.post(
                "/api/v1/content/generate",
                json={"platform": platform, "topic": "テスト"},
                headers=auth_headers,
            )
            # バリデーションエラーではない（他のエラーは許容）
            if response.status_code == 422:
                assert "platform" not in str(response.json())

    def test_content_tone_enum(self, client, auth_headers):
        """ContentToneEnum が有効な値のみ受け付けることを確認"""
        valid_tones = [
            "professional",
            "casual",
            "humorous",
            "educational",
            "inspirational",
            "promotional",
        ]
        for tone in valid_tones:
            response = client.post(
                "/api/v1/content/generate",
                json={"platform": "twitter", "tone": tone, "topic": "テスト"},
                headers=auth_headers,
            )
            if response.status_code == 422:
                assert "tone" not in str(response.json())

    def test_content_goal_enum(self, client, auth_headers):
        """ContentGoalEnum が有効な値のみ受け付けることを確認"""
        valid_goals = [
            "engagement",
            "awareness",
            "conversion",
            "traffic",
            "community",
        ]
        for goal in valid_goals:
            response = client.post(
                "/api/v1/content/generate",
                json={"platform": "twitter", "goal": goal, "topic": "テスト"},
                headers=auth_headers,
            )
            if response.status_code == 422:
                assert "goal" not in str(response.json())
