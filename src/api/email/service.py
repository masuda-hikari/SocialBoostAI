"""
メール送信サービス

SMTPを使用したメール送信機能を提供する。
SendGridやAWS SESなどの外部サービスにも拡張可能。
"""

import asyncio
import logging
import os
import smtplib
import ssl
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import lru_cache
from typing import Any

from .templates import EmailTemplate, EmailTemplateManager, EmailTemplateType

logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """メール設定"""

    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    from_email: str
    from_name: str = "SocialBoostAI"
    use_tls: bool = True
    use_ssl: bool = False


class EmailService:
    """メール送信サービス"""

    def __init__(self, config: EmailConfig | None = None):
        """
        初期化

        Args:
            config: メール設定（Noneの場合は環境変数から取得）
        """
        if config:
            self.config = config
        else:
            self.config = self._load_config_from_env()

        self._enabled = self._check_enabled()

    def _load_config_from_env(self) -> EmailConfig | None:
        """環境変数からメール設定を読み込む"""
        smtp_host = os.getenv("SMTP_HOST", "")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        from_email = os.getenv("FROM_EMAIL", "noreply@socialboost.ai")
        from_name = os.getenv("FROM_NAME", "SocialBoostAI")
        use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        use_ssl = os.getenv("SMTP_USE_SSL", "false").lower() == "true"

        if not smtp_host:
            return None

        return EmailConfig(
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_user=smtp_user,
            smtp_password=smtp_password,
            from_email=from_email,
            from_name=from_name,
            use_tls=use_tls,
            use_ssl=use_ssl,
        )

    def _check_enabled(self) -> bool:
        """メール送信が有効かどうかを確認"""
        if self.config is None:
            logger.warning("メール設定が見つかりません。メール送信は無効です。")
            return False
        return True

    @property
    def is_enabled(self) -> bool:
        """メール送信が有効かどうか"""
        return self._enabled

    def _create_message(
        self,
        to_email: str,
        template: EmailTemplate,
    ) -> MIMEMultipart:
        """MIMEメッセージを作成"""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = template.subject
        msg["From"] = f"{self.config.from_name} <{self.config.from_email}>"
        msg["To"] = to_email

        # テキスト版
        text_part = MIMEText(template.text_body, "plain", "utf-8")
        msg.attach(text_part)

        # HTML版
        html_part = MIMEText(template.html_body, "html", "utf-8")
        msg.attach(html_part)

        return msg

    def _send_smtp(self, to_email: str, message: MIMEMultipart) -> bool:
        """SMTPでメールを送信"""
        try:
            if self.config.use_ssl:
                # SSL接続（通常ポート465）
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(
                    self.config.smtp_host,
                    self.config.smtp_port,
                    context=context,
                ) as server:
                    server.login(self.config.smtp_user, self.config.smtp_password)
                    server.sendmail(
                        self.config.from_email,
                        to_email,
                        message.as_string(),
                    )
            else:
                # STARTTLS接続（通常ポート587）
                with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                    if self.config.use_tls:
                        context = ssl.create_default_context()
                        server.starttls(context=context)
                    server.login(self.config.smtp_user, self.config.smtp_password)
                    server.sendmail(
                        self.config.from_email,
                        to_email,
                        message.as_string(),
                    )

            logger.info(f"メール送信成功: {to_email}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP認証エラー: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTPエラー: {e}")
            return False
        except Exception as e:
            logger.error(f"メール送信エラー: {e}")
            return False

    def send(self, to_email: str, template: EmailTemplate) -> bool:
        """
        メールを送信（同期）

        Args:
            to_email: 送信先メールアドレス
            template: メールテンプレート

        Returns:
            送信成功ならTrue
        """
        if not self._enabled:
            logger.warning(f"メール送信スキップ（無効）: {to_email}")
            return False

        message = self._create_message(to_email, template)
        return self._send_smtp(to_email, message)

    async def send_async(self, to_email: str, template: EmailTemplate) -> bool:
        """
        メールを送信（非同期）

        Args:
            to_email: 送信先メールアドレス
            template: メールテンプレート

        Returns:
            送信成功ならTrue
        """
        if not self._enabled:
            logger.warning(f"メール送信スキップ（無効）: {to_email}")
            return False

        message = self._create_message(to_email, template)
        # SMTPは同期処理なのでスレッドプールで実行
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._send_smtp, to_email, message)

    async def send_bulk_async(
        self,
        recipients: list[tuple[str, EmailTemplate]],
        max_concurrent: int = 10,
    ) -> dict[str, bool]:
        """
        複数のメールを一括送信（非同期）

        Args:
            recipients: (メールアドレス, テンプレート)のリスト
            max_concurrent: 同時送信数の上限

        Returns:
            {メールアドレス: 成功/失敗}の辞書
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def send_with_limit(email: str, template: EmailTemplate) -> tuple[str, bool]:
            async with semaphore:
                result = await self.send_async(email, template)
                return email, result

        tasks = [send_with_limit(email, template) for email, template in recipients]
        results = await asyncio.gather(*tasks)

        return dict(results)

    # 便利メソッド
    def send_welcome(self, to_email: str, user_name: str) -> bool:
        """ウェルカムメールを送信"""
        template = EmailTemplateManager.welcome(user_name)
        return self.send(to_email, template)

    async def send_welcome_async(self, to_email: str, user_name: str) -> bool:
        """ウェルカムメールを送信（非同期）"""
        template = EmailTemplateManager.welcome(user_name)
        return await self.send_async(to_email, template)

    def send_password_reset(
        self,
        to_email: str,
        user_name: str,
        reset_url: str,
        expires_in: str = "1時間",
    ) -> bool:
        """パスワードリセットメールを送信"""
        template = EmailTemplateManager.password_reset(user_name, reset_url, expires_in)
        return self.send(to_email, template)

    async def send_password_reset_async(
        self,
        to_email: str,
        user_name: str,
        reset_url: str,
        expires_in: str = "1時間",
    ) -> bool:
        """パスワードリセットメールを送信（非同期）"""
        template = EmailTemplateManager.password_reset(user_name, reset_url, expires_in)
        return await self.send_async(to_email, template)

    def send_analysis_complete(
        self,
        to_email: str,
        user_name: str,
        platform: str,
        metrics: dict[str, Any],
    ) -> bool:
        """分析完了通知メールを送信"""
        template = EmailTemplateManager.analysis_complete(user_name, platform, metrics)
        return self.send(to_email, template)

    async def send_analysis_complete_async(
        self,
        to_email: str,
        user_name: str,
        platform: str,
        metrics: dict[str, Any],
    ) -> bool:
        """分析完了通知メールを送信（非同期）"""
        template = EmailTemplateManager.analysis_complete(user_name, platform, metrics)
        return await self.send_async(to_email, template)

    def send_weekly_report(
        self,
        to_email: str,
        user_name: str,
        period: str,
        summary: dict[str, Any],
        highlights: list[str],
        recommendations: list[str],
    ) -> bool:
        """週次レポートメールを送信"""
        template = EmailTemplateManager.weekly_report(
            user_name, period, summary, highlights, recommendations
        )
        return self.send(to_email, template)

    async def send_weekly_report_async(
        self,
        to_email: str,
        user_name: str,
        period: str,
        summary: dict[str, Any],
        highlights: list[str],
        recommendations: list[str],
    ) -> bool:
        """週次レポートメールを送信（非同期）"""
        template = EmailTemplateManager.weekly_report(
            user_name, period, summary, highlights, recommendations
        )
        return await self.send_async(to_email, template)

    def send_monthly_report(
        self,
        to_email: str,
        user_name: str,
        period: str,
        summary: dict[str, Any],
        growth: dict[str, str],
        top_content: list[dict[str, str]],
    ) -> bool:
        """月次レポートメールを送信"""
        template = EmailTemplateManager.monthly_report(
            user_name, period, summary, growth, top_content
        )
        return self.send(to_email, template)

    async def send_monthly_report_async(
        self,
        to_email: str,
        user_name: str,
        period: str,
        summary: dict[str, Any],
        growth: dict[str, str],
        top_content: list[dict[str, str]],
    ) -> bool:
        """月次レポートメールを送信（非同期）"""
        template = EmailTemplateManager.monthly_report(
            user_name, period, summary, growth, top_content
        )
        return await self.send_async(to_email, template)

    def send_subscription_created(
        self,
        to_email: str,
        user_name: str,
        plan_name: str,
        price: str,
        next_billing_date: str,
    ) -> bool:
        """サブスクリプション開始メールを送信"""
        template = EmailTemplateManager.subscription_created(
            user_name, plan_name, price, next_billing_date
        )
        return self.send(to_email, template)

    async def send_subscription_created_async(
        self,
        to_email: str,
        user_name: str,
        plan_name: str,
        price: str,
        next_billing_date: str,
    ) -> bool:
        """サブスクリプション開始メールを送信（非同期）"""
        template = EmailTemplateManager.subscription_created(
            user_name, plan_name, price, next_billing_date
        )
        return await self.send_async(to_email, template)

    def send_payment_failed(
        self,
        to_email: str,
        user_name: str,
        plan_name: str,
        amount: str,
        retry_date: str,
    ) -> bool:
        """支払い失敗通知メールを送信"""
        template = EmailTemplateManager.payment_failed(
            user_name, plan_name, amount, retry_date
        )
        return self.send(to_email, template)

    async def send_payment_failed_async(
        self,
        to_email: str,
        user_name: str,
        plan_name: str,
        amount: str,
        retry_date: str,
    ) -> bool:
        """支払い失敗通知メールを送信（非同期）"""
        template = EmailTemplateManager.payment_failed(
            user_name, plan_name, amount, retry_date
        )
        return await self.send_async(to_email, template)

    def send_engagement_alert(
        self,
        to_email: str,
        user_name: str,
        platform: str,
        content_title: str,
        current_engagement: str,
        change: str,
    ) -> bool:
        """エンゲージメントアラートメールを送信"""
        template = EmailTemplateManager.engagement_alert(
            user_name, platform, content_title, current_engagement, change
        )
        return self.send(to_email, template)

    async def send_engagement_alert_async(
        self,
        to_email: str,
        user_name: str,
        platform: str,
        content_title: str,
        current_engagement: str,
        change: str,
    ) -> bool:
        """エンゲージメントアラートメールを送信（非同期）"""
        template = EmailTemplateManager.engagement_alert(
            user_name, platform, content_title, current_engagement, change
        )
        return await self.send_async(to_email, template)


# グローバルインスタンス
_email_service: EmailService | None = None


def get_email_service() -> EmailService:
    """EmailServiceのシングルトンインスタンスを取得"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
