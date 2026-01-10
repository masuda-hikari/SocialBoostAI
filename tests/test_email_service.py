"""
メール通知機能のテスト
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.api.email import (
    EmailService,
    EmailTemplate,
    EmailTemplateManager,
    EmailTemplateType,
    get_email_service,
)
from src.api.email.service import EmailConfig


class TestEmailTemplateManager:
    """EmailTemplateManagerのテスト"""

    def test_welcome_template(self):
        """ウェルカムメールテンプレート生成"""
        template = EmailTemplateManager.welcome("テストユーザー")

        assert template.template_type == EmailTemplateType.WELCOME
        assert "ようこそ" in template.subject
        assert "SocialBoostAI" in template.subject
        assert "テストユーザー" in template.html_body
        assert "テストユーザー" in template.text_body
        assert "SocialBoostAI" in template.html_body

    def test_password_reset_template(self):
        """パスワードリセットメールテンプレート生成"""
        reset_url = "https://example.com/reset/abc123"
        template = EmailTemplateManager.password_reset(
            "テストユーザー", reset_url, "30分"
        )

        assert template.template_type == EmailTemplateType.PASSWORD_RESET
        assert "パスワードリセット" in template.subject
        assert reset_url in template.html_body
        assert reset_url in template.text_body
        assert "30分" in template.html_body
        assert "30分" in template.text_body

    def test_analysis_complete_template(self):
        """分析完了通知メールテンプレート生成"""
        metrics = {
            "総投稿数": "100件",
            "エンゲージメント率": "5.2%",
        }
        template = EmailTemplateManager.analysis_complete(
            "テストユーザー", "Twitter", metrics
        )

        assert template.template_type == EmailTemplateType.ANALYSIS_COMPLETE
        assert "Twitter" in template.subject
        assert "分析が完了" in template.subject
        assert "100件" in template.html_body
        assert "5.2%" in template.html_body

    def test_weekly_report_template(self):
        """週次レポートメールテンプレート生成"""
        summary = {"投稿数": "25件", "総エンゲージメント": "5,000"}
        highlights = ["エンゲージメント率向上", "フォロワー増加"]
        recommendations = ["投稿時間の最適化を推奨"]

        template = EmailTemplateManager.weekly_report(
            "テストユーザー",
            "2026/01/06 - 2026/01/12",
            summary,
            highlights,
            recommendations,
        )

        assert template.template_type == EmailTemplateType.WEEKLY_REPORT
        assert "週次レポート" in template.subject
        assert "2026/01/06" in template.subject
        assert "25件" in template.html_body
        assert "エンゲージメント率向上" in template.html_body
        assert "投稿時間の最適化を推奨" in template.html_body

    def test_monthly_report_template(self):
        """月次レポートメールテンプレート生成"""
        summary = {"投稿数": "100件", "総エンゲージメント": "20,000"}
        growth = {"エンゲージメント率": "+15%", "フォロワー": "+200"}
        top_content = [
            {"title": "AIの使い方", "engagement": "2,500"},
            {"title": "ツール紹介", "engagement": "1,800"},
        ]

        template = EmailTemplateManager.monthly_report(
            "テストユーザー", "2026年1月", summary, growth, top_content
        )

        assert template.template_type == EmailTemplateType.MONTHLY_REPORT
        assert "月次レポート" in template.subject
        assert "2026年1月" in template.subject
        assert "+15%" in template.html_body
        assert "AIの使い方" in template.html_body

    def test_subscription_created_template(self):
        """サブスクリプション開始メールテンプレート生成"""
        template = EmailTemplateManager.subscription_created(
            "テストユーザー", "Pro", "¥1,980", "2026/02/11"
        )

        assert template.template_type == EmailTemplateType.SUBSCRIPTION_CREATED
        assert "Pro" in template.subject
        assert "¥1,980" in template.html_body
        assert "2026/02/11" in template.html_body

    def test_payment_failed_template(self):
        """支払い失敗通知メールテンプレート生成"""
        template = EmailTemplateManager.payment_failed(
            "テストユーザー", "Pro", "¥1,980", "2026/01/15"
        )

        assert template.template_type == EmailTemplateType.PAYMENT_FAILED
        assert "お支払いに失敗" in template.subject
        assert "¥1,980" in template.html_body
        assert "2026/01/15" in template.html_body

    def test_engagement_alert_template(self):
        """エンゲージメントアラートメールテンプレート生成"""
        template = EmailTemplateManager.engagement_alert(
            "テストユーザー",
            "Twitter",
            "人気の投稿",
            "1,500",
            "+250%",
        )

        assert template.template_type == EmailTemplateType.ENGAGEMENT_ALERT
        assert "エンゲージメント" in template.subject
        assert "急上昇" in template.subject
        assert "人気の投稿" in template.html_body
        assert "+250%" in template.html_body


class TestEmailService:
    """EmailServiceのテスト"""

    def test_service_disabled_without_config(self):
        """設定なしではメール送信が無効になる"""
        # 環境変数をクリア
        with patch.dict("os.environ", {}, clear=True):
            service = EmailService()
            assert service.is_enabled is False

    def test_service_enabled_with_config(self):
        """設定ありではメール送信が有効になる"""
        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user",
            smtp_password="password",
            from_email="test@example.com",
        )
        service = EmailService(config=config)
        assert service.is_enabled is True

    def test_send_returns_false_when_disabled(self):
        """無効時はsend()がFalseを返す"""
        with patch.dict("os.environ", {}, clear=True):
            service = EmailService()
            template = EmailTemplateManager.welcome("テスト")
            result = service.send("test@example.com", template)
            assert result is False

    @pytest.mark.asyncio
    async def test_send_async_returns_false_when_disabled(self):
        """無効時はsend_async()がFalseを返す"""
        with patch.dict("os.environ", {}, clear=True):
            service = EmailService()
            template = EmailTemplateManager.welcome("テスト")
            result = await service.send_async("test@example.com", template)
            assert result is False

    def test_create_message(self):
        """MIMEメッセージの作成"""
        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user",
            smtp_password="password",
            from_email="noreply@example.com",
            from_name="TestApp",
        )
        service = EmailService(config=config)
        template = EmailTemplateManager.welcome("テストユーザー")

        message = service._create_message("recipient@example.com", template)

        assert message["Subject"] == template.subject
        assert "TestApp" in message["From"]
        assert "noreply@example.com" in message["From"]
        assert message["To"] == "recipient@example.com"

    @patch("smtplib.SMTP")
    def test_send_smtp_success(self, mock_smtp):
        """SMTP送信成功"""
        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user",
            smtp_password="password",
            from_email="noreply@example.com",
        )
        service = EmailService(config=config)
        template = EmailTemplateManager.welcome("テストユーザー")

        # SMTPモックの設定
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

        result = service.send("recipient@example.com", template)

        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user", "password")
        mock_server.sendmail.assert_called_once()

    @patch("smtplib.SMTP")
    def test_send_smtp_auth_error(self, mock_smtp):
        """SMTP認証エラー"""
        import smtplib

        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user",
            smtp_password="wrong_password",
            from_email="noreply@example.com",
        )
        service = EmailService(config=config)
        template = EmailTemplateManager.welcome("テストユーザー")

        # 認証エラーをシミュレート
        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Auth failed")
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

        result = service.send("recipient@example.com", template)

        assert result is False

    @pytest.mark.asyncio
    @patch("smtplib.SMTP")
    async def test_send_async_success(self, mock_smtp):
        """非同期SMTP送信成功"""
        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user",
            smtp_password="password",
            from_email="noreply@example.com",
        )
        service = EmailService(config=config)
        template = EmailTemplateManager.welcome("テストユーザー")

        # SMTPモックの設定
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

        result = await service.send_async("recipient@example.com", template)

        assert result is True

    @pytest.mark.asyncio
    @patch("smtplib.SMTP")
    async def test_send_bulk_async(self, mock_smtp):
        """一括送信"""
        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user",
            smtp_password="password",
            from_email="noreply@example.com",
        )
        service = EmailService(config=config)

        # SMTPモックの設定
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

        recipients = [
            ("user1@example.com", EmailTemplateManager.welcome("ユーザー1")),
            ("user2@example.com", EmailTemplateManager.welcome("ユーザー2")),
            ("user3@example.com", EmailTemplateManager.welcome("ユーザー3")),
        ]

        results = await service.send_bulk_async(recipients, max_concurrent=2)

        assert len(results) == 3
        assert all(success for success in results.values())


class TestEmailServiceConvenienceMethods:
    """EmailService便利メソッドのテスト"""

    @patch("smtplib.SMTP")
    def test_send_welcome(self, mock_smtp):
        """ウェルカムメール送信"""
        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user",
            smtp_password="password",
            from_email="noreply@example.com",
        )
        service = EmailService(config=config)

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

        result = service.send_welcome("test@example.com", "テストユーザー")
        assert result is True

    @patch("smtplib.SMTP")
    def test_send_password_reset(self, mock_smtp):
        """パスワードリセットメール送信"""
        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user",
            smtp_password="password",
            from_email="noreply@example.com",
        )
        service = EmailService(config=config)

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

        result = service.send_password_reset(
            "test@example.com", "テストユーザー", "https://example.com/reset"
        )
        assert result is True

    @patch("smtplib.SMTP")
    def test_send_analysis_complete(self, mock_smtp):
        """分析完了通知メール送信"""
        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user",
            smtp_password="password",
            from_email="noreply@example.com",
        )
        service = EmailService(config=config)

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

        result = service.send_analysis_complete(
            "test@example.com",
            "テストユーザー",
            "Twitter",
            {"投稿数": "100"},
        )
        assert result is True

    @patch("smtplib.SMTP")
    def test_send_engagement_alert(self, mock_smtp):
        """エンゲージメントアラートメール送信"""
        config = EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user",
            smtp_password="password",
            from_email="noreply@example.com",
        )
        service = EmailService(config=config)

        mock_server = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

        result = service.send_engagement_alert(
            "test@example.com",
            "テストユーザー",
            "Twitter",
            "人気の投稿",
            "1,500",
            "+250%",
        )
        assert result is True


class TestGetEmailService:
    """get_email_service関数のテスト"""

    def test_returns_singleton(self):
        """シングルトンインスタンスを返す"""
        # グローバル変数をリセット
        import src.api.email.service as email_module
        email_module._email_service = None

        service1 = get_email_service()
        service2 = get_email_service()

        assert service1 is service2

        # クリーンアップ
        email_module._email_service = None
