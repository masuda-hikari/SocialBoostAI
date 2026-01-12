"""
使用量モニタリングAPIテスト
"""

import json
from datetime import datetime, timezone

import pytest
from fastapi import status

from src.api.db.models import ApiCallLog, DailyUsage


class TestUsageAPI:
    """使用量APIテスト"""

    def test_get_usage_dashboard_unauthorized(self, client):
        """未認証時は使用量ダッシュボードを取得できない"""
        response = client.get("/api/v1/usage/dashboard")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_usage_dashboard(self, authenticated_client, test_user, db_session):
        """使用量ダッシュボードを取得できる"""
        response = authenticated_client.get("/api/v1/usage/dashboard")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "current_plan" in data
        assert "usage_with_limits" in data
        assert "trend" in data
        assert data["current_plan"] == "free"

    def test_get_today_usage(self, authenticated_client, test_user, db_session):
        """今日の使用量を取得できる"""
        response = authenticated_client.get("/api/v1/usage/today")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "api_calls" in data
        assert "analyses_run" in data
        assert "reports_generated" in data
        assert "scheduled_posts" in data
        assert "ai_generations" in data
        assert "platform_usage" in data

    def test_get_usage_with_limits(self, authenticated_client, test_user, db_session):
        """使用量と制限を取得できる"""
        response = authenticated_client.get("/api/v1/usage/with-limits")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "today" in data
        assert "limits" in data
        assert "remaining" in data
        assert "usage_percent" in data

        # Free プランの制限を確認
        limits = data["limits"]
        assert limits["api_calls_per_day"] == 1000
        assert limits["analyses_per_day"] == 5
        assert limits["scheduled_posts_per_day"] == 0  # Free プランでは利用不可

    def test_get_plan_limits(self, authenticated_client, test_user):
        """プラン制限を取得できる"""
        response = authenticated_client.get("/api/v1/usage/limits")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # Free プランの制限
        assert data["api_calls_per_day"] == 1000
        assert data["api_calls_per_minute"] == 30
        assert data["analyses_per_day"] == 5
        assert data["reports_per_month"] == 1
        assert data["scheduled_posts_per_day"] == 0
        assert data["ai_generations_per_day"] == 3
        assert data["platforms"] == 1
        assert data["history_days"] == 7

    def test_get_usage_history(self, authenticated_client, test_user, db_session):
        """使用量履歴を取得できる"""
        # テストデータ作成
        usage = DailyUsage(
            user_id=test_user.id,
            date=datetime.now(timezone.utc),
            api_calls=100,
            analyses_run=5,
            reports_generated=1,
            scheduled_posts=0,
            ai_generations=2,
            platform_usage=json.dumps({"twitter": 50, "instagram": 30}),
        )
        db_session.add(usage)
        db_session.commit()

        response = authenticated_client.get("/api/v1/usage/history?days=7")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "period_start" in data
        assert "period_end" in data
        assert "daily_usage" in data
        assert "total" in data
        assert "average" in data

    def test_get_usage_history_with_days_param(self, authenticated_client, test_user):
        """日数パラメータで使用量履歴を取得できる"""
        response = authenticated_client.get("/api/v1/usage/history?days=14")
        assert response.status_code == status.HTTP_200_OK

    def test_get_usage_history_invalid_days(self, authenticated_client, test_user):
        """不正な日数は拒否される"""
        response = authenticated_client.get("/api/v1/usage/history?days=100")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_monthly_summary(self, authenticated_client, test_user, db_session):
        """月次サマリーを取得できる"""
        response = authenticated_client.get("/api/v1/usage/monthly")
        assert response.status_code == status.HTTP_200_OK

    def test_get_monthly_summary_with_param(self, authenticated_client, test_user):
        """年月パラメータで月次サマリーを取得できる"""
        response = authenticated_client.get("/api/v1/usage/monthly?year_month=2026-01")
        assert response.status_code == status.HTTP_200_OK

    def test_get_monthly_summary_invalid_format(self, authenticated_client, test_user):
        """不正な年月形式は拒否される"""
        response = authenticated_client.get("/api/v1/usage/monthly?year_month=2026-1")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_usage_trend(self, authenticated_client, test_user, db_session):
        """使用量トレンドを取得できる"""
        response = authenticated_client.get("/api/v1/usage/trend")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "period" in data
        assert "data" in data
        assert "trend_percent" in data

    def test_get_usage_trend_with_days(self, authenticated_client, test_user):
        """日数パラメータで使用量トレンドを取得できる"""
        response = authenticated_client.get("/api/v1/usage/trend?days=14")
        assert response.status_code == status.HTTP_200_OK

    def test_get_api_call_logs(self, authenticated_client, test_user, db_session):
        """API呼び出しログを取得できる"""
        # テストデータ作成
        log = ApiCallLog(
            user_id=test_user.id,
            endpoint="/api/v1/analysis",
            method="GET",
            status_code=200,
            response_time_ms=50.5,
        )
        db_session.add(log)
        db_session.commit()

        response = authenticated_client.get("/api/v1/usage/logs")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "pages" in data

    def test_get_api_call_logs_with_filter(self, authenticated_client, test_user, db_session):
        """エンドポイントフィルターでAPI呼び出しログを取得できる"""
        # テストデータ作成
        log1 = ApiCallLog(
            user_id=test_user.id,
            endpoint="/api/v1/analysis",
            method="GET",
            status_code=200,
        )
        log2 = ApiCallLog(
            user_id=test_user.id,
            endpoint="/api/v1/reports",
            method="GET",
            status_code=200,
        )
        db_session.add_all([log1, log2])
        db_session.commit()

        response = authenticated_client.get("/api/v1/usage/logs?endpoint=analysis")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # analysisを含むエンドポイントのみ取得
        for item in data["items"]:
            assert "analysis" in item["endpoint"]

    def test_get_api_call_logs_pagination(self, authenticated_client, test_user):
        """ページネーションでAPI呼び出しログを取得できる"""
        response = authenticated_client.get("/api/v1/usage/logs?page=1&per_page=10")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 10

    def test_get_upgrade_recommendation(self, authenticated_client, test_user, db_session):
        """アップグレード推奨を取得できる"""
        response = authenticated_client.get("/api/v1/usage/upgrade-recommendation")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "should_upgrade" in data
        assert "current_usage_vs_limit" in data

    def test_check_usage_limit_allowed(self, authenticated_client, test_user, db_session):
        """使用量制限チェック - 許可"""
        response = authenticated_client.get("/api/v1/usage/check/api_call?count=1")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["allowed"] is True
        assert data["usage_type"] == "api_call"
        assert data["requested_count"] == 1

    def test_check_usage_limit_analysis(self, authenticated_client, test_user, db_session):
        """分析使用量制限チェック"""
        response = authenticated_client.get("/api/v1/usage/check/analysis?count=1")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "allowed" in data
        assert data["usage_type"] == "analysis"


class TestUsageService:
    """使用量サービステスト"""

    def test_get_plan_limits_free(self, db_session):
        """Free プランの制限を取得できる"""
        from src.api.usage.service import UsageService

        service = UsageService(db_session)
        limits = service.get_plan_limits("free")

        assert limits.api_calls_per_day == 1000
        assert limits.analyses_per_day == 5
        assert limits.scheduled_posts_per_day == 0

    def test_get_plan_limits_pro(self, db_session):
        """Pro プランの制限を取得できる"""
        from src.api.usage.service import UsageService

        service = UsageService(db_session)
        limits = service.get_plan_limits("pro")

        assert limits.api_calls_per_day == 5000
        assert limits.analyses_per_day == 20
        assert limits.scheduled_posts_per_day == 10

    def test_get_plan_limits_business(self, db_session):
        """Business プランの制限を取得できる"""
        from src.api.usage.service import UsageService

        service = UsageService(db_session)
        limits = service.get_plan_limits("business")

        assert limits.api_calls_per_day == 20000
        assert limits.analyses_per_day == 100
        assert limits.reports_per_month == -1  # 無制限

    def test_get_plan_limits_enterprise(self, db_session):
        """Enterprise プランの制限を取得できる"""
        from src.api.usage.service import UsageService

        service = UsageService(db_session)
        limits = service.get_plan_limits("enterprise")

        assert limits.api_calls_per_day == -1  # 無制限
        assert limits.analyses_per_day == -1
        assert limits.reports_per_month == -1

    def test_get_plan_limits_unknown(self, db_session):
        """未知のプランはFreeとして扱う"""
        from src.api.usage.service import UsageService

        service = UsageService(db_session)
        limits = service.get_plan_limits("unknown_plan")

        assert limits.api_calls_per_day == 1000  # Free と同じ

    def test_increment_usage(self, db_session, test_user):
        """使用量をインクリメントできる"""
        from src.api.usage.service import UsageService

        service = UsageService(db_session)

        # 初回インクリメント
        usage = service.increment_usage(test_user.id, "api_call", count=5)
        assert usage.api_calls == 5

        # 追加インクリメント
        usage = service.increment_usage(test_user.id, "api_call", count=3)
        assert usage.api_calls == 8

    def test_increment_usage_with_platform(self, db_session, test_user):
        """プラットフォーム別使用量をインクリメントできる"""
        from src.api.usage.service import UsageService

        service = UsageService(db_session)

        usage = service.increment_usage(
            test_user.id, "analysis", platform="twitter", count=2
        )
        assert usage.analyses_run == 2

        platform_usage = json.loads(usage.platform_usage)
        assert platform_usage["twitter"] == 2

    def test_log_api_call(self, db_session, test_user):
        """API呼び出しをログに記録できる"""
        from src.api.usage.service import UsageService

        service = UsageService(db_session)

        log = service.log_api_call(
            user_id=test_user.id,
            endpoint="/api/v1/analysis",
            method="GET",
            status_code=200,
            response_time_ms=45.5,
            ip_address="192.168.1.1",
        )

        assert log.endpoint == "/api/v1/analysis"
        assert log.method == "GET"
        assert log.status_code == 200
        assert log.response_time_ms == 45.5

    def test_check_limit_allowed(self, db_session, test_user):
        """使用量が制限内の場合はTrueを返す"""
        from src.api.usage.service import UsageService

        service = UsageService(db_session)

        allowed, message = service.check_limit(
            test_user.id, "free", "api_call", count=1
        )
        assert allowed is True
        assert message == "OK"

    def test_check_limit_exceeded(self, db_session, test_user):
        """使用量が制限を超えた場合はFalseを返す"""
        from src.api.usage.service import UsageService

        service = UsageService(db_session)

        # 制限を超える使用量を作成
        for _ in range(1001):
            service.increment_usage(test_user.id, "api_call", count=1)

        allowed, message = service.check_limit(
            test_user.id, "free", "api_call", count=1
        )
        assert allowed is False
        assert "制限" in message

    def test_check_limit_unlimited(self, db_session, test_user):
        """無制限プランでは常にTrueを返す"""
        from src.api.usage.service import UsageService

        service = UsageService(db_session)

        # Enterprise プランは無制限
        allowed, message = service.check_limit(
            test_user.id, "enterprise", "api_call", count=1000000
        )
        assert allowed is True
