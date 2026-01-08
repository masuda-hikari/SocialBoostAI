"""
課金サービス - ビジネスロジック
"""

import os
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from ..db.models import Subscription as SubscriptionModel
from ..db.models import User
from .stripe_client import StripeClient

if TYPE_CHECKING:
    import stripe


class PlanTier(str, Enum):
    """プランティア"""

    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


# プラン別価格ID（環境変数から取得）
PLAN_PRICE_IDS: dict[PlanTier, str] = {
    PlanTier.FREE: "",  # 無料プランは価格IDなし
    PlanTier.PRO: os.getenv("STRIPE_PRICE_PRO", ""),
    PlanTier.BUSINESS: os.getenv("STRIPE_PRICE_BUSINESS", ""),
    PlanTier.ENTERPRISE: os.getenv("STRIPE_PRICE_ENTERPRISE", ""),
}

# プラン別制限
PLAN_LIMITS: dict[PlanTier, dict[str, int]] = {
    PlanTier.FREE: {
        "api_calls_per_day": 100,
        "reports_per_month": 1,
        "platforms": 1,
        "history_days": 7,
    },
    PlanTier.PRO: {
        "api_calls_per_day": 1000,
        "reports_per_month": 4,
        "platforms": 1,
        "history_days": 90,
    },
    PlanTier.BUSINESS: {
        "api_calls_per_day": 10000,
        "reports_per_month": -1,  # 無制限
        "platforms": 3,
        "history_days": -1,  # 無制限
    },
    PlanTier.ENTERPRISE: {
        "api_calls_per_day": -1,  # 無制限
        "reports_per_month": -1,
        "platforms": -1,
        "history_days": -1,
    },
}


class BillingService:
    """課金サービス"""

    def __init__(self, stripe_client: StripeClient | None = None) -> None:
        """
        Args:
            stripe_client: Stripeクライアント（テスト用DI）
        """
        self._stripe = stripe_client or StripeClient()

    @property
    def is_stripe_configured(self) -> bool:
        """Stripeが設定済みか"""
        return self._stripe.is_configured

    def get_plan_limits(self, plan: PlanTier) -> dict[str, int]:
        """
        プラン別制限を取得

        Args:
            plan: プランティア

        Returns:
            制限設定辞書
        """
        return PLAN_LIMITS.get(plan, PLAN_LIMITS[PlanTier.FREE])

    def create_customer(
        self,
        db: Session,
        user: User,
    ) -> str:
        """
        Stripe顧客を作成しユーザーに紐付け

        Args:
            db: DBセッション
            user: ユーザー

        Returns:
            Stripe顧客ID
        """
        customer = self._stripe.create_customer(
            email=user.email,
            name=user.username,
            metadata={"user_id": user.id},
        )

        # ユーザーにStripe顧客IDを保存
        user.stripe_customer_id = customer.id
        db.commit()

        return customer.id

    def get_or_create_customer(
        self,
        db: Session,
        user: User,
    ) -> str:
        """
        Stripe顧客を取得または作成

        Args:
            db: DBセッション
            user: ユーザー

        Returns:
            Stripe顧客ID
        """
        if user.stripe_customer_id:
            return user.stripe_customer_id

        return self.create_customer(db, user)

    def create_checkout_session(
        self,
        db: Session,
        user: User,
        plan: PlanTier,
        success_url: str,
        cancel_url: str,
    ) -> str:
        """
        Checkout Sessionを作成

        Args:
            db: DBセッション
            user: ユーザー
            plan: 目標プラン
            success_url: 成功時URL
            cancel_url: キャンセル時URL

        Returns:
            Checkout Session URL
        """
        if plan == PlanTier.FREE:
            raise ValueError("無料プランには課金不要")

        price_id = PLAN_PRICE_IDS.get(plan)
        if not price_id:
            raise ValueError(f"プラン {plan} の価格IDが設定されていません")

        customer_id = self.get_or_create_customer(db, user)
        session = self._stripe.create_checkout_session(
            customer_id=customer_id,
            price_id=price_id,
            success_url=success_url,
            cancel_url=cancel_url,
        )

        return session.url or ""

    def create_portal_session(
        self,
        db: Session,
        user: User,
        return_url: str,
    ) -> str:
        """
        Customer Portal Sessionを作成

        Args:
            db: DBセッション
            user: ユーザー
            return_url: 戻りURL

        Returns:
            Portal Session URL
        """
        if not user.stripe_customer_id:
            raise ValueError("Stripe顧客が存在しません")

        session = self._stripe.create_portal_session(
            customer_id=user.stripe_customer_id,
            return_url=return_url,
        )

        return session.url

    def handle_checkout_completed(
        self,
        db: Session,
        event: "stripe.Event",
    ) -> None:
        """
        checkout.session.completed イベント処理

        Args:
            db: DBセッション
            event: Stripeイベント
        """
        session = event.data.object
        customer_id = session.customer
        subscription_id = session.subscription

        # ユーザーを取得
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if not user:
            return

        # サブスクリプション情報を取得
        stripe_sub = self._stripe.get_subscription(subscription_id)
        if not stripe_sub:
            return

        # プランを特定
        price_id = stripe_sub.items.data[0].price.id
        plan = self._get_plan_from_price_id(price_id)

        # サブスクリプションをDBに保存
        subscription = SubscriptionModel(
            user_id=user.id,
            stripe_subscription_id=subscription_id,
            stripe_customer_id=customer_id,
            plan=plan.value,
            status="active",
            current_period_start=datetime.fromtimestamp(
                stripe_sub.current_period_start, tz=timezone.utc
            ),
            current_period_end=datetime.fromtimestamp(
                stripe_sub.current_period_end, tz=timezone.utc
            ),
        )
        db.add(subscription)

        # ユーザーロールを更新
        user.role = plan.value
        db.commit()

    def handle_subscription_updated(
        self,
        db: Session,
        event: "stripe.Event",
    ) -> None:
        """
        customer.subscription.updated イベント処理

        Args:
            db: DBセッション
            event: Stripeイベント
        """
        stripe_sub = event.data.object
        subscription_id = stripe_sub.id

        # DBのサブスクリプションを取得
        subscription = (
            db.query(SubscriptionModel)
            .filter(SubscriptionModel.stripe_subscription_id == subscription_id)
            .first()
        )
        if not subscription:
            return

        # ステータス更新
        subscription.status = stripe_sub.status
        subscription.current_period_start = datetime.fromtimestamp(
            stripe_sub.current_period_start, tz=timezone.utc
        )
        subscription.current_period_end = datetime.fromtimestamp(
            stripe_sub.current_period_end, tz=timezone.utc
        )

        # キャンセル予定の場合
        if stripe_sub.cancel_at_period_end:
            subscription.cancel_at_period_end = True
            if stripe_sub.canceled_at:
                subscription.canceled_at = datetime.fromtimestamp(
                    stripe_sub.canceled_at, tz=timezone.utc
                )

        db.commit()

    def handle_subscription_deleted(
        self,
        db: Session,
        event: "stripe.Event",
    ) -> None:
        """
        customer.subscription.deleted イベント処理

        Args:
            db: DBセッション
            event: Stripeイベント
        """
        stripe_sub = event.data.object
        subscription_id = stripe_sub.id

        # DBのサブスクリプションを取得
        subscription = (
            db.query(SubscriptionModel)
            .filter(SubscriptionModel.stripe_subscription_id == subscription_id)
            .first()
        )
        if not subscription:
            return

        # ステータスを更新
        subscription.status = "canceled"
        subscription.canceled_at = datetime.now(timezone.utc)

        # ユーザーを無料プランに戻す
        user = db.query(User).filter(User.id == subscription.user_id).first()
        if user:
            user.role = PlanTier.FREE.value

        db.commit()

    def handle_invoice_payment_failed(
        self,
        db: Session,
        event: "stripe.Event",
    ) -> None:
        """
        invoice.payment_failed イベント処理

        Args:
            db: DBセッション
            event: Stripeイベント
        """
        invoice = event.data.object
        subscription_id = invoice.subscription
        if not subscription_id:
            return

        # DBのサブスクリプションを取得
        subscription = (
            db.query(SubscriptionModel)
            .filter(SubscriptionModel.stripe_subscription_id == subscription_id)
            .first()
        )
        if not subscription:
            return

        # ステータスを更新
        subscription.status = "past_due"
        db.commit()

    def cancel_subscription(
        self,
        db: Session,
        user: User,
        at_period_end: bool = True,
    ) -> bool:
        """
        サブスクリプションをキャンセル

        Args:
            db: DBセッション
            user: ユーザー
            at_period_end: 期間終了時にキャンセルするか

        Returns:
            成功したか
        """
        subscription = (
            db.query(SubscriptionModel)
            .filter(
                SubscriptionModel.user_id == user.id,
                SubscriptionModel.status == "active",
            )
            .first()
        )
        if not subscription:
            return False

        # Stripeでキャンセル
        self._stripe.cancel_subscription(
            subscription.stripe_subscription_id,
            at_period_end=at_period_end,
        )

        # DB更新
        subscription.cancel_at_period_end = at_period_end
        if not at_period_end:
            subscription.status = "canceled"
            subscription.canceled_at = datetime.now(timezone.utc)
            user.role = PlanTier.FREE.value

        db.commit()
        return True

    def get_user_subscription(
        self,
        db: Session,
        user: User,
    ) -> SubscriptionModel | None:
        """
        ユーザーのアクティブなサブスクリプションを取得

        Args:
            db: DBセッション
            user: ユーザー

        Returns:
            サブスクリプション（存在しない場合None）
        """
        return (
            db.query(SubscriptionModel)
            .filter(
                SubscriptionModel.user_id == user.id,
                SubscriptionModel.status.in_(["active", "trialing", "past_due"]),
            )
            .first()
        )

    def _get_plan_from_price_id(self, price_id: str) -> PlanTier:
        """価格IDからプランを特定"""
        for plan, pid in PLAN_PRICE_IDS.items():
            if pid == price_id:
                return plan
        return PlanTier.FREE
