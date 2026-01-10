"""
レート制限ミドルウェアのテスト
"""

import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from src.api.middleware.rate_limit import (
    ANONYMOUS_RATE_LIMIT,
    PLAN_RATE_LIMITS,
    RateLimitConfig,
    RateLimitMiddleware,
    RateLimitState,
    get_rate_limit_stats,
)


class TestRateLimitConfig:
    """RateLimitConfig テスト"""

    def test_config_creation(self):
        """設定オブジェクト作成テスト"""
        config = RateLimitConfig(
            requests_per_minute=100, requests_per_day=10000, burst_limit=20
        )
        assert config.requests_per_minute == 100
        assert config.requests_per_day == 10000
        assert config.burst_limit == 20

    def test_plan_configs_exist(self):
        """プラン設定存在確認"""
        assert "free" in PLAN_RATE_LIMITS
        assert "pro" in PLAN_RATE_LIMITS
        assert "business" in PLAN_RATE_LIMITS
        assert "enterprise" in PLAN_RATE_LIMITS

    def test_plan_limits_ascending(self):
        """プラン制限が上位ほど大きいことを確認"""
        free = PLAN_RATE_LIMITS["free"]
        pro = PLAN_RATE_LIMITS["pro"]
        business = PLAN_RATE_LIMITS["business"]
        enterprise = PLAN_RATE_LIMITS["enterprise"]

        assert free.requests_per_minute < pro.requests_per_minute
        assert pro.requests_per_minute < business.requests_per_minute
        assert business.requests_per_minute < enterprise.requests_per_minute

        assert free.requests_per_day < pro.requests_per_day
        assert pro.requests_per_day < business.requests_per_day
        assert business.requests_per_day < enterprise.requests_per_day


class TestRateLimitState:
    """RateLimitState テスト"""

    def test_default_state(self):
        """デフォルト状態テスト"""
        state = RateLimitState()
        assert state.minute_count == 0
        assert state.minute_reset == 0.0
        assert state.day_count == 0
        assert state.day_reset == 0.0
        assert state.burst_count == 0
        assert state.burst_reset == 0.0


class TestRateLimitMiddleware:
    """RateLimitMiddleware テスト"""

    @pytest.fixture
    def app(self):
        """テスト用アプリケーション（レート制限有効）"""
        import os

        # レート制限を有効化してミドルウェアを作成
        original = os.environ.get("RATE_LIMIT_ENABLED")
        os.environ["RATE_LIMIT_ENABLED"] = "true"

        try:
            app = FastAPI()
            app.add_middleware(RateLimitMiddleware)

            @app.get("/test")
            async def test_endpoint():
                return {"message": "ok"}

            @app.get("/health")
            async def health():
                return {"status": "healthy"}

            yield app
        finally:
            if original is None:
                os.environ.pop("RATE_LIMIT_ENABLED", None)
            else:
                os.environ["RATE_LIMIT_ENABLED"] = original

    @pytest.fixture
    def client(self, app):
        """テストクライアント"""
        return TestClient(app)

    def test_basic_request_allowed(self, client):
        """基本リクエストが許可されること"""
        response = client.get("/test")
        assert response.status_code == 200

    def test_rate_limit_headers_present(self, client):
        """レート制限ヘッダーが存在すること"""
        response = client.get("/test")
        assert "X-RateLimit-Limit-Minute" in response.headers
        assert "X-RateLimit-Remaining-Minute" in response.headers
        assert "X-RateLimit-Limit-Day" in response.headers
        assert "X-RateLimit-Remaining-Day" in response.headers

    def test_health_endpoint_skipped(self, client):
        """ヘルスエンドポイントはスキップされること"""
        # 多数リクエストしてもレート制限されない
        for _ in range(50):
            response = client.get("/health")
            assert response.status_code == 200

    def test_remaining_decreases(self, client):
        """残りリクエスト数が減少すること"""
        response1 = client.get("/test")
        remaining1 = int(response1.headers["X-RateLimit-Remaining-Minute"])

        response2 = client.get("/test")
        remaining2 = int(response2.headers["X-RateLimit-Remaining-Minute"])

        assert remaining2 < remaining1

    def test_burst_limit_exceeded(self, client):
        """バースト制限超過テスト"""
        # バースト制限は5回（ANONYMOUS_RATE_LIMIT）
        for i in range(ANONYMOUS_RATE_LIMIT.burst_limit):
            response = client.get("/test")
            # 最後の1回はまだ許可されるはず

        # 次のリクエストは拒否される
        response = client.get("/test")
        assert response.status_code == 429

    def test_rate_limit_response_content(self, client):
        """レート制限レスポンス内容テスト"""
        # バースト制限を超過させる
        for _ in range(ANONYMOUS_RATE_LIMIT.burst_limit + 1):
            response = client.get("/test")

        data = response.json()
        assert "detail" in data
        assert "error" in data
        assert data["error"] == "rate_limit_exceeded"
        assert "retry_after" in data

    def test_rate_limit_headers_on_429(self, client):
        """429レスポンスにレート制限ヘッダーがあること"""
        # バースト制限を超過させる
        for _ in range(ANONYMOUS_RATE_LIMIT.burst_limit + 1):
            response = client.get("/test")

        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers


class TestRateLimitMiddlewarePlanBased:
    """プラン別レート制限テスト"""

    def test_get_rate_limit_config_free(self):
        """Freeプラン設定取得"""
        middleware = RateLimitMiddleware(MagicMock())
        config = middleware._get_rate_limit_config("free")
        assert config == PLAN_RATE_LIMITS["free"]

    def test_get_rate_limit_config_pro(self):
        """Proプラン設定取得"""
        middleware = RateLimitMiddleware(MagicMock())
        config = middleware._get_rate_limit_config("pro")
        assert config == PLAN_RATE_LIMITS["pro"]

    def test_get_rate_limit_config_unknown_plan(self):
        """不明プランはFreeにフォールバック"""
        middleware = RateLimitMiddleware(MagicMock())
        config = middleware._get_rate_limit_config("unknown")
        assert config == PLAN_RATE_LIMITS["free"]

    def test_get_rate_limit_config_anonymous(self):
        """匿名ユーザー設定取得"""
        middleware = RateLimitMiddleware(MagicMock())
        config = middleware._get_rate_limit_config("anonymous")
        assert config == ANONYMOUS_RATE_LIMIT


class TestRateLimitMiddlewareDisabled:
    """レート制限無効化テスト"""

    def test_disabled_allows_unlimited_requests(self):
        """無効時は無制限にリクエスト可能"""
        import os

        # 環境変数を設定してからミドルウェアを作成
        original = os.environ.get("RATE_LIMIT_ENABLED")
        try:
            os.environ["RATE_LIMIT_ENABLED"] = "false"

            # 新しいアプリとミドルウェアを作成
            app = FastAPI()
            app.add_middleware(RateLimitMiddleware)

            @app.get("/test")
            async def test_endpoint():
                return {"message": "ok"}

            client = TestClient(app)

            for _ in range(100):
                response = client.get("/test")
                assert response.status_code == 200
        finally:
            if original is None:
                os.environ.pop("RATE_LIMIT_ENABLED", None)
            else:
                os.environ["RATE_LIMIT_ENABLED"] = original


class TestRateLimitCleanup:
    """クリーンアップテスト"""

    def test_cleanup_expired_states(self):
        """期限切れ状態のクリーンアップ"""
        middleware = RateLimitMiddleware(MagicMock())

        # 期限切れ状態を追加
        now = time.time()
        middleware._states["test:1"] = RateLimitState(
            minute_reset=now - 100,
            day_reset=now - 100,
            burst_reset=now - 100,
        )

        # 有効な状態を追加
        middleware._states["test:2"] = RateLimitState(
            minute_reset=now + 100,
            day_reset=now + 100,
            burst_reset=now + 100,
        )

        cleaned = middleware.cleanup_expired_states()
        assert cleaned == 1
        assert "test:1" not in middleware._states
        assert "test:2" in middleware._states


class TestGetRateLimitStats:
    """統計取得テスト"""

    def test_stats_structure(self):
        """統計構造テスト"""
        stats = get_rate_limit_stats()

        assert "plans" in stats
        assert "anonymous" in stats

        for plan in ["free", "pro", "business", "enterprise"]:
            assert plan in stats["plans"]
            assert "requests_per_minute" in stats["plans"][plan]
            assert "requests_per_day" in stats["plans"][plan]
            assert "burst_limit" in stats["plans"][plan]

    def test_stats_values_match_config(self):
        """統計値が設定と一致すること"""
        stats = get_rate_limit_stats()

        for plan, config in PLAN_RATE_LIMITS.items():
            assert stats["plans"][plan]["requests_per_minute"] == config.requests_per_minute
            assert stats["plans"][plan]["requests_per_day"] == config.requests_per_day
            assert stats["plans"][plan]["burst_limit"] == config.burst_limit
