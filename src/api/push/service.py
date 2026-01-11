"""
プッシュ通知サービス

Web Push API を使用したプッシュ通知の送信・管理
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

# pywebpushはオプショナル（テスト環境などでインストールできない場合がある）
try:
    from pywebpush import WebPushException, webpush
    HAS_WEBPUSH = True
except ImportError:
    HAS_WEBPUSH = False
    WebPushException = Exception  # フォールバック
    webpush = None  # type: ignore

from ..db.models import PushNotificationLog, PushSubscription, User
from ..schemas import (
    PushNotificationLogResponse,
    PushNotificationLogStatus,
    PushNotificationLogsResponse,
    PushNotificationStatsResponse,
    PushNotificationType,
    PushSubscriptionCreate,
    PushSubscriptionListResponse,
    PushSubscriptionResponse,
    PushSubscriptionUpdate,
)

logger = logging.getLogger(__name__)


class PushNotificationService:
    """プッシュ通知サービス"""

    def __init__(self, db: Session):
        self.db = db
        # VAPID設定（環境変数から取得）
        self.vapid_private_key = os.getenv("VAPID_PRIVATE_KEY", "")
        self.vapid_public_key = os.getenv("VAPID_PUBLIC_KEY", "")
        self.vapid_claims = {
            "sub": os.getenv("VAPID_SUBJECT", "mailto:admin@socialboostai.com")
        }

    def get_vapid_public_key(self) -> str:
        """VAPID公開鍵を取得"""
        return self.vapid_public_key

    # ==========================================================================
    # サブスクリプション管理
    # ==========================================================================

    def create_subscription(
        self, user_id: str, data: PushSubscriptionCreate
    ) -> PushSubscriptionResponse:
        """プッシュ通知サブスクリプションを登録"""
        # 既存のエンドポイントを確認（既に登録されている場合は更新）
        existing = self.db.execute(
            select(PushSubscription).where(
                PushSubscription.endpoint == data.endpoint
            )
        ).scalar_one_or_none()

        if existing:
            # 既存のサブスクリプションを更新
            existing.user_id = user_id
            existing.p256dh_key = data.keys.p256dh
            existing.auth_key = data.keys.auth
            existing.device_type = data.device_type
            existing.browser = data.browser
            existing.os = data.os
            existing.device_name = data.device_name
            if data.notification_types:
                existing.notification_types = json.dumps(
                    [t.value for t in data.notification_types]
                )
            existing.enabled = True
            existing.updated_at = datetime.now(timezone.utc)
            subscription = existing
        else:
            # 新規サブスクリプション作成
            notification_types = (
                [t.value for t in data.notification_types]
                if data.notification_types
                else []
            )
            subscription = PushSubscription(
                user_id=user_id,
                endpoint=data.endpoint,
                p256dh_key=data.keys.p256dh,
                auth_key=data.keys.auth,
                device_type=data.device_type,
                browser=data.browser,
                os=data.os,
                device_name=data.device_name,
                notification_types=json.dumps(notification_types),
                enabled=True,
            )
            self.db.add(subscription)

        self.db.commit()
        self.db.refresh(subscription)

        return self._to_subscription_response(subscription)

    def get_subscriptions(self, user_id: str) -> PushSubscriptionListResponse:
        """ユーザーのサブスクリプション一覧を取得"""
        query = select(PushSubscription).where(
            PushSubscription.user_id == user_id
        ).order_by(PushSubscription.created_at.desc())

        subscriptions = self.db.execute(query).scalars().all()

        return PushSubscriptionListResponse(
            items=[self._to_subscription_response(s) for s in subscriptions],
            total=len(subscriptions),
        )

    def get_subscription(
        self, subscription_id: str, user_id: str
    ) -> Optional[PushSubscriptionResponse]:
        """サブスクリプションを取得"""
        subscription = self.db.execute(
            select(PushSubscription).where(
                PushSubscription.id == subscription_id,
                PushSubscription.user_id == user_id,
            )
        ).scalar_one_or_none()

        if not subscription:
            return None

        return self._to_subscription_response(subscription)

    def update_subscription(
        self, subscription_id: str, user_id: str, data: PushSubscriptionUpdate
    ) -> Optional[PushSubscriptionResponse]:
        """サブスクリプションを更新"""
        subscription = self.db.execute(
            select(PushSubscription).where(
                PushSubscription.id == subscription_id,
                PushSubscription.user_id == user_id,
            )
        ).scalar_one_or_none()

        if not subscription:
            return None

        if data.enabled is not None:
            subscription.enabled = data.enabled
        if data.device_name is not None:
            subscription.device_name = data.device_name
        if data.notification_types is not None:
            subscription.notification_types = json.dumps(
                [t.value for t in data.notification_types]
            )

        subscription.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(subscription)

        return self._to_subscription_response(subscription)

    def delete_subscription(self, subscription_id: str, user_id: str) -> bool:
        """サブスクリプションを削除"""
        subscription = self.db.execute(
            select(PushSubscription).where(
                PushSubscription.id == subscription_id,
                PushSubscription.user_id == user_id,
            )
        ).scalar_one_or_none()

        if not subscription:
            return False

        self.db.delete(subscription)
        self.db.commit()
        return True

    def delete_subscription_by_endpoint(self, endpoint: str) -> bool:
        """エンドポイントでサブスクリプションを削除（無効になったサブスク用）"""
        subscription = self.db.execute(
            select(PushSubscription).where(PushSubscription.endpoint == endpoint)
        ).scalar_one_or_none()

        if not subscription:
            return False

        self.db.delete(subscription)
        self.db.commit()
        return True

    # ==========================================================================
    # 通知送信
    # ==========================================================================

    def send_notification(
        self,
        user_id: str,
        notification_type: PushNotificationType,
        title: str,
        body: Optional[str] = None,
        icon: Optional[str] = None,
        url: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> list[PushNotificationLogResponse]:
        """ユーザーに通知を送信"""
        # ユーザーの有効なサブスクリプションを取得
        subscriptions = self.db.execute(
            select(PushSubscription).where(
                PushSubscription.user_id == user_id,
                PushSubscription.enabled == True,  # noqa: E712
            )
        ).scalars().all()

        results = []
        for subscription in subscriptions:
            # 通知タイプのフィルタリング
            allowed_types = json.loads(subscription.notification_types or "[]")
            if allowed_types and notification_type.value not in allowed_types:
                continue

            # 通知ログ作成
            log = PushNotificationLog(
                user_id=user_id,
                subscription_id=subscription.id,
                notification_type=notification_type.value,
                title=title,
                body=body,
                icon=icon or "/icons/icon-192x192.svg",
                url=url,
                data=json.dumps(data or {}),
                status="pending",
            )
            self.db.add(log)
            self.db.flush()

            # Web Push送信
            try:
                self._send_webpush(
                    subscription=subscription,
                    title=title,
                    body=body,
                    icon=icon,
                    url=url,
                    data=data,
                    notification_type=notification_type.value,
                )
                log.status = "sent"
                log.sent_at = datetime.now(timezone.utc)
                subscription.last_used_at = datetime.now(timezone.utc)
            except WebPushException as e:
                logger.error(f"プッシュ通知送信エラー: {e}")
                log.status = "failed"
                log.error_message = str(e)

                # 410 Gone の場合はサブスクリプションを削除
                if HAS_WEBPUSH and hasattr(e, 'response') and e.response and e.response.status_code == 410:
                    log.subscription_id = None  # 削除前にNULLに設定
                    self.db.delete(subscription)
            except Exception as e:
                logger.error(f"プッシュ通知送信エラー: {e}")
                log.status = "failed"
                log.error_message = str(e)

                # 410 Gone の場合はサブスクリプションを削除（一般例外でも対応）
                if hasattr(e, 'response') and e.response and e.response.status_code == 410:
                    log.subscription_id = None  # 削除前にNULLに設定
                    self.db.delete(subscription)

            self.db.commit()
            # logオブジェクトがセッションに残っている場合のみrefresh
            try:
                self.db.refresh(log)
            except Exception:
                # セッションから切り離された場合は再取得
                refreshed_log = self.db.execute(
                    select(PushNotificationLog).where(PushNotificationLog.id == log.id)
                ).scalar_one_or_none()
                if refreshed_log:
                    log = refreshed_log
            results.append(self._to_log_response(log))

        return results

    def send_to_all_users(
        self,
        notification_type: PushNotificationType,
        title: str,
        body: Optional[str] = None,
        icon: Optional[str] = None,
        url: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> dict[str, int]:
        """全ユーザーに通知を送信（管理者用）"""
        # 有効なサブスクリプションを持つユーザーを取得
        user_ids = self.db.execute(
            select(PushSubscription.user_id).where(
                PushSubscription.enabled == True  # noqa: E712
            ).distinct()
        ).scalars().all()

        sent = 0
        failed = 0

        for user_id in user_ids:
            results = self.send_notification(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                body=body,
                icon=icon,
                url=url,
                data=data,
            )
            for result in results:
                if result.status == PushNotificationLogStatus.SENT:
                    sent += 1
                else:
                    failed += 1

        return {"sent": sent, "failed": failed}

    def _send_webpush(
        self,
        subscription: PushSubscription,
        title: str,
        body: Optional[str],
        icon: Optional[str],
        url: Optional[str],
        data: Optional[dict],
        notification_type: str,
    ) -> None:
        """Web Push通知を送信"""
        if not HAS_WEBPUSH:
            logger.warning("pywebpushがインストールされていません")
            raise Exception("pywebpush not installed")

        if not self.vapid_private_key:
            logger.warning("VAPID秘密鍵が設定されていません")
            return

        payload = {
            "title": title,
            "body": body or "",
            "icon": icon or "/icons/icon-192x192.svg",
            "badge": "/icons/icon-72x72.svg",
            "tag": notification_type,
            "data": {
                "url": url or "/",
                "type": notification_type,
                **(data or {}),
            },
        }

        subscription_info = {
            "endpoint": subscription.endpoint,
            "keys": {
                "p256dh": subscription.p256dh_key,
                "auth": subscription.auth_key,
            },
        }

        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload),
            vapid_private_key=self.vapid_private_key,
            vapid_claims=self.vapid_claims,
        )

    # ==========================================================================
    # 通知ログ
    # ==========================================================================

    def get_notification_logs(
        self,
        user_id: str,
        page: int = 1,
        per_page: int = 20,
        notification_type: Optional[str] = None,
    ) -> PushNotificationLogsResponse:
        """通知ログを取得"""
        query = select(PushNotificationLog).where(
            PushNotificationLog.user_id == user_id
        )

        if notification_type:
            query = query.where(
                PushNotificationLog.notification_type == notification_type
            )

        # 総件数
        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_query).scalar() or 0

        # ページネーション
        query = query.order_by(PushNotificationLog.created_at.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)

        logs = self.db.execute(query).scalars().all()

        return PushNotificationLogsResponse(
            items=[self._to_log_response(log) for log in logs],
            total=total,
            page=page,
            per_page=per_page,
            pages=(total + per_page - 1) // per_page,
        )

    def mark_notification_clicked(self, log_id: str, user_id: str) -> bool:
        """通知をクリック済みにする"""
        log = self.db.execute(
            select(PushNotificationLog).where(
                PushNotificationLog.id == log_id,
                PushNotificationLog.user_id == user_id,
            )
        ).scalar_one_or_none()

        if not log:
            return False

        log.status = "clicked"
        log.clicked_at = datetime.now(timezone.utc)
        self.db.commit()
        return True

    # ==========================================================================
    # 統計
    # ==========================================================================

    def get_stats(self, user_id: Optional[str] = None) -> PushNotificationStatsResponse:
        """通知統計を取得"""
        # サブスクリプション統計
        sub_query = select(PushSubscription)
        if user_id:
            sub_query = sub_query.where(PushSubscription.user_id == user_id)

        subscriptions = self.db.execute(sub_query).scalars().all()
        total_subscriptions = len(subscriptions)
        active_subscriptions = len([s for s in subscriptions if s.enabled])

        # デバイス別統計
        by_device: dict[str, int] = {}
        for sub in subscriptions:
            device = sub.device_type or "unknown"
            by_device[device] = by_device.get(device, 0) + 1

        # 通知ログ統計
        log_query = select(PushNotificationLog)
        if user_id:
            log_query = log_query.where(PushNotificationLog.user_id == user_id)

        logs = self.db.execute(log_query).scalars().all()

        total_sent = len([l for l in logs if l.status == "sent"])
        total_clicked = len([l for l in logs if l.status == "clicked"])
        total_failed = len([l for l in logs if l.status == "failed"])

        click_rate = (total_clicked / total_sent * 100) if total_sent > 0 else 0.0

        # タイプ別統計
        by_type: dict[str, int] = {}
        for log in logs:
            by_type[log.notification_type] = by_type.get(log.notification_type, 0) + 1

        return PushNotificationStatsResponse(
            total_subscriptions=total_subscriptions,
            active_subscriptions=active_subscriptions,
            total_sent=total_sent,
            total_clicked=total_clicked,
            total_failed=total_failed,
            click_rate=round(click_rate, 2),
            by_type=by_type,
            by_device=by_device,
        )

    # ==========================================================================
    # ヘルパー
    # ==========================================================================

    def _to_subscription_response(
        self, subscription: PushSubscription
    ) -> PushSubscriptionResponse:
        """サブスクリプションをレスポンスに変換"""
        notification_types = json.loads(subscription.notification_types or "[]")
        return PushSubscriptionResponse(
            id=subscription.id,
            endpoint=subscription.endpoint,
            device_type=subscription.device_type,
            browser=subscription.browser,
            os=subscription.os,
            device_name=subscription.device_name,
            enabled=subscription.enabled,
            notification_types=notification_types,
            last_used_at=subscription.last_used_at,
            created_at=subscription.created_at,
        )

    def _to_log_response(self, log: PushNotificationLog) -> PushNotificationLogResponse:
        """ログをレスポンスに変換"""
        return PushNotificationLogResponse(
            id=log.id,
            notification_type=log.notification_type,
            title=log.title,
            body=log.body,
            url=log.url,
            status=PushNotificationLogStatus(log.status),
            error_message=log.error_message,
            sent_at=log.sent_at,
            clicked_at=log.clicked_at,
            created_at=log.created_at,
        )


# =============================================================================
# 便利関数（他モジュールから呼び出し用）
# =============================================================================


def notify_analysis_complete(db: Session, user_id: str, analysis_id: str) -> None:
    """分析完了通知を送信"""
    service = PushNotificationService(db)
    service.send_notification(
        user_id=user_id,
        notification_type=PushNotificationType.ANALYSIS_COMPLETE,
        title="分析が完了しました",
        body="ダッシュボードで結果を確認できます",
        url=f"/dashboard?analysis={analysis_id}",
        data={"analysis_id": analysis_id},
    )


def notify_report_ready(db: Session, user_id: str, report_id: str) -> None:
    """レポート完了通知を送信"""
    service = PushNotificationService(db)
    service.send_notification(
        user_id=user_id,
        notification_type=PushNotificationType.REPORT_READY,
        title="レポートが完成しました",
        body="ダウンロードできます",
        url=f"/reports?id={report_id}",
        data={"report_id": report_id},
    )


def notify_scheduled_post_published(
    db: Session, user_id: str, post_id: str, platform: str
) -> None:
    """投稿公開通知を送信"""
    service = PushNotificationService(db)
    service.send_notification(
        user_id=user_id,
        notification_type=PushNotificationType.SCHEDULED_POST_PUBLISHED,
        title=f"{platform}への投稿が公開されました",
        body="予定通り投稿されました",
        url=f"/schedule?post={post_id}",
        data={"post_id": post_id, "platform": platform},
    )


def notify_scheduled_post_failed(
    db: Session, user_id: str, post_id: str, platform: str, error: str
) -> None:
    """投稿失敗通知を送信"""
    service = PushNotificationService(db)
    service.send_notification(
        user_id=user_id,
        notification_type=PushNotificationType.SCHEDULED_POST_FAILED,
        title=f"{platform}への投稿に失敗しました",
        body=error[:100] if error else "詳細を確認してください",
        url=f"/schedule?post={post_id}",
        data={"post_id": post_id, "platform": platform, "error": error},
    )


def notify_weekly_summary(
    db: Session, user_id: str, summary: dict
) -> None:
    """週次サマリー通知を送信"""
    service = PushNotificationService(db)
    service.send_notification(
        user_id=user_id,
        notification_type=PushNotificationType.WEEKLY_SUMMARY,
        title="今週のパフォーマンスサマリー",
        body=f"エンゲージメント: {summary.get('engagement_rate', 0):.1f}%",
        url="/dashboard",
        data=summary,
    )


def notify_engagement_alert(
    db: Session, user_id: str, platform: str, metric: str, change: float
) -> None:
    """エンゲージメントアラート通知を送信"""
    direction = "上昇" if change > 0 else "低下"
    service = PushNotificationService(db)
    service.send_notification(
        user_id=user_id,
        notification_type=PushNotificationType.ENGAGEMENT_ALERT,
        title=f"{platform}の{metric}が{abs(change):.1f}%{direction}",
        body="詳細を確認してください",
        url=f"/analytics?platform={platform.lower()}",
        data={"platform": platform, "metric": metric, "change": change},
    )
