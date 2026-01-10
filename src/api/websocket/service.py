"""
通知サービス
"""

import logging
from dataclasses import asdict
from typing import Any, Optional

from .connection_manager import ConnectionManager, get_connection_manager
from .types import (
    AnalysisCompletePayload,
    DashboardUpdatePayload,
    MetricsUpdatePayload,
    Notification,
    NotificationType,
    ReportReadyPayload,
    SubscriptionUpdatePayload,
    SystemNotificationPayload,
)

logger = logging.getLogger(__name__)


class NotificationService:
    """
    通知サービス

    アプリケーション内から通知を送信するためのサービス
    """

    def __init__(self, connection_manager: Optional[ConnectionManager] = None):
        self._manager = connection_manager or get_connection_manager()

    async def notify_analysis_started(
        self,
        user_id: str,
        analysis_id: str,
        platform: str,
    ) -> int:
        """
        分析開始通知

        Args:
            user_id: ユーザーID
            analysis_id: 分析ID
            platform: プラットフォーム

        Returns:
            送信成功数
        """
        notification = Notification(
            type=NotificationType.ANALYSIS_STARTED,
            payload={
                "analysis_id": analysis_id,
                "platform": platform,
                "message": f"{platform}の分析を開始しました",
            },
        )
        return await self._manager.send_to_user(user_id, notification)

    async def notify_analysis_progress(
        self,
        user_id: str,
        analysis_id: str,
        progress: int,
        status: str = "",
    ) -> int:
        """
        分析進捗通知

        Args:
            user_id: ユーザーID
            analysis_id: 分析ID
            progress: 進捗率（0-100）
            status: ステータスメッセージ

        Returns:
            送信成功数
        """
        notification = Notification(
            type=NotificationType.ANALYSIS_PROGRESS,
            payload={
                "analysis_id": analysis_id,
                "progress": progress,
                "status": status,
            },
        )
        return await self._manager.send_to_user(user_id, notification)

    async def notify_analysis_complete(
        self,
        user_id: str,
        payload: AnalysisCompletePayload,
    ) -> int:
        """
        分析完了通知

        Args:
            user_id: ユーザーID
            payload: 分析完了ペイロード

        Returns:
            送信成功数
        """
        notification = Notification(
            type=NotificationType.ANALYSIS_COMPLETE,
            payload=asdict(payload),
        )
        return await self._manager.send_to_user(user_id, notification)

    async def notify_analysis_failed(
        self,
        user_id: str,
        analysis_id: str,
        error_message: str,
    ) -> int:
        """
        分析失敗通知

        Args:
            user_id: ユーザーID
            analysis_id: 分析ID
            error_message: エラーメッセージ

        Returns:
            送信成功数
        """
        notification = Notification(
            type=NotificationType.ANALYSIS_FAILED,
            payload={
                "analysis_id": analysis_id,
                "error_message": error_message,
            },
        )
        return await self._manager.send_to_user(user_id, notification)

    async def notify_report_generating(
        self,
        user_id: str,
        report_id: str,
        report_type: str,
    ) -> int:
        """
        レポート生成中通知

        Args:
            user_id: ユーザーID
            report_id: レポートID
            report_type: レポートタイプ

        Returns:
            送信成功数
        """
        notification = Notification(
            type=NotificationType.REPORT_GENERATING,
            payload={
                "report_id": report_id,
                "report_type": report_type,
                "message": f"{report_type}レポートを生成中です",
            },
        )
        return await self._manager.send_to_user(user_id, notification)

    async def notify_report_ready(
        self,
        user_id: str,
        payload: ReportReadyPayload,
    ) -> int:
        """
        レポート完了通知

        Args:
            user_id: ユーザーID
            payload: レポート完了ペイロード

        Returns:
            送信成功数
        """
        notification = Notification(
            type=NotificationType.REPORT_READY,
            payload=asdict(payload),
        )
        return await self._manager.send_to_user(user_id, notification)

    async def notify_subscription_updated(
        self,
        user_id: str,
        payload: SubscriptionUpdatePayload,
    ) -> int:
        """
        サブスクリプション更新通知

        Args:
            user_id: ユーザーID
            payload: サブスクリプション更新ペイロード

        Returns:
            送信成功数
        """
        notification = Notification(
            type=NotificationType.SUBSCRIPTION_UPDATED,
            payload=asdict(payload),
        )
        return await self._manager.send_to_user(user_id, notification)

    async def notify_payment_failed(
        self,
        user_id: str,
        reason: str = "",
    ) -> int:
        """
        支払い失敗通知

        Args:
            user_id: ユーザーID
            reason: 失敗理由

        Returns:
            送信成功数
        """
        notification = Notification(
            type=NotificationType.PAYMENT_FAILED,
            payload={
                "message": "支払いに失敗しました。支払い方法を確認してください。",
                "reason": reason,
            },
        )
        return await self._manager.send_to_user(user_id, notification)

    async def send_system_notification(
        self,
        user_id: str,
        payload: SystemNotificationPayload,
    ) -> int:
        """
        システム通知を送信

        Args:
            user_id: ユーザーID
            payload: システム通知ペイロード

        Returns:
            送信成功数
        """
        notification = Notification(
            type=NotificationType.SYSTEM_NOTIFICATION,
            payload=asdict(payload),
        )
        return await self._manager.send_to_user(user_id, notification)

    async def broadcast_system_notification(
        self,
        payload: SystemNotificationPayload,
    ) -> int:
        """
        全ユーザーにシステム通知をブロードキャスト

        Args:
            payload: システム通知ペイロード

        Returns:
            送信成功数
        """
        notification = Notification(
            type=NotificationType.SYSTEM_NOTIFICATION,
            payload=asdict(payload),
        )
        return await self._manager.broadcast(notification)

    async def broadcast_maintenance_notification(
        self,
        scheduled_at: str,
        duration_minutes: int,
        message: str = "",
    ) -> int:
        """
        メンテナンス通知をブロードキャスト

        Args:
            scheduled_at: メンテナンス開始予定時刻（ISO形式）
            duration_minutes: メンテナンス予定時間（分）
            message: 追加メッセージ

        Returns:
            送信成功数
        """
        notification = Notification(
            type=NotificationType.MAINTENANCE_SCHEDULED,
            payload={
                "scheduled_at": scheduled_at,
                "duration_minutes": duration_minutes,
                "message": message or f"メンテナンスを実施します（約{duration_minutes}分）",
            },
        )
        return await self._manager.broadcast(notification)

    async def send_dashboard_update(
        self,
        user_id: str,
        payload: DashboardUpdatePayload,
    ) -> int:
        """
        ダッシュボード更新通知

        Args:
            user_id: ユーザーID
            payload: ダッシュボード更新ペイロード

        Returns:
            送信成功数
        """
        notification = Notification(
            type=NotificationType.DASHBOARD_UPDATE,
            payload=asdict(payload),
        )
        return await self._manager.send_to_user(user_id, notification)

    async def send_metrics_update(
        self,
        user_id: str,
        payload: MetricsUpdatePayload,
    ) -> int:
        """
        メトリクス更新通知

        Args:
            user_id: ユーザーID
            payload: メトリクス更新ペイロード

        Returns:
            送信成功数
        """
        notification = Notification(
            type=NotificationType.METRICS_UPDATE,
            payload=asdict(payload),
        )
        return await self._manager.send_to_user(user_id, notification)

    def is_user_online(self, user_id: str) -> bool:
        """ユーザーがオンラインか確認"""
        return self._manager.is_user_connected(user_id)

    def get_stats(self) -> dict[str, Any]:
        """接続統計を取得"""
        return self._manager.get_stats()


# シングルトンインスタンス
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """NotificationServiceインスタンスを取得"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
