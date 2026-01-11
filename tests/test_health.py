"""
ヘルスチェックエンドポイントテスト
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.routers.health import (
    ComponentHealth,
    check_database_health,
    check_disk_health,
    check_redis_health,
    get_overall_status,
)


@pytest.fixture
def client():
    """テストクライアント"""
    return TestClient(app)


class TestHealthEndpoint:
    """基本ヘルスチェックエンドポイントテスト"""

    def test_health_check_success(self, client):
        """ヘルスチェック成功"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "SocialBoostAI"
        assert data["version"] == "2.6.0"
        assert "timestamp" in data

    def test_health_returns_correct_fields(self, client):
        """必要なフィールドが含まれる"""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "service" in data
        assert "timestamp" in data


class TestDetailedHealthEndpoint:
    """詳細ヘルスチェックエンドポイントテスト"""

    def test_detailed_health_check(self, client):
        """詳細ヘルスチェック成功"""
        response = client.get("/health/detailed")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "components" in data
        assert "uptime_seconds" in data
        assert "environment" in data

    def test_detailed_health_includes_database(self, client):
        """データベースコンポーネントが含まれる"""
        response = client.get("/health/detailed")
        data = response.json()

        assert "database" in data["components"]
        assert "status" in data["components"]["database"]

    def test_detailed_health_includes_disk(self, client):
        """ディスクコンポーネントが含まれる"""
        response = client.get("/health/detailed")
        data = response.json()

        assert "disk" in data["components"]
        assert "status" in data["components"]["disk"]


class TestReadinessProbe:
    """Readiness Probeテスト"""

    def test_readiness_check(self, client):
        """Readiness Probe成功"""
        response = client.get("/health/ready")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ready"


class TestLivenessProbe:
    """Liveness Probeテスト"""

    def test_liveness_check(self, client):
        """Liveness Probe成功"""
        response = client.get("/health/live")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "alive"


class TestRootEndpoint:
    """ルートエンドポイントテスト"""

    def test_root_returns_info(self, client):
        """ルートエンドポイントが情報を返す"""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "SocialBoostAI API"
        assert "docs" in data
        assert "health" in data


class TestCheckDatabaseHealth:
    """データベースヘルスチェック関数テスト"""

    def test_database_health_returns_component_health(self, client):
        """ComponentHealthが返される"""
        # DBセッションを取得してテスト
        from src.api.db import get_db
        db = next(get_db())
        try:
            result = check_database_health(db)
            assert isinstance(result, ComponentHealth)
            assert result.status in ("healthy", "degraded", "unhealthy")
        finally:
            db.close()


class TestCheckDiskHealth:
    """ディスクヘルスチェック関数テスト"""

    def test_disk_health_returns_tuple(self):
        """タプル（健全性, ディスク情報）が返される"""
        health, disk_info = check_disk_health()

        assert isinstance(health, ComponentHealth)
        assert health.status in ("healthy", "degraded", "unhealthy")

        assert isinstance(disk_info, dict)
        if disk_info:
            assert "total_gb" in disk_info
            assert "used_gb" in disk_info
            assert "free_gb" in disk_info
            assert "percent_used" in disk_info


class TestCheckRedisHealth:
    """Redisヘルスチェック関数テスト"""

    def test_redis_health_without_config(self, monkeypatch):
        """Redis未設定時はhealthy"""
        monkeypatch.delenv("REDIS_URL", raising=False)
        result = check_redis_health()

        assert isinstance(result, ComponentHealth)
        assert result.status == "healthy"
        assert "未設定" in result.message


class TestGetOverallStatus:
    """全体ステータス判定テスト"""

    def test_all_healthy(self):
        """全コンポーネントhealthy時はhealthy"""
        components = {
            "db": ComponentHealth(status="healthy"),
            "redis": ComponentHealth(status="healthy"),
            "disk": ComponentHealth(status="healthy"),
        }
        assert get_overall_status(components) == "healthy"

    def test_one_degraded(self):
        """1つがdegraded時はdegraded"""
        components = {
            "db": ComponentHealth(status="healthy"),
            "redis": ComponentHealth(status="degraded"),
            "disk": ComponentHealth(status="healthy"),
        }
        assert get_overall_status(components) == "degraded"

    def test_one_unhealthy(self):
        """1つがunhealthy時はunhealthy"""
        components = {
            "db": ComponentHealth(status="unhealthy"),
            "redis": ComponentHealth(status="healthy"),
            "disk": ComponentHealth(status="healthy"),
        }
        assert get_overall_status(components) == "unhealthy"

    def test_unhealthy_takes_priority(self):
        """unhealthyはdegradedより優先"""
        components = {
            "db": ComponentHealth(status="unhealthy"),
            "redis": ComponentHealth(status="degraded"),
            "disk": ComponentHealth(status="healthy"),
        }
        assert get_overall_status(components) == "unhealthy"
