"""
Stripe APIクライアント
"""

import os
from typing import Any

import stripe
from stripe import Customer, PaymentIntent, Subscription


class StripeClient:
    """Stripe APIラッパー"""

    def __init__(self, api_key: str | None = None) -> None:
        """
        Args:
            api_key: Stripe APIキー（None時は環境変数から取得）
        """
        self._api_key = api_key or os.getenv("STRIPE_SECRET_KEY", "")
        if self._api_key:
            stripe.api_key = self._api_key

    @property
    def is_configured(self) -> bool:
        """Stripeが設定済みか"""
        return bool(self._api_key)

    def create_customer(
        self,
        email: str,
        name: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Customer:
        """
        Stripe顧客を作成

        Args:
            email: メールアドレス
            name: 顧客名
            metadata: メタデータ

        Returns:
            作成された顧客オブジェクト
        """
        params: dict[str, Any] = {"email": email}
        if name:
            params["name"] = name
        if metadata:
            params["metadata"] = metadata

        return stripe.Customer.create(**params)

    def get_customer(self, customer_id: str) -> Customer | None:
        """
        顧客情報を取得

        Args:
            customer_id: Stripe顧客ID

        Returns:
            顧客オブジェクト（存在しない場合None）
        """
        try:
            return stripe.Customer.retrieve(customer_id)
        except stripe.InvalidRequestError:
            return None

    def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        trial_days: int | None = None,
    ) -> Subscription:
        """
        サブスクリプションを作成

        Args:
            customer_id: Stripe顧客ID
            price_id: Stripe価格ID
            trial_days: 無料トライアル日数

        Returns:
            作成されたサブスクリプション
        """
        params: dict[str, Any] = {
            "customer": customer_id,
            "items": [{"price": price_id}],
        }
        if trial_days:
            params["trial_period_days"] = trial_days

        return stripe.Subscription.create(**params)

    def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True,
    ) -> Subscription:
        """
        サブスクリプションをキャンセル

        Args:
            subscription_id: サブスクリプションID
            at_period_end: 期間終了時にキャンセルするか

        Returns:
            更新されたサブスクリプション
        """
        return stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=at_period_end,
        )

    def get_subscription(self, subscription_id: str) -> Subscription | None:
        """
        サブスクリプションを取得

        Args:
            subscription_id: サブスクリプションID

        Returns:
            サブスクリプション（存在しない場合None）
        """
        try:
            return stripe.Subscription.retrieve(subscription_id)
        except stripe.InvalidRequestError:
            return None

    def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        mode: str = "subscription",
    ) -> stripe.checkout.Session:
        """
        Checkout Sessionを作成

        Args:
            customer_id: Stripe顧客ID
            price_id: 価格ID
            success_url: 成功時リダイレクトURL
            cancel_url: キャンセル時リダイレクトURL
            mode: モード（subscription/payment）

        Returns:
            Checkout Session
        """
        return stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode=mode,
            success_url=success_url,
            cancel_url=cancel_url,
        )

    def create_portal_session(
        self,
        customer_id: str,
        return_url: str,
    ) -> stripe.billing_portal.Session:
        """
        Customer Portal Sessionを作成

        Args:
            customer_id: Stripe顧客ID
            return_url: 戻りURL

        Returns:
            Portal Session
        """
        return stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )

    def construct_webhook_event(
        self,
        payload: bytes,
        signature: str,
        webhook_secret: str,
    ) -> stripe.Event:
        """
        Webhookイベントを検証・構築

        Args:
            payload: リクエストボディ
            signature: Stripe-Signatureヘッダー
            webhook_secret: Webhookシークレット

        Returns:
            検証済みイベント

        Raises:
            stripe.SignatureVerificationError: 署名検証失敗時
        """
        return stripe.Webhook.construct_event(
            payload,
            signature,
            webhook_secret,
        )
