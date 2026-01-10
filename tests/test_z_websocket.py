"""
WebSocket通知機能テスト
"""

import asyncio
import json
from dataclasses import asdict
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.api.websocket import (
    AnalysisCompletePayload,
    ConnectionManager,
    Notification,
    NotificationService,
    NotificationType,
    ReportReadyPayload,
    SubscriptionUpdatePayload,
    SystemNotificationPayload,
    get_connection_manager,
    get_notification_service,
)


class TestNotificationType:
    """NotificationTypeテスト"""

    def test_notification_types_exist(self):
        """通知タイプが存在することを確認"""
        assert NotificationType.ANALYSIS_STARTED.value == "analysis_started"
        assert NotificationType.ANALYSIS_COMPLETE.value == "analysis_complete"
        assert NotificationType.REPORT_READY.value == "report_ready"
        assert NotificationType.SYSTEM_NOTIFICATION.value == "system_notification"
        assert NotificationType.SUBSCRIPTION_UPDATED.value == "subscription_updated"


class TestNotification:
    """Notificationテスト"""

    def test_notification_creation(self):
        """通知オブジェクト生成テスト"""
        notification = Notification(
            type=NotificationType.ANALYSIS_COMPLETE,
            payload={"analysis_id": "test_123"},
        )

        assert notification.type == NotificationType.ANALYSIS_COMPLETE
        assert notification.payload["analysis_id"] == "test_123"
        assert notification.timestamp != ""
        assert notification.notification_id.startswith("notif_")

    def test_notification_to_dict(self):
        """辞書変換テスト"""
        notification = Notification(
            type=NotificationType.REPORT_READY,
            payload={"report_id": "report_456"},
        )

        result = notification.to_dict()

        assert result["type"] == "report_ready"
        assert result["payload"]["report_id"] == "report_456"
        assert "timestamp" in result
        assert "notification_id" in result


class TestPayloads:
    """ペイロードテスト"""

    def test_analysis_complete_payload(self):
        """分析完了ペイロードテスト"""
        payload = AnalysisCompletePayload(
            analysis_id="analysis_123",
            platform="twitter",
            period_start="2026-01-01",
            period_end="2026-01-10",
            total_posts=100,
            engagement_rate=0.05,
            best_hour=20,
            top_hashtags=["#test", "#python"],
        )

        assert payload.analysis_id == "analysis_123"
        assert payload.platform == "twitter"
        assert payload.engagement_rate == 0.05
        assert len(payload.top_hashtags) == 2

    def test_report_ready_payload(self):
        """レポート完了ペイロードテスト"""
        payload = ReportReadyPayload(
            report_id="report_456",
            report_type="weekly",
            platform="instagram",
            period_start="2026-01-01",
            period_end="2026-01-07",
            html_url="/reports/report_456.html",
        )

        assert payload.report_id == "report_456"
        assert payload.report_type == "weekly"
        assert payload.html_url is not None

    def test_system_notification_payload(self):
        """システム通知ペイロードテスト"""
        payload = SystemNotificationPayload(
            title="メンテナンス",
            message="定期メンテナンスを実施します",
            severity="warning",
        )

        assert payload.title == "メンテナンス"
        assert payload.severity == "warning"

    def test_subscription_update_payload(self):
        """サブスクリプション更新ペイロードテスト"""
        payload = SubscriptionUpdatePayload(
            plan="pro",
            status="active",
            previous_plan="free",
        )

        assert payload.plan == "pro"
        assert payload.previous_plan == "free"


class TestConnectionManager:
    """ConnectionManagerテスト"""

    @pytest.fixture
    def manager(self):
        """ConnectionManagerインスタンス"""
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        """モックWebSocket"""
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_text = AsyncMock()
        ws.send_json = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect(self, manager, mock_websocket):
        """接続テスト"""
        connection = await manager.connect(mock_websocket, "user_123")

        assert connection.user_id == "user_123"
        assert manager.connection_count == 1
        assert manager.user_count == 1
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect(self, manager, mock_websocket):
        """切断テスト"""
        await manager.connect(mock_websocket, "user_123")
        await manager.disconnect(mock_websocket, "user_123")

        assert manager.connection_count == 0
        assert manager.user_count == 0

    @pytest.mark.asyncio
    async def test_multiple_connections_same_user(self, manager):
        """同一ユーザー複数接続テスト"""
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await manager.connect(ws1, "user_123")
        await manager.connect(ws2, "user_123")

        assert manager.connection_count == 2
        assert manager.user_count == 1

    @pytest.mark.asyncio
    async def test_send_to_user(self, manager, mock_websocket):
        """ユーザーへの送信テスト"""
        await manager.connect(mock_websocket, "user_123")

        notification = Notification(
            type=NotificationType.ANALYSIS_COMPLETE,
            payload={"test": "data"},
        )

        sent_count = await manager.send_to_user("user_123", notification)

        assert sent_count == 1
        mock_websocket.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_to_nonexistent_user(self, manager):
        """存在しないユーザーへの送信テスト"""
        notification = Notification(
            type=NotificationType.SYSTEM_NOTIFICATION,
            payload={},
        )

        sent_count = await manager.send_to_user("nonexistent", notification)

        assert sent_count == 0

    @pytest.mark.asyncio
    async def test_broadcast(self, manager):
        """ブロードキャストテスト"""
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await manager.connect(ws1, "user_1")
        await manager.connect(ws2, "user_2")

        notification = Notification(
            type=NotificationType.MAINTENANCE_SCHEDULED,
            payload={"message": "メンテナンス予定"},
        )

        sent_count = await manager.broadcast(notification)

        assert sent_count == 2
        ws1.send_text.assert_called_once()
        ws2.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_user_connected(self, manager, mock_websocket):
        """接続確認テスト"""
        assert not manager.is_user_connected("user_123")

        await manager.connect(mock_websocket, "user_123")
        assert manager.is_user_connected("user_123")

        await manager.disconnect(mock_websocket, "user_123")
        assert not manager.is_user_connected("user_123")

    def test_get_stats(self, manager):
        """統計取得テスト"""
        stats = manager.get_stats()

        assert "total_connections" in stats
        assert "unique_users" in stats
        assert "users" in stats


class TestNotificationService:
    """NotificationServiceテスト"""

    @pytest.fixture
    def mock_manager(self):
        """モックConnectionManager"""
        manager = MagicMock()
        manager.send_to_user = AsyncMock(return_value=1)
        manager.broadcast = AsyncMock(return_value=5)
        manager.is_user_connected = MagicMock(return_value=True)
        manager.get_stats = MagicMock(return_value={"total_connections": 5})
        return manager

    @pytest.fixture
    def service(self, mock_manager):
        """NotificationServiceインスタンス"""
        return NotificationService(mock_manager)

    @pytest.mark.asyncio
    async def test_notify_analysis_started(self, service, mock_manager):
        """分析開始通知テスト"""
        result = await service.notify_analysis_started(
            "user_123", "analysis_456", "twitter"
        )

        assert result == 1
        mock_manager.send_to_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_notify_analysis_progress(self, service, mock_manager):
        """分析進捗通知テスト"""
        result = await service.notify_analysis_progress(
            "user_123", "analysis_456", 50, "データ取得中"
        )

        assert result == 1
        call_args = mock_manager.send_to_user.call_args
        notification = call_args[0][1]
        assert notification.type == NotificationType.ANALYSIS_PROGRESS
        assert notification.payload["progress"] == 50

    @pytest.mark.asyncio
    async def test_notify_analysis_complete(self, service, mock_manager):
        """分析完了通知テスト"""
        payload = AnalysisCompletePayload(
            analysis_id="analysis_789",
            platform="instagram",
            period_start="2026-01-01",
            period_end="2026-01-10",
            total_posts=50,
            engagement_rate=0.08,
        )

        result = await service.notify_analysis_complete("user_123", payload)

        assert result == 1
        call_args = mock_manager.send_to_user.call_args
        notification = call_args[0][1]
        assert notification.type == NotificationType.ANALYSIS_COMPLETE
        assert notification.payload["platform"] == "instagram"

    @pytest.mark.asyncio
    async def test_notify_report_ready(self, service, mock_manager):
        """レポート完了通知テスト"""
        payload = ReportReadyPayload(
            report_id="report_123",
            report_type="monthly",
            platform="tiktok",
            period_start="2026-01-01",
            period_end="2026-01-31",
        )

        result = await service.notify_report_ready("user_123", payload)

        assert result == 1

    @pytest.mark.asyncio
    async def test_notify_subscription_updated(self, service, mock_manager):
        """サブスクリプション更新通知テスト"""
        payload = SubscriptionUpdatePayload(
            plan="business",
            status="active",
            previous_plan="pro",
        )

        result = await service.notify_subscription_updated("user_123", payload)

        assert result == 1

    @pytest.mark.asyncio
    async def test_notify_payment_failed(self, service, mock_manager):
        """支払い失敗通知テスト"""
        result = await service.notify_payment_failed("user_123", "カード残高不足")

        assert result == 1
        call_args = mock_manager.send_to_user.call_args
        notification = call_args[0][1]
        assert notification.type == NotificationType.PAYMENT_FAILED

    @pytest.mark.asyncio
    async def test_broadcast_system_notification(self, service, mock_manager):
        """システム通知ブロードキャストテスト"""
        payload = SystemNotificationPayload(
            title="新機能追加",
            message="YouTube分析機能が追加されました",
            severity="info",
        )

        result = await service.broadcast_system_notification(payload)

        assert result == 5
        mock_manager.broadcast.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_maintenance_notification(self, service, mock_manager):
        """メンテナンス通知ブロードキャストテスト"""
        result = await service.broadcast_maintenance_notification(
            scheduled_at="2026-01-15T03:00:00Z",
            duration_minutes=30,
        )

        assert result == 5

    def test_is_user_online(self, service, mock_manager):
        """オンライン確認テスト"""
        result = service.is_user_online("user_123")

        assert result is True
        mock_manager.is_user_connected.assert_called_with("user_123")

    def test_get_stats(self, service, mock_manager):
        """統計取得テスト"""
        stats = service.get_stats()

        assert stats["total_connections"] == 5


class TestSingletonInstances:
    """シングルトンインスタンステスト"""

    def test_get_connection_manager_singleton(self):
        """ConnectionManagerシングルトンテスト"""
        manager1 = get_connection_manager()
        manager2 = get_connection_manager()

        assert manager1 is manager2

    def test_get_notification_service_singleton(self):
        """NotificationServiceシングルトンテスト"""
        service1 = get_notification_service()
        service2 = get_notification_service()

        assert service1 is service2
