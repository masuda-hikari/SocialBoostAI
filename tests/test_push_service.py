"""
プッシュ通知サービス テスト
"""

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

# pywebpushはオプショナル
try:
    from pywebpush import WebPushException
except ImportError:
    WebPushException = Exception

from src.api.db.models import PushNotificationLog, PushSubscription, User
from src.api.push.service import (
    PushNotificationService,
    notify_analysis_complete,
    notify_engagement_alert,
    notify_report_ready,
    notify_scheduled_post_failed,
    notify_scheduled_post_published,
    notify_weekly_summary,
)
from src.api.schemas import (
    PushNotificationLogStatus,
    PushNotificationType,
    PushSubscriptionCreate,
    PushSubscriptionKeys,
    PushSubscriptionUpdate,
)


class TestPushNotificationService:
    """PushNotificationServiceテスト"""

    def test_get_vapid_public_key(self, db_session):
        """VAPID公開鍵取得テスト"""
        with patch.dict("os.environ", {"VAPID_PUBLIC_KEY": "test_public_key_value"}):
            service = PushNotificationService(db_session)
            key = service.get_vapid_public_key()
            assert key == "test_public_key_value"

    def test_create_subscription(self, db_session, test_user):
        """サブスクリプション作成テスト"""
        service = PushNotificationService(db_session)

        data = PushSubscriptionCreate(
            endpoint="https://push.example.com/service-test",
            keys=PushSubscriptionKeys(p256dh="test_p256dh", auth="test_auth"),
            device_type="desktop",
            browser="chrome",
            os="windows",
            device_name="テストPC",
            notification_types=[
                PushNotificationType.ANALYSIS_COMPLETE,
                PushNotificationType.REPORT_READY,
            ],
        )

        result = service.create_subscription(test_user.id, data)

        assert result.endpoint == data.endpoint
        assert result.device_type == "desktop"
        assert result.browser == "chrome"
        assert result.enabled is True
        assert "analysis_complete" in result.notification_types

    def test_create_subscription_update_existing(self, db_session, test_user):
        """既存サブスクリプション更新テスト"""
        service = PushNotificationService(db_session)
        endpoint = "https://push.example.com/update-existing"

        # 1回目の作成
        data1 = PushSubscriptionCreate(
            endpoint=endpoint,
            keys=PushSubscriptionKeys(p256dh="key1", auth="auth1"),
            device_name="デバイス1",
        )
        result1 = service.create_subscription(test_user.id, data1)

        # 2回目の作成（同じエンドポイント）
        data2 = PushSubscriptionCreate(
            endpoint=endpoint,
            keys=PushSubscriptionKeys(p256dh="key2", auth="auth2"),
            device_name="デバイス2",
        )
        result2 = service.create_subscription(test_user.id, data2)

        # 同じIDで更新される
        assert result1.id == result2.id
        assert result2.device_name == "デバイス2"

    def test_get_subscriptions(self, db_session, test_user):
        """サブスクリプション一覧取得テスト"""
        # サブスクリプションを複数作成
        for i in range(3):
            sub = PushSubscription(
                user_id=test_user.id,
                endpoint=f"https://push.example.com/list-{i}",
                p256dh_key=f"key_{i}",
                auth_key=f"auth_{i}",
                notification_types="[]",
            )
            db_session.add(sub)
        db_session.commit()

        service = PushNotificationService(db_session)
        result = service.get_subscriptions(test_user.id)

        assert result.total >= 3
        assert len(result.items) >= 3

    def test_get_subscription(self, db_session, test_user):
        """サブスクリプション取得テスト"""
        sub = PushSubscription(
            user_id=test_user.id,
            endpoint="https://push.example.com/get-single",
            p256dh_key="test_key",
            auth_key="test_auth",
            device_name="単体取得テスト",
            notification_types="[]",
        )
        db_session.add(sub)
        db_session.commit()

        service = PushNotificationService(db_session)
        result = service.get_subscription(sub.id, test_user.id)

        assert result is not None
        assert result.device_name == "単体取得テスト"

    def test_get_subscription_not_found(self, db_session, test_user):
        """存在しないサブスクリプション取得テスト"""
        service = PushNotificationService(db_session)
        result = service.get_subscription("nonexistent", test_user.id)
        assert result is None

    def test_update_subscription(self, db_session, test_user):
        """サブスクリプション更新テスト"""
        sub = PushSubscription(
            user_id=test_user.id,
            endpoint="https://push.example.com/update-test",
            p256dh_key="test_key",
            auth_key="test_auth",
            enabled=True,
            notification_types="[]",
        )
        db_session.add(sub)
        db_session.commit()

        service = PushNotificationService(db_session)
        update_data = PushSubscriptionUpdate(
            enabled=False,
            device_name="更新後の名前",
            notification_types=[PushNotificationType.SYSTEM],
        )

        result = service.update_subscription(sub.id, test_user.id, update_data)

        assert result is not None
        assert result.enabled is False
        assert result.device_name == "更新後の名前"
        assert "system" in result.notification_types

    def test_delete_subscription(self, db_session, test_user):
        """サブスクリプション削除テスト"""
        sub = PushSubscription(
            user_id=test_user.id,
            endpoint="https://push.example.com/delete-test",
            p256dh_key="test_key",
            auth_key="test_auth",
            notification_types="[]",
        )
        db_session.add(sub)
        db_session.commit()
        sub_id = sub.id

        service = PushNotificationService(db_session)
        result = service.delete_subscription(sub_id, test_user.id)

        assert result is True

        # 削除確認
        check = service.get_subscription(sub_id, test_user.id)
        assert check is None

    def test_delete_subscription_by_endpoint(self, db_session, test_user):
        """エンドポイントによるサブスクリプション削除テスト"""
        endpoint = "https://push.example.com/delete-by-endpoint"
        sub = PushSubscription(
            user_id=test_user.id,
            endpoint=endpoint,
            p256dh_key="test_key",
            auth_key="test_auth",
            notification_types="[]",
        )
        db_session.add(sub)
        db_session.commit()

        service = PushNotificationService(db_session)
        result = service.delete_subscription_by_endpoint(endpoint)

        assert result is True


class TestPushNotificationSending:
    """通知送信テスト"""

    @patch("src.api.push.service.HAS_WEBPUSH", True)
    @patch("src.api.push.service.webpush")
    def test_send_notification_success(self, mock_webpush, db_session, test_user):
        """通知送信成功テスト"""
        # サブスクリプション作成
        sub = PushSubscription(
            user_id=test_user.id,
            endpoint="https://push.example.com/send-test",
            p256dh_key="test_key",
            auth_key="test_auth",
            enabled=True,
            notification_types="[]",
        )
        db_session.add(sub)
        db_session.commit()

        with patch.dict(
            "os.environ",
            {
                "VAPID_PRIVATE_KEY": "test_private_key",
                "VAPID_PUBLIC_KEY": "test_public_key",
            },
        ):
            service = PushNotificationService(db_session)
            results = service.send_notification(
                user_id=test_user.id,
                notification_type=PushNotificationType.ANALYSIS_COMPLETE,
                title="テスト通知",
                body="テスト本文",
                url="/dashboard",
            )

        assert len(results) >= 1
        assert results[0].status == PushNotificationLogStatus.SENT
        mock_webpush.assert_called_once()

    @patch("src.api.push.service.HAS_WEBPUSH", True)
    @patch("src.api.push.service.webpush")
    def test_send_notification_filtered_by_type(
        self, mock_webpush, db_session, test_user
    ):
        """通知タイプフィルタリングテスト"""
        # analysis_completeのみ受信するサブスクリプション
        sub = PushSubscription(
            user_id=test_user.id,
            endpoint="https://push.example.com/filter-test",
            p256dh_key="test_key",
            auth_key="test_auth",
            enabled=True,
            notification_types=json.dumps(["analysis_complete"]),
        )
        db_session.add(sub)
        db_session.commit()

        with patch.dict(
            "os.environ",
            {"VAPID_PRIVATE_KEY": "test_private_key"},
        ):
            service = PushNotificationService(db_session)

            # analysis_complete は送信される
            results1 = service.send_notification(
                user_id=test_user.id,
                notification_type=PushNotificationType.ANALYSIS_COMPLETE,
                title="分析完了",
            )
            assert len(results1) >= 1

            # report_ready は送信されない
            results2 = service.send_notification(
                user_id=test_user.id,
                notification_type=PushNotificationType.REPORT_READY,
                title="レポート完了",
            )
            # フィルタリングされて送信されない
            assert len(results2) == 0

    @patch("src.api.push.service.HAS_WEBPUSH", True)
    @patch("src.api.push.service.webpush")
    def test_send_notification_failure(self, mock_webpush, db_session, test_user):
        """通知送信失敗テスト"""
        mock_webpush.side_effect = Exception("送信エラー")

        sub = PushSubscription(
            user_id=test_user.id,
            endpoint="https://push.example.com/fail-test",
            p256dh_key="test_key",
            auth_key="test_auth",
            enabled=True,
            notification_types="[]",
        )
        db_session.add(sub)
        db_session.commit()

        with patch.dict(
            "os.environ",
            {"VAPID_PRIVATE_KEY": "test_private_key"},
        ):
            service = PushNotificationService(db_session)
            results = service.send_notification(
                user_id=test_user.id,
                notification_type=PushNotificationType.SYSTEM,
                title="失敗テスト",
            )

        assert len(results) >= 1
        assert results[0].status == PushNotificationLogStatus.FAILED
        assert results[0].error_message is not None

    @patch("src.api.push.service.HAS_WEBPUSH", True)
    @patch("src.api.push.service.webpush")
    def test_send_notification_410_removes_subscription(
        self, mock_webpush, db_session, test_user
    ):
        """410エラー時のサブスクリプション削除テスト"""
        # 410 Gone レスポンスをモック（WebPushExceptionの代わりにモックExceptionを使用）
        mock_response = MagicMock()
        mock_response.status_code = 410
        mock_error = Exception("Gone")
        mock_error.response = mock_response
        mock_webpush.side_effect = mock_error

        sub = PushSubscription(
            user_id=test_user.id,
            endpoint="https://push.example.com/gone-test",
            p256dh_key="test_key",
            auth_key="test_auth",
            enabled=True,
            notification_types="[]",
        )
        db_session.add(sub)
        db_session.commit()
        sub_id = sub.id

        with patch.dict(
            "os.environ",
            {"VAPID_PRIVATE_KEY": "test_private_key"},
        ):
            service = PushNotificationService(db_session)
            service.send_notification(
                user_id=test_user.id,
                notification_type=PushNotificationType.SYSTEM,
                title="Goneテスト",
            )

        # サブスクリプションが削除される
        check = service.get_subscription(sub_id, test_user.id)
        assert check is None


class TestNotificationLogs:
    """通知ログテスト"""

    def test_get_notification_logs(self, db_session, test_user):
        """通知ログ取得テスト"""
        # ログを複数作成
        for i in range(5):
            log = PushNotificationLog(
                user_id=test_user.id,
                notification_type="analysis_complete",
                title=f"テスト通知{i}",
                status="sent",
            )
            db_session.add(log)
        db_session.commit()

        service = PushNotificationService(db_session)
        result = service.get_notification_logs(test_user.id, page=1, per_page=3)

        assert result.total >= 5
        assert len(result.items) == 3
        assert result.page == 1
        assert result.per_page == 3

    def test_get_notification_logs_with_type_filter(self, db_session, test_user):
        """通知ログタイプフィルタテスト"""
        log1 = PushNotificationLog(
            user_id=test_user.id,
            notification_type="analysis_complete",
            title="分析完了",
            status="sent",
        )
        log2 = PushNotificationLog(
            user_id=test_user.id,
            notification_type="report_ready",
            title="レポート完了",
            status="sent",
        )
        db_session.add_all([log1, log2])
        db_session.commit()

        service = PushNotificationService(db_session)
        result = service.get_notification_logs(
            test_user.id, notification_type="analysis_complete"
        )

        for item in result.items:
            assert item.notification_type == "analysis_complete"

    def test_mark_notification_clicked(self, db_session, test_user):
        """通知クリック記録テスト"""
        log = PushNotificationLog(
            user_id=test_user.id,
            notification_type="system",
            title="クリックテスト",
            status="sent",
        )
        db_session.add(log)
        db_session.commit()

        service = PushNotificationService(db_session)
        result = service.mark_notification_clicked(log.id, test_user.id)

        assert result is True
        db_session.refresh(log)
        assert log.status == "clicked"
        assert log.clicked_at is not None


class TestPushStats:
    """統計テスト"""

    def test_get_stats(self, db_session, test_user):
        """統計取得テスト"""
        # サブスクリプション作成
        sub1 = PushSubscription(
            user_id=test_user.id,
            endpoint="https://push.example.com/stats-1",
            p256dh_key="key1",
            auth_key="auth1",
            enabled=True,
            device_type="desktop",
            notification_types="[]",
        )
        sub2 = PushSubscription(
            user_id=test_user.id,
            endpoint="https://push.example.com/stats-2",
            p256dh_key="key2",
            auth_key="auth2",
            enabled=False,
            device_type="mobile",
            notification_types="[]",
        )
        db_session.add_all([sub1, sub2])

        # ログ作成
        log1 = PushNotificationLog(
            user_id=test_user.id,
            notification_type="analysis_complete",
            title="テスト1",
            status="sent",
        )
        log2 = PushNotificationLog(
            user_id=test_user.id,
            notification_type="analysis_complete",
            title="テスト2",
            status="clicked",
        )
        log3 = PushNotificationLog(
            user_id=test_user.id,
            notification_type="report_ready",
            title="テスト3",
            status="failed",
        )
        db_session.add_all([log1, log2, log3])
        db_session.commit()

        service = PushNotificationService(db_session)
        result = service.get_stats(test_user.id)

        assert result.total_subscriptions >= 2
        assert result.active_subscriptions >= 1
        assert result.total_sent >= 1
        assert result.total_clicked >= 1
        assert result.total_failed >= 1
        assert "analysis_complete" in result.by_type
        assert "desktop" in result.by_device or "mobile" in result.by_device


class TestConvenienceFunctions:
    """便利関数テスト"""

    @patch("src.api.push.service.PushNotificationService.send_notification")
    def test_notify_analysis_complete(self, mock_send, db_session, test_user):
        """分析完了通知テスト"""
        notify_analysis_complete(db_session, test_user.id, "analysis_123")

        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args.kwargs["notification_type"] == PushNotificationType.ANALYSIS_COMPLETE
        assert "分析" in call_args.kwargs["title"]

    @patch("src.api.push.service.PushNotificationService.send_notification")
    def test_notify_report_ready(self, mock_send, db_session, test_user):
        """レポート完了通知テスト"""
        notify_report_ready(db_session, test_user.id, "report_123")

        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args.kwargs["notification_type"] == PushNotificationType.REPORT_READY

    @patch("src.api.push.service.PushNotificationService.send_notification")
    def test_notify_scheduled_post_published(self, mock_send, db_session, test_user):
        """投稿公開通知テスト"""
        notify_scheduled_post_published(
            db_session, test_user.id, "post_123", "Twitter"
        )

        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert (
            call_args.kwargs["notification_type"]
            == PushNotificationType.SCHEDULED_POST_PUBLISHED
        )
        assert "Twitter" in call_args.kwargs["title"]

    @patch("src.api.push.service.PushNotificationService.send_notification")
    def test_notify_scheduled_post_failed(self, mock_send, db_session, test_user):
        """投稿失敗通知テスト"""
        notify_scheduled_post_failed(
            db_session, test_user.id, "post_123", "Instagram", "APIエラー"
        )

        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert (
            call_args.kwargs["notification_type"]
            == PushNotificationType.SCHEDULED_POST_FAILED
        )

    @patch("src.api.push.service.PushNotificationService.send_notification")
    def test_notify_weekly_summary(self, mock_send, db_session, test_user):
        """週次サマリー通知テスト"""
        summary = {"engagement_rate": 5.5, "total_posts": 10}
        notify_weekly_summary(db_session, test_user.id, summary)

        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert call_args.kwargs["notification_type"] == PushNotificationType.WEEKLY_SUMMARY
        assert "5.5%" in call_args.kwargs["body"]

    @patch("src.api.push.service.PushNotificationService.send_notification")
    def test_notify_engagement_alert(self, mock_send, db_session, test_user):
        """エンゲージメントアラート通知テスト"""
        notify_engagement_alert(
            db_session, test_user.id, "Twitter", "いいね数", 25.0
        )

        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert (
            call_args.kwargs["notification_type"]
            == PushNotificationType.ENGAGEMENT_ALERT
        )
        assert "25.0%" in call_args.kwargs["title"]
        assert "上昇" in call_args.kwargs["title"]
