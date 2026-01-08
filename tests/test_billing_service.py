"""
課金サービス 単体テスト
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.api.billing.service import PLAN_LIMITS, BillingService, PlanTier
from src.api.billing.stripe_client import StripeClient


class TestPlanLimits:
    """プラン制限テスト"""

    def test_free_plan_limits(self):
        """Freeプラン制限"""
        limits = PLAN_LIMITS[PlanTier.FREE]
        assert limits["api_calls_per_day"] == 100
        assert limits["reports_per_month"] == 1
        assert limits["platforms"] == 1
        assert limits["history_days"] == 7

    def test_pro_plan_limits(self):
        """Proプラン制限"""
        limits = PLAN_LIMITS[PlanTier.PRO]
        assert limits["api_calls_per_day"] == 1000
        assert limits["reports_per_month"] == 4
        assert limits["platforms"] == 1
        assert limits["history_days"] == 90

    def test_business_plan_limits(self):
        """Businessプラン制限"""
        limits = PLAN_LIMITS[PlanTier.BUSINESS]
        assert limits["api_calls_per_day"] == 10000
        assert limits["reports_per_month"] == -1  # 無制限
        assert limits["platforms"] == 3
        assert limits["history_days"] == -1  # 無制限

    def test_enterprise_plan_limits(self):
        """Enterpriseプラン制限"""
        limits = PLAN_LIMITS[PlanTier.ENTERPRISE]
        assert limits["api_calls_per_day"] == -1  # 無制限
        assert limits["reports_per_month"] == -1
        assert limits["platforms"] == -1
        assert limits["history_days"] == -1


class TestBillingService:
    """BillingServiceテスト"""

    def test_get_plan_limits(self):
        """プラン制限取得"""
        service = BillingService()

        free_limits = service.get_plan_limits(PlanTier.FREE)
        assert free_limits["api_calls_per_day"] == 100

        pro_limits = service.get_plan_limits(PlanTier.PRO)
        assert pro_limits["api_calls_per_day"] == 1000

    def test_is_stripe_configured_false(self):
        """Stripe未設定時"""
        service = BillingService()
        # 環境変数なしの場合はFalse
        assert service.is_stripe_configured is False

    @patch.dict("os.environ", {"STRIPE_SECRET_KEY": "sk_test_123"})
    def test_is_stripe_configured_true(self):
        """Stripe設定済み時"""
        client = StripeClient()
        service = BillingService(stripe_client=client)
        assert service.is_stripe_configured is True


class TestStripeClient:
    """StripeClientテスト"""

    def test_is_configured_false(self):
        """APIキーなしの場合"""
        client = StripeClient(api_key="")
        assert client.is_configured is False

    def test_is_configured_true(self):
        """APIキーありの場合"""
        client = StripeClient(api_key="sk_test_123")
        assert client.is_configured is True


class TestPlanTier:
    """PlanTierテスト"""

    def test_plan_tier_values(self):
        """プラン値確認"""
        assert PlanTier.FREE.value == "free"
        assert PlanTier.PRO.value == "pro"
        assert PlanTier.BUSINESS.value == "business"
        assert PlanTier.ENTERPRISE.value == "enterprise"

    def test_plan_tier_from_string(self):
        """文字列からプラン変換"""
        assert PlanTier("free") == PlanTier.FREE
        assert PlanTier("pro") == PlanTier.PRO
        assert PlanTier("business") == PlanTier.BUSINESS

    def test_invalid_plan_tier(self):
        """不正なプラン値"""
        with pytest.raises(ValueError):
            PlanTier("invalid")
