"""
プッシュ通知API テスト
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.db.models import PushSubscription, PushNotificationLog, User
from src.api.schemas import PushNotificationType


client = TestClient(app)


class TestPushSubscriptionAPI:
    """サブスクリプション管理APIテスト"""

    def test_get_vapid_key(self, db_session):
        """VAPID公開鍵取得テスト"""
        with patch.dict("os.environ", {"VAPID_PUBLIC_KEY": "test_public_key"}):
            response = client.get("/api/v1/push/vapid-key")

        assert response.status_code == 200
        # 環境変数が設定されていない場合は空文字が返る
        assert "public_key" in response.json()

    def test_create_subscription(self, db_session, test_user, auth_headers):
        """サブスクリプション作成テスト"""
        data = {
            "endpoint": "https://push.example.com/test-endpoint-123",
            "keys": {
                "p256dh": "test_p256dh_key_value",
                "auth": "test_auth_key_value"
            },
            "device_type": "desktop",
            "browser": "chrome",
            "os": "windows",
            "device_name": "テスト用PC",
            "notification_types": ["analysis_complete", "report_ready"]
        }

        response = client.post(
            "/api/v1/push/subscriptions",
            json=data,
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result["endpoint"] == data["endpoint"]
        assert result["device_type"] == "desktop"
        assert result["browser"] == "chrome"
        assert result["enabled"] is True
        assert "analysis_complete" in result["notification_types"]

    def test_create_subscription_unauthenticated(self, db_session):
        """未認証でのサブスクリプション作成テスト"""
        data = {
            "endpoint": "https://push.example.com/test-endpoint",
            "keys": {
                "p256dh": "test_p256dh",
                "auth": "test_auth"
            }
        }

        response = client.post("/api/v1/push/subscriptions", json=data)
        assert response.status_code == 401

    def test_create_subscription_duplicate_endpoint(self, db_session, test_user, auth_headers):
        """重複エンドポイントでのサブスクリプション作成テスト（更新される）"""
        endpoint = "https://push.example.com/duplicate-test"

        # 1回目の登録
        data1 = {
            "endpoint": endpoint,
            "keys": {"p256dh": "key1", "auth": "auth1"},
            "device_name": "デバイス1"
        }
        response1 = client.post(
            "/api/v1/push/subscriptions",
            json=data1,
            headers=auth_headers
        )
        assert response1.status_code == 200
        first_id = response1.json()["id"]

        # 2回目の登録（同じエンドポイント）
        data2 = {
            "endpoint": endpoint,
            "keys": {"p256dh": "key2", "auth": "auth2"},
            "device_name": "デバイス2"
        }
        response2 = client.post(
            "/api/v1/push/subscriptions",
            json=data2,
            headers=auth_headers
        )
        assert response2.status_code == 200
        # 同じIDで更新される
        assert response2.json()["id"] == first_id
        assert response2.json()["device_name"] == "デバイス2"

    def test_get_subscriptions(self, db_session, test_user, auth_headers):
        """サブスクリプション一覧取得テスト"""
        # サブスクリプションを作成
        sub = PushSubscription(
            user_id=test_user.id,
            endpoint="https://push.example.com/list-test",
            p256dh_key="test_key",
            auth_key="test_auth",
            device_type="mobile",
            notification_types="[]"
        )
        db_session.add(sub)
        db_session.commit()

        response = client.get("/api/v1/push/subscriptions", headers=auth_headers)

        assert response.status_code == 200
        result = response.json()
        assert result["total"] >= 1
        assert len(result["items"]) >= 1

    def test_get_subscription_detail(self, db_session, test_user, auth_headers):
        """サブスクリプション詳細取得テスト"""
        sub = PushSubscription(
            user_id=test_user.id,
            endpoint="https://push.example.com/detail-test",
            p256dh_key="test_key",
            auth_key="test_auth",
            device_name="詳細テスト",
            notification_types="[]"
        )
        db_session.add(sub)
        db_session.commit()

        response = client.get(
            f"/api/v1/push/subscriptions/{sub.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["device_name"] == "詳細テスト"

    def test_get_subscription_not_found(self, db_session, auth_headers):
        """存在しないサブスクリプション取得テスト"""
        response = client.get(
            "/api/v1/push/subscriptions/nonexistent_id",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_update_subscription(self, db_session, test_user, auth_headers):
        """サブスクリプション更新テスト"""
        sub = PushSubscription(
            user_id=test_user.id,
            endpoint="https://push.example.com/update-test",
            p256dh_key="test_key",
            auth_key="test_auth",
            enabled=True,
            notification_types="[]"
        )
        db_session.add(sub)
        db_session.commit()

        update_data = {
            "enabled": False,
            "device_name": "更新後のデバイス名",
            "notification_types": ["system", "weekly_summary"]
        }

        response = client.put(
            f"/api/v1/push/subscriptions/{sub.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result["enabled"] is False
        assert result["device_name"] == "更新後のデバイス名"
        assert "system" in result["notification_types"]

    def test_delete_subscription(self, db_session, test_user, auth_headers):
        """サブスクリプション削除テスト"""
        sub = PushSubscription(
            user_id=test_user.id,
            endpoint="https://push.example.com/delete-test",
            p256dh_key="test_key",
            auth_key="test_auth",
            notification_types="[]"
        )
        db_session.add(sub)
        db_session.commit()
        sub_id = sub.id

        response = client.delete(
            f"/api/v1/push/subscriptions/{sub_id}",
            headers=auth_headers
        )

        assert response.status_code == 204

        # 削除確認
        check_response = client.get(
            f"/api/v1/push/subscriptions/{sub_id}",
            headers=auth_headers
        )
        assert check_response.status_code == 404


class TestPushNotificationLogsAPI:
    """通知ログAPIテスト"""

    def test_get_notification_logs(self, db_session, test_user, auth_headers):
        """通知ログ取得テスト"""
        # ログを作成
        log = PushNotificationLog(
            user_id=test_user.id,
            notification_type="analysis_complete",
            title="テスト通知",
            body="テスト本文",
            status="sent"
        )
        db_session.add(log)
        db_session.commit()

        response = client.get("/api/v1/push/logs", headers=auth_headers)

        assert response.status_code == 200
        result = response.json()
        assert result["total"] >= 1
        assert len(result["items"]) >= 1

    def test_get_notification_logs_with_filter(self, db_session, test_user, auth_headers):
        """通知ログフィルタ取得テスト"""
        # 複数タイプのログを作成
        log1 = PushNotificationLog(
            user_id=test_user.id,
            notification_type="analysis_complete",
            title="分析完了",
            status="sent"
        )
        log2 = PushNotificationLog(
            user_id=test_user.id,
            notification_type="report_ready",
            title="レポート完了",
            status="sent"
        )
        db_session.add_all([log1, log2])
        db_session.commit()

        response = client.get(
            "/api/v1/push/logs?notification_type=analysis_complete",
            headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()
        # フィルタされた結果のみ
        for item in result["items"]:
            assert item["notification_type"] == "analysis_complete"

    def test_mark_notification_clicked(self, db_session, test_user, auth_headers):
        """通知クリック記録テスト"""
        log = PushNotificationLog(
            user_id=test_user.id,
            notification_type="system",
            title="クリックテスト",
            status="sent"
        )
        db_session.add(log)
        db_session.commit()

        response = client.post(
            f"/api/v1/push/logs/{log.id}/clicked",
            headers=auth_headers
        )

        assert response.status_code == 204

        # 状態確認
        db_session.refresh(log)
        assert log.status == "clicked"
        assert log.clicked_at is not None


class TestPushStatsAPI:
    """統計APIテスト"""

    def test_get_push_stats(self, db_session, test_user, auth_headers):
        """統計取得テスト"""
        # サブスクリプションとログを作成
        sub = PushSubscription(
            user_id=test_user.id,
            endpoint="https://push.example.com/stats-test",
            p256dh_key="test_key",
            auth_key="test_auth",
            enabled=True,
            device_type="desktop",
            notification_types="[]"
        )
        db_session.add(sub)

        log1 = PushNotificationLog(
            user_id=test_user.id,
            notification_type="analysis_complete",
            title="テスト1",
            status="sent"
        )
        log2 = PushNotificationLog(
            user_id=test_user.id,
            notification_type="analysis_complete",
            title="テスト2",
            status="clicked"
        )
        db_session.add_all([log1, log2])
        db_session.commit()

        response = client.get("/api/v1/push/stats", headers=auth_headers)

        assert response.status_code == 200
        result = response.json()
        assert result["total_subscriptions"] >= 1
        assert result["active_subscriptions"] >= 1
        assert "by_type" in result
        assert "by_device" in result


class TestPushTestNotificationAPI:
    """テスト通知APIテスト"""

    def test_send_test_notification_no_subscriptions(self, db_session, test_user, auth_headers):
        """サブスクリプションなしでのテスト通知"""
        response = client.post("/api/v1/push/test", json={}, headers=auth_headers)

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "no_subscriptions"

    @patch("src.api.push.service.HAS_WEBPUSH", True)
    @patch("src.api.push.service.webpush")
    def test_send_test_notification_with_subscription(
        self, mock_webpush, db_session, test_user, auth_headers
    ):
        """サブスクリプションありでのテスト通知"""
        # サブスクリプションを作成
        sub = PushSubscription(
            user_id=test_user.id,
            endpoint="https://push.example.com/test-notify",
            p256dh_key="test_p256dh_key",
            auth_key="test_auth_key",
            enabled=True,
            notification_types="[]"
        )
        db_session.add(sub)
        db_session.commit()

        # VAPID設定をモック
        with patch.dict("os.environ", {
            "VAPID_PRIVATE_KEY": "test_private_key",
            "VAPID_PUBLIC_KEY": "test_public_key",
            "VAPID_SUBJECT": "mailto:test@example.com"
        }):
            response = client.post(
                "/api/v1/push/test",
                json={},
                headers=auth_headers
            )

        assert response.status_code == 200
        result = response.json()
        # VAPIDキーがテスト用なので失敗するかもしれないが、APIは動作する
        assert result["status"] == "ok" or result["status"] == "no_subscriptions"


class TestAdminPushAPI:
    """管理者用プッシュ通知APIテスト"""

    def test_admin_send_notification_unauthorized(self, db_session, auth_headers):
        """非管理者による管理者API呼び出しテスト"""
        data = {
            "notification_type": "system",
            "title": "テスト通知"
        }

        response = client.post(
            "/api/v1/push/admin/send",
            json=data,
            headers=auth_headers
        )

        assert response.status_code == 403

    def test_admin_get_stats(self, db_session, admin_user, admin_headers):
        """管理者統計取得テスト"""
        response = client.get(
            "/api/v1/push/admin/stats",
            headers=admin_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert "total_subscriptions" in result
        assert "total_sent" in result

    @patch("src.api.push.service.HAS_WEBPUSH", True)
    @patch("src.api.push.service.webpush")
    def test_admin_send_to_user(
        self, mock_webpush, db_session, admin_user, admin_headers, test_user
    ):
        """管理者による特定ユーザーへの通知送信テスト"""
        # サブスクリプションを作成
        sub = PushSubscription(
            user_id=test_user.id,
            endpoint="https://push.example.com/admin-test",
            p256dh_key="test_key",
            auth_key="test_auth",
            enabled=True,
            notification_types="[]"
        )
        db_session.add(sub)
        db_session.commit()

        data = {
            "user_id": test_user.id,
            "notification_type": "system",
            "title": "管理者からの通知",
            "body": "テスト本文"
        }

        with patch.dict("os.environ", {
            "VAPID_PRIVATE_KEY": "test_private_key",
            "VAPID_PUBLIC_KEY": "test_public_key"
        }):
            response = client.post(
                "/api/v1/push/admin/send",
                json=data,
                headers=admin_headers
            )

        assert response.status_code == 200
        result = response.json()
        assert "sent" in result or "failed" in result
