"""
プッシュ通知 API ルーター

Web Push通知のサブスクリプション管理と通知送信
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..db.base import get_db
from ..db.models import User
from ..dependencies import get_current_user, require_admin
from ..push.service import PushNotificationService
from ..schemas import (
    PushNotificationLogsResponse,
    PushNotificationSendRequest,
    PushNotificationStatsResponse,
    PushNotificationTestRequest,
    PushSubscriptionCreate,
    PushSubscriptionListResponse,
    PushSubscriptionResponse,
    PushSubscriptionUpdate,
    VapidPublicKeyResponse,
)

router = APIRouter(tags=["push"])


# =============================================================================
# 公開エンドポイント
# =============================================================================


@router.get("/vapid-key", response_model=VapidPublicKeyResponse)
def get_vapid_public_key(db: Session = Depends(get_db)):
    """
    VAPID公開鍵を取得

    クライアントがプッシュ通知を購読する際に必要
    """
    service = PushNotificationService(db)
    return VapidPublicKeyResponse(public_key=service.get_vapid_public_key())


# =============================================================================
# サブスクリプション管理
# =============================================================================


@router.post("/subscriptions", response_model=PushSubscriptionResponse)
def create_subscription(
    data: PushSubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    プッシュ通知サブスクリプションを登録

    ブラウザからのプッシュ通知購読情報を保存
    """
    service = PushNotificationService(db)
    return service.create_subscription(current_user.id, data)


@router.get("/subscriptions", response_model=PushSubscriptionListResponse)
def get_subscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    サブスクリプション一覧を取得

    現在のユーザーに登録されているすべてのデバイスを返す
    """
    service = PushNotificationService(db)
    return service.get_subscriptions(current_user.id)


@router.get("/subscriptions/{subscription_id}", response_model=PushSubscriptionResponse)
def get_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    サブスクリプション詳細を取得
    """
    service = PushNotificationService(db)
    result = service.get_subscription(subscription_id, current_user.id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="サブスクリプションが見つかりません",
        )
    return result


@router.put("/subscriptions/{subscription_id}", response_model=PushSubscriptionResponse)
def update_subscription(
    subscription_id: str,
    data: PushSubscriptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    サブスクリプションを更新

    通知の有効/無効、受信する通知タイプを変更
    """
    service = PushNotificationService(db)
    result = service.update_subscription(subscription_id, current_user.id, data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="サブスクリプションが見つかりません",
        )
    return result


@router.delete("/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    サブスクリプションを削除

    デバイスの通知購読を解除
    """
    service = PushNotificationService(db)
    if not service.delete_subscription(subscription_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="サブスクリプションが見つかりません",
        )


# =============================================================================
# 通知ログ
# =============================================================================


@router.get("/logs", response_model=PushNotificationLogsResponse)
def get_notification_logs(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    notification_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    通知ログを取得

    送信された通知の履歴を返す
    """
    service = PushNotificationService(db)
    return service.get_notification_logs(
        current_user.id,
        page=page,
        per_page=per_page,
        notification_type=notification_type,
    )


@router.post("/logs/{log_id}/clicked", status_code=status.HTTP_204_NO_CONTENT)
def mark_notification_clicked(
    log_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    通知をクリック済みにする

    クリック率の計測に使用
    """
    service = PushNotificationService(db)
    if not service.mark_notification_clicked(log_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知が見つかりません",
        )


# =============================================================================
# 統計
# =============================================================================


@router.get("/stats", response_model=PushNotificationStatsResponse)
def get_push_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    通知統計を取得

    送信数、クリック率などの統計情報を返す
    """
    service = PushNotificationService(db)
    return service.get_stats(current_user.id)


# =============================================================================
# テスト送信
# =============================================================================


@router.post("/test")
def send_test_notification(
    data: PushNotificationTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    テスト通知を送信

    プッシュ通知が正常に動作するか確認
    """
    from ..schemas import PushNotificationType

    service = PushNotificationService(db)
    results = service.send_notification(
        user_id=current_user.id,
        notification_type=PushNotificationType.SYSTEM,
        title="テスト通知",
        body="SocialBoostAIからのテスト通知です",
        url="/dashboard",
    )

    if not results:
        return {"status": "no_subscriptions", "message": "有効なサブスクリプションがありません"}

    sent = len([r for r in results if r.status.value == "sent"])
    failed = len([r for r in results if r.status.value == "failed"])

    return {
        "status": "ok",
        "sent": sent,
        "failed": failed,
        "details": [
            {"id": r.id, "status": r.status.value, "error": r.error_message}
            for r in results
        ],
    }


# =============================================================================
# 管理者エンドポイント
# =============================================================================


@router.post("/admin/send")
def admin_send_notification(
    data: PushNotificationSendRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    管理者: 通知を送信

    特定ユーザーまたは全ユーザーに通知を送信
    """
    service = PushNotificationService(db)

    if data.user_id:
        # 特定ユーザーに送信
        results = service.send_notification(
            user_id=data.user_id,
            notification_type=data.notification_type,
            title=data.title,
            body=data.body,
            icon=data.icon,
            url=data.url,
            data=data.data,
        )
        sent = len([r for r in results if r.status.value == "sent"])
        failed = len([r for r in results if r.status.value == "failed"])
        return {"sent": sent, "failed": failed}
    else:
        # 全ユーザーに送信
        result = service.send_to_all_users(
            notification_type=data.notification_type,
            title=data.title,
            body=data.body,
            icon=data.icon,
            url=data.url,
            data=data.data,
        )
        return result


@router.get("/admin/stats", response_model=PushNotificationStatsResponse)
def admin_get_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    管理者: 全体統計を取得
    """
    service = PushNotificationService(db)
    return service.get_stats()
