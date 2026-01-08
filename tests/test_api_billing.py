"""
課金API テスト
"""

import hashlib
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from src.api.db.models import Subscription, Token, User
from src.api.main import app
from src.api.schemas import PlanTier

client = TestClient(app)


def _hash_password(password: str) -> str:
    """パスワードハッシュ化"""
    return hashlib.sha256(password.encode()).hexdigest()


@pytest.fixture
def test_user(db_session):
    """テスト用ユーザー作成"""
    user = User(
        id="user_billing_test",
        email="billing@test.com",
        username="billinguser",
        password_hash=_hash_password("password123"),
        role="free",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def pro_user(db_session):
    """Proプランユーザー作成"""
    user = User(
        id="user_pro_test",
        email="pro@test.com",
        username="prouser",
        password_hash=_hash_password("password123"),
        role="pro",
        stripe_customer_id="cus_test123",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def user_token(db_session, test_user):
    """認証トークン作成"""
    token = Token(
        token="billing_test_token_12345678",
        user_id=test_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db_session.add(token)
    db_session.commit()
    return token.token


@pytest.fixture
def pro_user_token(db_session, pro_user):
    """Proユーザー用認証トークン作成"""
    token = Token(
        token="pro_user_test_token_12345678",
        user_id=pro_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db_session.add(token)
    db_session.commit()
    return token.token


@pytest.fixture
def active_subscription(db_session, pro_user):
    """アクティブなサブスクリプション作成"""
    subscription = Subscription(
        id="sub_test123",
        user_id=pro_user.id,
        stripe_subscription_id="stripe_sub_test123",
        stripe_customer_id="cus_test123",
        plan="pro",
        status="active",
        current_period_start=datetime.now(timezone.utc) - timedelta(days=15),
        current_period_end=datetime.now(timezone.utc) + timedelta(days=15),
        cancel_at_period_end=False,
    )
    db_session.add(subscription)
    db_session.commit()
    return subscription


class TestGetPlans:
    """プラン一覧取得テスト"""

    def test_get_plans_success(self):
        """プラン一覧取得成功"""
        response = client.get("/api/v1/billing/plans")
        assert response.status_code == 200

        plans = response.json()
        assert len(plans) == 4

        # Freeプラン検証
        free_plan = next(p for p in plans if p["tier"] == "free")
        assert free_plan["name"] == "Free"
        assert free_plan["price_monthly"] == 0
        assert free_plan["api_calls_per_day"] == 100

        # Proプラン検証
        pro_plan = next(p for p in plans if p["tier"] == "pro")
        assert pro_plan["name"] == "Pro"
        assert pro_plan["price_monthly"] == 1980
        assert pro_plan["api_calls_per_day"] == 1000

    def test_get_single_plan(self):
        """単一プラン取得"""
        response = client.get("/api/v1/billing/plans/pro")
        assert response.status_code == 200

        plan = response.json()
        assert plan["tier"] == "pro"
        assert plan["name"] == "Pro"

    def test_get_invalid_plan(self):
        """存在しないプラン取得"""
        response = client.get("/api/v1/billing/plans/invalid")
        assert response.status_code == 422  # Validation error


class TestGetSubscription:
    """サブスクリプション取得テスト"""

    def test_get_subscription_none(self, user_token):
        """サブスクリプションなし"""
        response = client.get(
            "/api/v1/billing/subscription",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        assert response.json() is None

    def test_get_subscription_active(self, pro_user_token, active_subscription):
        """アクティブなサブスクリプション取得"""
        response = client.get(
            "/api/v1/billing/subscription",
            headers={"Authorization": f"Bearer {pro_user_token}"},
        )
        assert response.status_code == 200

        sub = response.json()
        assert sub["plan"] == "pro"
        assert sub["status"] == "active"
        assert sub["cancel_at_period_end"] is False

    def test_get_subscription_unauthorized(self):
        """認証なしでサブスクリプション取得"""
        response = client.get("/api/v1/billing/subscription")
        assert response.status_code == 401


class TestCheckoutSession:
    """Checkout Session作成テスト"""

    def test_checkout_free_plan_error(self, user_token):
        """無料プランへの課金はエラー"""
        response = client.post(
            "/api/v1/billing/checkout",
            json={
                "plan": "free",
                "success_url": "https://example.com/success",
                "cancel_url": "https://example.com/cancel",
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 400
        assert "無料プラン" in response.json()["detail"]

    def test_checkout_unauthorized(self):
        """認証なしでCheckout Session作成"""
        response = client.post(
            "/api/v1/billing/checkout",
            json={
                "plan": "pro",
                "success_url": "https://example.com/success",
                "cancel_url": "https://example.com/cancel",
            },
        )
        assert response.status_code == 401

    def test_checkout_stripe_not_configured(self, user_token):
        """Stripe未設定でCheckout Session作成"""
        response = client.post(
            "/api/v1/billing/checkout",
            json={
                "plan": "pro",
                "success_url": "https://example.com/success",
                "cancel_url": "https://example.com/cancel",
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        # Stripe未設定のため503
        assert response.status_code == 503


class TestPortalSession:
    """Customer Portal Session作成テスト"""

    def test_portal_no_customer(self, user_token):
        """Stripe顧客なしでPortal Session作成"""
        response = client.post(
            "/api/v1/billing/portal",
            json={"return_url": "https://example.com/account"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        # Stripe顧客IDがないのでエラー
        # Stripe未設定の場合は503が先に返る
        assert response.status_code in [400, 503]

    def test_portal_unauthorized(self):
        """認証なしでPortal Session作成"""
        response = client.post(
            "/api/v1/billing/portal",
            json={"return_url": "https://example.com/account"},
        )
        assert response.status_code == 401


class TestCancelSubscription:
    """サブスクリプションキャンセルテスト"""

    def test_cancel_no_subscription(self, user_token):
        """サブスクリプションなしでキャンセル"""
        response = client.post(
            "/api/v1/billing/cancel",
            json={"at_period_end": True},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 400
        assert "アクティブなサブスクリプション" in response.json()["detail"]

    def test_cancel_unauthorized(self):
        """認証なしでキャンセル"""
        response = client.post(
            "/api/v1/billing/cancel",
            json={"at_period_end": True},
        )
        assert response.status_code == 401


class TestGetLimits:
    """制限取得テスト"""

    def test_get_limits_free_user(self, user_token):
        """Freeユーザーの制限取得"""
        response = client.get(
            "/api/v1/billing/limits",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200

        limits = response.json()
        assert limits["api_calls_per_day"] == 100
        assert limits["reports_per_month"] == 1
        assert limits["platforms"] == 1
        assert limits["history_days"] == 7

    def test_get_limits_pro_user(self, pro_user_token):
        """Proユーザーの制限取得"""
        response = client.get(
            "/api/v1/billing/limits",
            headers={"Authorization": f"Bearer {pro_user_token}"},
        )
        assert response.status_code == 200

        limits = response.json()
        assert limits["api_calls_per_day"] == 1000
        assert limits["reports_per_month"] == 4
        assert limits["platforms"] == 1
        assert limits["history_days"] == 90

    def test_get_limits_unauthorized(self):
        """認証なしで制限取得"""
        response = client.get("/api/v1/billing/limits")
        assert response.status_code == 401


class TestWebhook:
    """Webhookテスト"""

    def test_webhook_no_secret(self):
        """Webhookシークレット未設定"""
        response = client.post(
            "/api/v1/billing/webhook",
            content=b"{}",
            headers={"Stripe-Signature": "test_signature"},
        )
        assert response.status_code == 503

    def test_webhook_no_signature(self):
        """署名ヘッダーなし"""
        response = client.post(
            "/api/v1/billing/webhook",
            content=b"{}",
        )
        # Webhook設定がない場合は503、設定されていれば400
        assert response.status_code in [400, 503]
