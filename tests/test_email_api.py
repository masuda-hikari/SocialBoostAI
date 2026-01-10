"""
メールAPI エンドポイントのテスト
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch

from fastapi.testclient import TestClient

from src.api.main import app
from src.api.dependencies import get_current_user
from src.api.email import get_email_service


@pytest.fixture
def mock_current_user():
    """現在のユーザーをモック"""
    user = MagicMock()
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.plan = "pro"
    user.is_active = True
    return user


@pytest.fixture
def mock_email_service():
    """メールサービスをモック"""
    service = MagicMock()
    service.is_enabled = True
    service.send_async = AsyncMock(return_value=True)
    service.send_weekly_report_async = AsyncMock(return_value=True)
    return service


@pytest.fixture
def client(mock_current_user, mock_email_service):
    """テストクライアント（依存性オーバーライド付き）"""
    app.dependency_overrides[get_current_user] = lambda: mock_current_user
    app.dependency_overrides[get_email_service] = lambda: mock_email_service
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestEmailStatusEndpoint:
    """メール状態取得エンドポイントのテスト"""

    def test_status_enabled(self, client):
        """メール送信が有効な場合"""
        response = client.get("/api/v1/email/status")

        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is True
        assert "有効" in data["message"]

    def test_status_disabled(self, mock_current_user):
        """メール送信が無効な場合"""
        mock_service = MagicMock()
        mock_service.is_enabled = False

        app.dependency_overrides[get_current_user] = lambda: mock_current_user
        app.dependency_overrides[get_email_service] = lambda: mock_service

        client = TestClient(app)
        response = client.get("/api/v1/email/status")

        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False
        assert "構成されていません" in data["message"]

        app.dependency_overrides.clear()


class TestSendTestEmailEndpoint:
    """テストメール送信エンドポイントのテスト"""

    def test_send_test_email_welcome(self, client):
        """ウェルカムテストメール送信"""
        response = client.post(
            "/api/v1/email/test",
            json={"template_type": "welcome"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "welcome" in data["message"]

    def test_send_test_email_analysis_complete(self, client):
        """分析完了テストメール送信"""
        response = client.post(
            "/api/v1/email/test",
            json={"template_type": "analysis_complete"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_send_test_email_weekly_report(self, client):
        """週次レポートテストメール送信"""
        response = client.post(
            "/api/v1/email/test",
            json={"template_type": "weekly_report"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_send_test_email_engagement_alert(self, client):
        """エンゲージメントアラートテストメール送信"""
        response = client.post(
            "/api/v1/email/test",
            json={"template_type": "engagement_alert"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_send_test_email_invalid_template(self, client):
        """不明なテンプレート種別"""
        response = client.post(
            "/api/v1/email/test",
            json={"template_type": "invalid_type"},
        )

        assert response.status_code == 400
        assert "不明なテンプレート種別" in response.json()["detail"]

    def test_send_test_email_service_disabled(self, mock_current_user):
        """メールサービスが無効な場合"""
        mock_service = MagicMock()
        mock_service.is_enabled = False

        app.dependency_overrides[get_current_user] = lambda: mock_current_user
        app.dependency_overrides[get_email_service] = lambda: mock_service

        client = TestClient(app)
        response = client.post(
            "/api/v1/email/test",
            json={"template_type": "welcome"},
        )

        assert response.status_code == 503
        assert "メール送信が無効" in response.json()["detail"]

        app.dependency_overrides.clear()


class TestWeeklyReportEndpoint:
    """週次レポート送信エンドポイントのテスト"""

    def test_send_weekly_report_success(self, client):
        """週次レポート送信成功"""
        response = client.post("/api/v1/email/send-weekly-report")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "週次レポート" in data["message"]

    def test_send_weekly_report_free_plan_forbidden(self, mock_email_service):
        """Freeプランでは週次レポート送信不可"""
        free_user = MagicMock()
        free_user.id = 1
        free_user.username = "freeuser"
        free_user.email = "free@example.com"
        free_user.plan = "free"
        free_user.is_active = True

        app.dependency_overrides[get_current_user] = lambda: free_user
        app.dependency_overrides[get_email_service] = lambda: mock_email_service

        client = TestClient(app)
        response = client.post("/api/v1/email/send-weekly-report")

        # require_planによってForbiddenになるはず
        assert response.status_code == 403
        assert "pro" in response.json()["detail"].lower()

        app.dependency_overrides.clear()


class TestEmailPreferencesEndpoint:
    """メール通知設定エンドポイントのテスト"""

    def test_get_preferences(self, client):
        """設定取得"""
        response = client.get("/api/v1/email/preferences")

        assert response.status_code == 200
        data = response.json()
        assert "weekly_report" in data
        assert "monthly_report" in data
        assert "analysis_complete" in data
        assert "engagement_alerts" in data
        assert "billing_notifications" in data
        assert "updated_at" in data

    def test_update_preferences(self, client):
        """設定更新"""
        response = client.put(
            "/api/v1/email/preferences",
            json={
                "weekly_report": True,
                "monthly_report": False,
                "analysis_complete": True,
                "engagement_alerts": False,
                "billing_notifications": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["weekly_report"] is True
        assert data["monthly_report"] is False
        assert data["engagement_alerts"] is False


class TestEmailTemplateTypes:
    """メールテンプレート種別のテスト"""

    def test_all_template_types_have_methods(self):
        """すべてのテンプレート種別に対応するメソッドがあることを確認"""
        from src.api.email.templates import EmailTemplateType, EmailTemplateManager

        # 各テンプレート種別にメソッドが存在することを確認
        template_methods = {
            EmailTemplateType.WELCOME: "welcome",
            EmailTemplateType.PASSWORD_RESET: "password_reset",
            EmailTemplateType.ANALYSIS_COMPLETE: "analysis_complete",
            EmailTemplateType.WEEKLY_REPORT: "weekly_report",
            EmailTemplateType.MONTHLY_REPORT: "monthly_report",
            EmailTemplateType.SUBSCRIPTION_CREATED: "subscription_created",
            EmailTemplateType.PAYMENT_FAILED: "payment_failed",
            EmailTemplateType.ENGAGEMENT_ALERT: "engagement_alert",
        }

        for template_type, method_name in template_methods.items():
            assert hasattr(EmailTemplateManager, method_name), (
                f"EmailTemplateManagerに{method_name}メソッドがありません"
            )
