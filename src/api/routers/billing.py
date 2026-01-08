"""
課金API Router
"""

import os
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..billing.service import PLAN_LIMITS, BillingService, PlanTier
from ..db.base import get_db
from ..db.models import User
from ..dependencies import get_current_user
from ..schemas import (
    CancelSubscriptionRequest,
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    ErrorResponse,
    PlanInfo,
    PortalSessionRequest,
    PortalSessionResponse,
    SubscriptionResponse,
)

router = APIRouter(prefix="/billing", tags=["billing"])

# プラン情報定義
PLANS: list[PlanInfo] = [
    PlanInfo(
        tier=PlanTier.FREE,
        name="Free",
        price_monthly=0,
        api_calls_per_day=100,
        reports_per_month=1,
        platforms=1,
        history_days=7,
    ),
    PlanInfo(
        tier=PlanTier.PRO,
        name="Pro",
        price_monthly=1980,
        api_calls_per_day=1000,
        reports_per_month=4,
        platforms=1,
        history_days=90,
    ),
    PlanInfo(
        tier=PlanTier.BUSINESS,
        name="Business",
        price_monthly=4980,
        api_calls_per_day=10000,
        reports_per_month=-1,
        platforms=3,
        history_days=-1,
    ),
    PlanInfo(
        tier=PlanTier.ENTERPRISE,
        name="Enterprise",
        price_monthly=0,  # 要見積
        api_calls_per_day=-1,
        reports_per_month=-1,
        platforms=-1,
        history_days=-1,
    ),
]


def get_billing_service() -> BillingService:
    """BillingService依存性注入"""
    return BillingService()


@router.get("/plans", response_model=list[PlanInfo])
async def get_plans() -> list[PlanInfo]:
    """
    利用可能なプラン一覧を取得
    """
    return PLANS


@router.get("/plans/{tier}", response_model=PlanInfo)
async def get_plan(tier: PlanTier) -> PlanInfo:
    """
    指定プランの詳細を取得
    """
    for plan in PLANS:
        if plan.tier == tier:
            return plan
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="プランが見つかりません",
    )


@router.get(
    "/subscription",
    response_model=SubscriptionResponse | None,
    responses={401: {"model": ErrorResponse}},
)
async def get_subscription(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    billing: Annotated[BillingService, Depends(get_billing_service)],
) -> SubscriptionResponse | None:
    """
    現在のサブスクリプションを取得
    """
    subscription = billing.get_user_subscription(db, current_user)
    if not subscription:
        return None

    return SubscriptionResponse(
        id=subscription.id,
        user_id=subscription.user_id,
        plan=PlanTier(subscription.plan),
        status=subscription.status,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        cancel_at_period_end=subscription.cancel_at_period_end,
        canceled_at=subscription.canceled_at,
        created_at=subscription.created_at,
    )


@router.post(
    "/checkout",
    response_model=CheckoutSessionResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
async def create_checkout_session(
    request: CheckoutSessionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    billing: Annotated[BillingService, Depends(get_billing_service)],
) -> CheckoutSessionResponse:
    """
    Stripe Checkout Sessionを作成
    """
    # 無料プランチェックを先に行う
    if request.plan == PlanTier.FREE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="無料プランには課金不要です",
        )

    if not billing.is_stripe_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="決済サービスが設定されていません",
        )

    try:
        checkout_url = billing.create_checkout_session(
            db=db,
            user=current_user,
            plan=request.plan,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
        )
        return CheckoutSessionResponse(checkout_url=checkout_url)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post(
    "/portal",
    response_model=PortalSessionResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
async def create_portal_session(
    request: PortalSessionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    billing: Annotated[BillingService, Depends(get_billing_service)],
) -> PortalSessionResponse:
    """
    Stripe Customer Portal Sessionを作成
    """
    if not billing.is_stripe_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="決済サービスが設定されていません",
        )

    if not current_user.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stripe顧客が存在しません",
        )

    try:
        portal_url = billing.create_portal_session(
            db=db,
            user=current_user,
            return_url=request.return_url,
        )
        return PortalSessionResponse(portal_url=portal_url)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post(
    "/cancel",
    response_model=dict,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
    },
)
async def cancel_subscription(
    request: CancelSubscriptionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    billing: Annotated[BillingService, Depends(get_billing_service)],
) -> dict:
    """
    サブスクリプションをキャンセル
    """
    success = billing.cancel_subscription(
        db=db,
        user=current_user,
        at_period_end=request.at_period_end,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="アクティブなサブスクリプションがありません",
        )

    return {"message": "サブスクリプションをキャンセルしました"}


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    stripe_signature: Annotated[str | None, Header(alias="Stripe-Signature")] = None,
    db: Session = Depends(get_db),
) -> dict:
    """
    Stripe Webhookエンドポイント
    """
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    if not webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook設定がありません",
        )

    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stripe-Signatureヘッダーがありません",
        )

    payload = await request.body()
    billing = BillingService()

    try:
        event = billing._stripe.construct_webhook_event(
            payload=payload,
            signature=stripe_signature,
            webhook_secret=webhook_secret,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook署名検証失敗: {e}",
        ) from e

    # イベント処理
    event_type = event.type

    if event_type == "checkout.session.completed":
        billing.handle_checkout_completed(db, event)
    elif event_type == "customer.subscription.updated":
        billing.handle_subscription_updated(db, event)
    elif event_type == "customer.subscription.deleted":
        billing.handle_subscription_deleted(db, event)
    elif event_type == "invoice.payment_failed":
        billing.handle_invoice_payment_failed(db, event)

    return {"status": "success"}


@router.get("/limits", response_model=dict)
async def get_current_limits(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """
    現在のユーザーの制限を取得
    """
    try:
        plan = PlanTier(current_user.role)
    except ValueError:
        plan = PlanTier.FREE

    return PLAN_LIMITS.get(plan, PLAN_LIMITS[PlanTier.FREE])
