"""
リアルタイムダッシュボードAPIテスト

注: このテストファイルはsetup_database fixtureを使用
"""

import json
import secrets
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.db.models import Analysis, Report
from tests.conftest import TestingSessionLocal


@pytest.fixture
def client():
    """テストクライアント"""
    return TestClient(app)


@pytest.fixture
def test_db():
    """テスト用DBセッション"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


class TestRealtimeDashboard:
    """リアルタイムダッシュボードテスト"""

    def _register_and_login(self, client):
        """ユーザー登録とログイン"""
        unique = secrets.token_hex(4)
        email = f"realtime_{unique}@example.com"

        # 登録
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "password123",
                "username": f"realtimetest_{unique}",
            },
        )
        assert response.status_code == 201
        user_data = response.json()

        # ログイン
        response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "password123"},
        )
        assert response.status_code == 200
        token = response.json()["access_token"]

        return user_data["id"], {"Authorization": f"Bearer {token}"}

    def _create_sample_data(self, user_id, db_session):
        """サンプルデータ作成"""
        now = datetime.now(timezone.utc)
        unique = secrets.token_hex(4)

        # Twitter分析
        for i in range(3):
            analysis = Analysis(
                id=f"analysis_twitter_{i}_{unique}",
                user_id=user_id,
                platform="twitter",
                period_start=now - timedelta(days=7),
                period_end=now,
                total_posts=100 + i * 10,
                total_likes=500 + i * 50,
                total_retweets=50 + i * 5,
                engagement_rate=0.05 + i * 0.01,
                best_hour=20,
                top_hashtags=json.dumps(["#python", "#tech"]),
                created_at=now - timedelta(hours=i),
            )
            db_session.add(analysis)

        # Instagram分析
        analysis = Analysis(
            id=f"analysis_instagram_{unique}",
            user_id=user_id,
            platform="instagram",
            period_start=now - timedelta(days=7),
            period_end=now,
            total_posts=50,
            total_likes=1000,
            total_retweets=100,
            engagement_rate=0.08,
            best_hour=19,
            top_hashtags=json.dumps(["#photo", "#design"]),
            created_at=now - timedelta(hours=5),
        )
        db_session.add(analysis)

        # レポート
        for i in range(2):
            report = Report(
                id=f"report_{i}_{unique}",
                user_id=user_id,
                report_type="weekly",
                platform="twitter",
                period_start=now - timedelta(days=7),
                period_end=now,
                html_url=f"/reports/report_{i}.html",
                created_at=now - timedelta(hours=i * 2),
            )
            db_session.add(report)

        db_session.commit()

    def test_get_dashboard_unauthorized(self, client):
        """未認証アクセステスト"""
        response = client.get("/api/v1/realtime/dashboard")
        assert response.status_code == 401

    def test_get_dashboard_success(self, client, test_db):
        """ダッシュボード取得成功テスト"""
        user_id, headers = self._register_and_login(client)
        self._create_sample_data(user_id, test_db)

        response = client.get("/api/v1/realtime/dashboard", headers=headers)

        assert response.status_code == 200
        data = response.json()

        assert "user_id" in data
        assert "timestamp" in data
        assert "total_analyses" in data
        assert "total_reports" in data
        assert "platforms" in data
        assert "trending_hashtags" in data
        assert "recent_activity" in data
        assert "best_posting_times" in data
        assert "week_over_week" in data

    def test_get_dashboard_with_days_param(self, client, test_db):
        """日数パラメータテスト"""
        user_id, headers = self._register_and_login(client)
        self._create_sample_data(user_id, test_db)

        response = client.get("/api/v1/realtime/dashboard?days=30", headers=headers)
        assert response.status_code == 200

    def test_get_dashboard_platforms(self, client, test_db):
        """プラットフォーム別メトリクステスト"""
        user_id, headers = self._register_and_login(client)
        self._create_sample_data(user_id, test_db)

        response = client.get("/api/v1/realtime/dashboard", headers=headers)

        assert response.status_code == 200
        data = response.json()

        platforms = {p["platform"] for p in data["platforms"]}
        assert "twitter" in platforms
        assert "instagram" in platforms

    def test_get_dashboard_trending_hashtags(self, client, test_db):
        """トレンドハッシュタグテスト"""
        user_id, headers = self._register_and_login(client)
        self._create_sample_data(user_id, test_db)

        response = client.get("/api/v1/realtime/dashboard", headers=headers)

        assert response.status_code == 200
        data = response.json()

        if data["trending_hashtags"]:
            hashtag = data["trending_hashtags"][0]
            assert "tag" in hashtag
            assert "count" in hashtag

    def test_get_dashboard_recent_activity(self, client, test_db):
        """最近のアクティビティテスト"""
        user_id, headers = self._register_and_login(client)
        self._create_sample_data(user_id, test_db)

        response = client.get("/api/v1/realtime/dashboard", headers=headers)

        assert response.status_code == 200
        data = response.json()

        if len(data["recent_activity"]) > 1:
            first_time = data["recent_activity"][0]["created_at"]
            second_time = data["recent_activity"][1]["created_at"]
            assert first_time >= second_time


class TestLiveMetrics:
    """ライブメトリクステスト"""

    def _register_and_login(self, client):
        """ユーザー登録とログイン"""
        unique = secrets.token_hex(4)
        email = f"live_{unique}@example.com"

        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "password123",
                "username": f"livetest_{unique}",
            },
        )
        assert response.status_code == 201

        response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "password123"},
        )
        assert response.status_code == 200
        token = response.json()["access_token"]

        return {"Authorization": f"Bearer {token}"}

    def test_get_live_metrics_unauthorized(self, client):
        """未認証アクセステスト"""
        response = client.get("/api/v1/realtime/live-metrics")
        assert response.status_code == 401

    def test_get_live_metrics_success(self, client):
        """ライブメトリクス取得成功テスト"""
        headers = self._register_and_login(client)

        response = client.get("/api/v1/realtime/live-metrics", headers=headers)

        assert response.status_code == 200
        data = response.json()

        assert "timestamp" in data
        assert "is_connected" in data
        assert "metrics" in data


class TestRecentActivity:
    """最近のアクティビティテスト"""

    def _register_and_login(self, client):
        """ユーザー登録とログイン"""
        unique = secrets.token_hex(4)
        email = f"activity_{unique}@example.com"

        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "password123",
                "username": f"activitytest_{unique}",
            },
        )
        assert response.status_code == 201
        user_data = response.json()

        response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "password123"},
        )
        assert response.status_code == 200
        token = response.json()["access_token"]

        return user_data["id"], {"Authorization": f"Bearer {token}"}

    def _create_sample_data(self, user_id, db_session):
        """サンプルデータ作成"""
        now = datetime.now(timezone.utc)
        unique = secrets.token_hex(4)

        for i in range(3):
            analysis = Analysis(
                id=f"act_analysis_{i}_{unique}",
                user_id=user_id,
                platform="twitter",
                period_start=now - timedelta(days=7),
                period_end=now,
                total_posts=100,
                total_likes=500,
                total_retweets=50,
                engagement_rate=0.05,
                best_hour=20,
                top_hashtags="[]",
                created_at=now - timedelta(hours=i),
            )
            db_session.add(analysis)

        for i in range(2):
            report = Report(
                id=f"act_report_{i}_{unique}",
                user_id=user_id,
                report_type="weekly",
                platform="twitter",
                period_start=now - timedelta(days=7),
                period_end=now,
                created_at=now - timedelta(hours=i * 2),
            )
            db_session.add(report)

        db_session.commit()

    def test_get_activity_unauthorized(self, client):
        """未認証アクセステスト"""
        response = client.get("/api/v1/realtime/activity")
        assert response.status_code == 401

    def test_get_activity_success(self, client, test_db):
        """アクティビティ取得成功テスト"""
        user_id, headers = self._register_and_login(client)
        self._create_sample_data(user_id, test_db)

        response = client.get("/api/v1/realtime/activity", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_activity_with_limit(self, client, test_db):
        """件数制限テスト"""
        user_id, headers = self._register_and_login(client)
        self._create_sample_data(user_id, test_db)

        response = client.get("/api/v1/realtime/activity?limit=2", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_get_activity_filter_analysis(self, client, test_db):
        """分析フィルタテスト"""
        user_id, headers = self._register_and_login(client)
        self._create_sample_data(user_id, test_db)

        response = client.get(
            "/api/v1/realtime/activity?activity_type=analysis",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert item["type"] == "analysis"

    def test_get_activity_filter_report(self, client, test_db):
        """レポートフィルタテスト"""
        user_id, headers = self._register_and_login(client)
        self._create_sample_data(user_id, test_db)

        response = client.get(
            "/api/v1/realtime/activity?activity_type=report",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert item["type"] == "report"


class TestPlatformComparison:
    """プラットフォーム比較テスト"""

    def _register_and_login(self, client):
        """ユーザー登録とログイン"""
        unique = secrets.token_hex(4)
        email = f"comparison_{unique}@example.com"

        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "password123",
                "username": f"comptest_{unique}",
            },
        )
        assert response.status_code == 201
        user_data = response.json()

        response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "password123"},
        )
        assert response.status_code == 200
        token = response.json()["access_token"]

        return user_data["id"], {"Authorization": f"Bearer {token}"}

    def _create_sample_data(self, user_id, db_session):
        """サンプルデータ作成"""
        now = datetime.now(timezone.utc)
        unique = secrets.token_hex(4)

        for platform in ["twitter", "instagram"]:
            for i in range(2):
                analysis = Analysis(
                    id=f"comp_{platform}_{i}_{unique}",
                    user_id=user_id,
                    platform=platform,
                    period_start=now - timedelta(days=7),
                    period_end=now,
                    total_posts=100,
                    total_likes=500,
                    total_retweets=50,
                    engagement_rate=0.05,
                    best_hour=20,
                    top_hashtags="[]",
                    created_at=now - timedelta(hours=i),
                )
                db_session.add(analysis)

        db_session.commit()

    def test_get_comparison_unauthorized(self, client):
        """未認証アクセステスト"""
        response = client.get("/api/v1/realtime/platform-comparison")
        assert response.status_code == 401

    def test_get_comparison_success(self, client, test_db):
        """プラットフォーム比較取得成功テスト"""
        user_id, headers = self._register_and_login(client)
        self._create_sample_data(user_id, test_db)

        response = client.get("/api/v1/realtime/platform-comparison", headers=headers)

        assert response.status_code == 200
        data = response.json()

        assert "period_days" in data
        assert "platforms" in data
        assert "winner" in data
        assert "timestamp" in data

    def test_get_comparison_with_days(self, client, test_db):
        """日数パラメータテスト"""
        user_id, headers = self._register_and_login(client)
        self._create_sample_data(user_id, test_db)

        response = client.get(
            "/api/v1/realtime/platform-comparison?days=90",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["period_days"] == 90

    def test_get_comparison_platform_data(self, client, test_db):
        """プラットフォームデータテスト"""
        user_id, headers = self._register_and_login(client)
        self._create_sample_data(user_id, test_db)

        response = client.get("/api/v1/realtime/platform-comparison", headers=headers)

        assert response.status_code == 200
        data = response.json()

        for platform in data["platforms"]:
            assert "platform" in platform
            assert "analysis_count" in platform
            assert "total_posts" in platform
            assert "engagement_rate" in platform
            assert "average" in platform["engagement_rate"]
