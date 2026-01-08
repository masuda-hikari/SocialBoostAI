"""
ヘルスチェックAPIテスト
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """ヘルスチェックエンドポイントテスト"""

    def test_health_check(self):
        """ヘルスチェックが正常に動作する"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.5.0"
        assert data["service"] == "SocialBoostAI"

    def test_root_endpoint(self):
        """ルートエンドポイントが正常に動作する"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data
        assert "redoc" in data
