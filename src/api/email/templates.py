"""
メールテンプレート

各種通知メールのテンプレートを管理する。
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class EmailTemplateType(Enum):
    """メールテンプレート種別"""

    # 認証関連
    WELCOME = "welcome"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"

    # 分析関連
    ANALYSIS_COMPLETE = "analysis_complete"
    WEEKLY_REPORT = "weekly_report"
    MONTHLY_REPORT = "monthly_report"

    # 課金関連
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_UPDATED = "subscription_updated"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    PAYMENT_SUCCEEDED = "payment_succeeded"
    PAYMENT_FAILED = "payment_failed"

    # エンゲージメント
    ENGAGEMENT_ALERT = "engagement_alert"
    TRENDING_CONTENT = "trending_content"


@dataclass
class EmailTemplate:
    """メールテンプレート"""

    template_type: EmailTemplateType
    subject: str
    html_body: str
    text_body: str


class EmailTemplateManager:
    """メールテンプレート管理"""

    # サービス名
    SERVICE_NAME = "SocialBoostAI"
    SUPPORT_EMAIL = "support@socialboost.ai"
    WEBSITE_URL = "https://socialboost.ai"

    # 共通ヘッダー
    _HTML_HEADER = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .content {{ background: white; padding: 30px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .button {{ display: inline-block; background: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; margin: 20px 0; }}
        .button:hover {{ background: #5558e3; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        .stats {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .stats-item {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }}
        .stats-item:last-child {{ border-bottom: none; }}
        .highlight {{ color: #6366f1; font-weight: bold; }}
        .alert {{ background: #fef3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 6px; margin: 15px 0; }}
        .success {{ background: #d4edda; border: 1px solid #28a745; }}
        .danger {{ background: #f8d7da; border: 1px solid #dc3545; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{header_title}</h1>
        </div>
        <div class="content">
"""

    _HTML_FOOTER = """
        </div>
        <div class="footer">
            <p>&copy; {year} {service_name}. All rights reserved.</p>
            <p>ご不明な点がございましたら、<a href="mailto:{support_email}">{support_email}</a>までお問い合わせください。</p>
            <p><a href="{website_url}">{website_url}</a></p>
        </div>
    </div>
</body>
</html>
"""

    @classmethod
    def _wrap_html(cls, title: str, header_title: str, content: str) -> str:
        """HTMLテンプレートをラップする"""
        return (
            cls._HTML_HEADER.format(title=title, header_title=header_title)
            + content
            + cls._HTML_FOOTER.format(
                year=datetime.now().year,
                service_name=cls.SERVICE_NAME,
                support_email=cls.SUPPORT_EMAIL,
                website_url=cls.WEBSITE_URL,
            )
        )

    @classmethod
    def welcome(cls, user_name: str) -> EmailTemplate:
        """ウェルカムメール"""
        subject = f"ようこそ {cls.SERVICE_NAME} へ！"
        html_content = f"""
            <h2>こんにちは、{user_name}さん！</h2>
            <p>{cls.SERVICE_NAME}へのご登録ありがとうございます。</p>
            <p>AIがあなたのソーシャルメディアのエンゲージメント向上をサポートします。</p>

            <h3>はじめに</h3>
            <ol>
                <li><strong>SNSアカウントを連携</strong> - Twitter、Instagram、TikTok、YouTube、LinkedInに対応</li>
                <li><strong>分析を開始</strong> - 投稿パフォーマンスを詳細に分析</li>
                <li><strong>AIの提案を活用</strong> - 最適な投稿時間、コンテンツ提案を受け取る</li>
            </ol>

            <a href="{cls.WEBSITE_URL}/dashboard" class="button">ダッシュボードへ</a>

            <p>ご質問がございましたら、お気軽にサポートまでお問い合わせください。</p>
        """
        text_body = f"""
こんにちは、{user_name}さん！

{cls.SERVICE_NAME}へのご登録ありがとうございます。
AIがあなたのソーシャルメディアのエンゲージメント向上をサポートします。

【はじめに】
1. SNSアカウントを連携 - Twitter、Instagram、TikTok、YouTube、LinkedInに対応
2. 分析を開始 - 投稿パフォーマンスを詳細に分析
3. AIの提案を活用 - 最適な投稿時間、コンテンツ提案を受け取る

ダッシュボード: {cls.WEBSITE_URL}/dashboard

ご質問がございましたら、{cls.SUPPORT_EMAIL}までお問い合わせください。
        """
        return EmailTemplate(
            template_type=EmailTemplateType.WELCOME,
            subject=subject,
            html_body=cls._wrap_html(subject, "ようこそ！", html_content),
            text_body=text_body.strip(),
        )

    @classmethod
    def password_reset(cls, user_name: str, reset_url: str, expires_in: str = "1時間") -> EmailTemplate:
        """パスワードリセットメール"""
        subject = f"[{cls.SERVICE_NAME}] パスワードリセットのご案内"
        html_content = f"""
            <h2>パスワードリセット</h2>
            <p>{user_name}さん、</p>
            <p>パスワードリセットのリクエストを受け付けました。</p>
            <p>以下のボタンをクリックして、新しいパスワードを設定してください。</p>

            <a href="{reset_url}" class="button">パスワードをリセット</a>

            <p class="alert">このリンクは<strong>{expires_in}</strong>で期限切れになります。</p>

            <p>このリクエストに心当たりがない場合は、このメールを無視してください。<br>
            パスワードは変更されません。</p>
        """
        text_body = f"""
{user_name}さん、

パスワードリセットのリクエストを受け付けました。
以下のURLにアクセスして、新しいパスワードを設定してください。

{reset_url}

このリンクは{expires_in}で期限切れになります。

このリクエストに心当たりがない場合は、このメールを無視してください。
パスワードは変更されません。
        """
        return EmailTemplate(
            template_type=EmailTemplateType.PASSWORD_RESET,
            subject=subject,
            html_body=cls._wrap_html(subject, "パスワードリセット", html_content),
            text_body=text_body.strip(),
        )

    @classmethod
    def analysis_complete(
        cls,
        user_name: str,
        platform: str,
        metrics: dict[str, Any],
    ) -> EmailTemplate:
        """分析完了通知メール"""
        subject = f"[{cls.SERVICE_NAME}] {platform}の分析が完了しました"

        # メトリクス表示
        metrics_html = ""
        for key, value in metrics.items():
            metrics_html += f'<div class="stats-item"><span>{key}</span><span class="highlight">{value}</span></div>'

        html_content = f"""
            <h2>分析完了</h2>
            <p>{user_name}さん、</p>
            <p><strong>{platform}</strong>の分析が完了しました。</p>

            <div class="stats">
                <h3>主要指標</h3>
                {metrics_html}
            </div>

            <a href="{cls.WEBSITE_URL}/dashboard" class="button">詳細を見る</a>

            <p>詳しい分析結果はダッシュボードでご確認いただけます。</p>
        """

        metrics_text = "\n".join([f"  {key}: {value}" for key, value in metrics.items()])
        text_body = f"""
{user_name}さん、

{platform}の分析が完了しました。

【主要指標】
{metrics_text}

詳細を見る: {cls.WEBSITE_URL}/dashboard
        """
        return EmailTemplate(
            template_type=EmailTemplateType.ANALYSIS_COMPLETE,
            subject=subject,
            html_body=cls._wrap_html(subject, "分析完了", html_content),
            text_body=text_body.strip(),
        )

    @classmethod
    def weekly_report(
        cls,
        user_name: str,
        period: str,
        summary: dict[str, Any],
        highlights: list[str],
        recommendations: list[str],
    ) -> EmailTemplate:
        """週次レポートメール"""
        subject = f"[{cls.SERVICE_NAME}] 週次レポート - {period}"

        # サマリー表示
        summary_html = ""
        for key, value in summary.items():
            summary_html += f'<div class="stats-item"><span>{key}</span><span class="highlight">{value}</span></div>'

        # ハイライト
        highlights_html = "".join([f"<li>{h}</li>" for h in highlights])

        # 推奨事項
        recommendations_html = "".join([f"<li>{r}</li>" for r in recommendations])

        html_content = f"""
            <h2>週次レポート</h2>
            <p>{user_name}さん、</p>
            <p><strong>{period}</strong>のレポートをお届けします。</p>

            <div class="stats">
                <h3>今週のサマリー</h3>
                {summary_html}
            </div>

            <h3>ハイライト</h3>
            <ul>{highlights_html}</ul>

            <h3>AIからの提案</h3>
            <ul>{recommendations_html}</ul>

            <a href="{cls.WEBSITE_URL}/reports" class="button">詳細レポートを見る</a>
        """

        summary_text = "\n".join([f"  {key}: {value}" for key, value in summary.items()])
        highlights_text = "\n".join([f"  - {h}" for h in highlights])
        recommendations_text = "\n".join([f"  - {r}" for r in recommendations])

        text_body = f"""
{user_name}さん、

{period}の週次レポートをお届けします。

【今週のサマリー】
{summary_text}

【ハイライト】
{highlights_text}

【AIからの提案】
{recommendations_text}

詳細レポート: {cls.WEBSITE_URL}/reports
        """
        return EmailTemplate(
            template_type=EmailTemplateType.WEEKLY_REPORT,
            subject=subject,
            html_body=cls._wrap_html(subject, "週次レポート", html_content),
            text_body=text_body.strip(),
        )

    @classmethod
    def monthly_report(
        cls,
        user_name: str,
        period: str,
        summary: dict[str, Any],
        growth: dict[str, str],
        top_content: list[dict[str, str]],
    ) -> EmailTemplate:
        """月次レポートメール"""
        subject = f"[{cls.SERVICE_NAME}] 月次レポート - {period}"

        # サマリー表示
        summary_html = ""
        for key, value in summary.items():
            summary_html += f'<div class="stats-item"><span>{key}</span><span class="highlight">{value}</span></div>'

        # 成長指標
        growth_html = ""
        for key, value in growth.items():
            color = "green" if value.startswith("+") else "red"
            growth_html += f'<div class="stats-item"><span>{key}</span><span style="color:{color};font-weight:bold">{value}</span></div>'

        # トップコンテンツ
        top_content_html = ""
        for i, content in enumerate(top_content[:5], 1):
            top_content_html += f"""
                <div style="padding: 10px; border-bottom: 1px solid #eee;">
                    <strong>#{i}</strong> {content.get('title', '')}
                    <span class="highlight" style="float:right">{content.get('engagement', '')}</span>
                </div>
            """

        html_content = f"""
            <h2>月次レポート</h2>
            <p>{user_name}さん、</p>
            <p><strong>{period}</strong>の月次レポートをお届けします。</p>

            <div class="stats">
                <h3>今月のサマリー</h3>
                {summary_html}
            </div>

            <div class="stats">
                <h3>前月比</h3>
                {growth_html}
            </div>

            <h3>トップコンテンツ</h3>
            <div style="background: #f8f9fa; border-radius: 8px; overflow: hidden;">
                {top_content_html}
            </div>

            <a href="{cls.WEBSITE_URL}/reports" class="button">詳細レポートを見る</a>
        """

        summary_text = "\n".join([f"  {key}: {value}" for key, value in summary.items()])
        growth_text = "\n".join([f"  {key}: {value}" for key, value in growth.items()])
        top_content_text = "\n".join(
            [f"  {i}. {c.get('title', '')}: {c.get('engagement', '')}" for i, c in enumerate(top_content[:5], 1)]
        )

        text_body = f"""
{user_name}さん、

{period}の月次レポートをお届けします。

【今月のサマリー】
{summary_text}

【前月比】
{growth_text}

【トップコンテンツ】
{top_content_text}

詳細レポート: {cls.WEBSITE_URL}/reports
        """
        return EmailTemplate(
            template_type=EmailTemplateType.MONTHLY_REPORT,
            subject=subject,
            html_body=cls._wrap_html(subject, "月次レポート", html_content),
            text_body=text_body.strip(),
        )

    @classmethod
    def subscription_created(
        cls,
        user_name: str,
        plan_name: str,
        price: str,
        next_billing_date: str,
    ) -> EmailTemplate:
        """サブスクリプション開始メール"""
        subject = f"[{cls.SERVICE_NAME}] {plan_name}プランへのご登録ありがとうございます"
        html_content = f"""
            <h2>サブスクリプション開始</h2>
            <p>{user_name}さん、</p>
            <p><strong>{plan_name}</strong>プランへのご登録ありがとうございます！</p>

            <div class="stats">
                <div class="stats-item"><span>プラン</span><span class="highlight">{plan_name}</span></div>
                <div class="stats-item"><span>料金</span><span class="highlight">{price}/月</span></div>
                <div class="stats-item"><span>次回請求日</span><span>{next_billing_date}</span></div>
            </div>

            <div class="alert success">
                <strong>すべての{plan_name}機能がご利用いただけます！</strong>
            </div>

            <a href="{cls.WEBSITE_URL}/dashboard" class="button">今すぐ始める</a>
        """
        text_body = f"""
{user_name}さん、

{plan_name}プランへのご登録ありがとうございます！

【サブスクリプション情報】
  プラン: {plan_name}
  料金: {price}/月
  次回請求日: {next_billing_date}

すべての{plan_name}機能がご利用いただけます！

ダッシュボード: {cls.WEBSITE_URL}/dashboard
        """
        return EmailTemplate(
            template_type=EmailTemplateType.SUBSCRIPTION_CREATED,
            subject=subject,
            html_body=cls._wrap_html(subject, "ご登録完了", html_content),
            text_body=text_body.strip(),
        )

    @classmethod
    def payment_failed(
        cls,
        user_name: str,
        plan_name: str,
        amount: str,
        retry_date: str,
    ) -> EmailTemplate:
        """支払い失敗通知メール"""
        subject = f"[{cls.SERVICE_NAME}] お支払いに失敗しました - ご確認をお願いします"
        html_content = f"""
            <h2>お支払いに失敗しました</h2>
            <p>{user_name}さん、</p>
            <p><strong>{plan_name}</strong>プランのお支払い処理に失敗しました。</p>

            <div class="alert danger">
                <strong>請求金額:</strong> {amount}<br>
                <strong>次回再試行:</strong> {retry_date}
            </div>

            <p>お支払い方法をご確認の上、更新してください。</p>

            <a href="{cls.WEBSITE_URL}/billing" class="button">お支払い情報を更新</a>

            <p>ご不明な点がございましたら、サポートまでお問い合わせください。</p>
        """
        text_body = f"""
{user_name}さん、

{plan_name}プランのお支払い処理に失敗しました。

請求金額: {amount}
次回再試行: {retry_date}

お支払い方法をご確認の上、以下のURLから更新してください。
{cls.WEBSITE_URL}/billing

ご不明な点がございましたら、{cls.SUPPORT_EMAIL}までお問い合わせください。
        """
        return EmailTemplate(
            template_type=EmailTemplateType.PAYMENT_FAILED,
            subject=subject,
            html_body=cls._wrap_html(subject, "お支払いエラー", html_content),
            text_body=text_body.strip(),
        )

    @classmethod
    def engagement_alert(
        cls,
        user_name: str,
        platform: str,
        content_title: str,
        current_engagement: str,
        change: str,
    ) -> EmailTemplate:
        """エンゲージメントアラートメール"""
        subject = f"[{cls.SERVICE_NAME}] {platform}でエンゲージメントが急上昇中！"
        html_content = f"""
            <h2>エンゲージメントアラート</h2>
            <p>{user_name}さん、</p>
            <p>あなたのコンテンツが注目を集めています！</p>

            <div class="alert success">
                <strong>{platform}</strong>: {content_title}<br>
                <span class="highlight" style="font-size: 1.5em">{change}</span>
            </div>

            <div class="stats">
                <div class="stats-item"><span>現在のエンゲージメント</span><span class="highlight">{current_engagement}</span></div>
            </div>

            <p>この勢いを活かして、フォロワーと積極的に交流しましょう！</p>

            <a href="{cls.WEBSITE_URL}/dashboard" class="button">ダッシュボードで確認</a>
        """
        text_body = f"""
{user_name}さん、

あなたのコンテンツが注目を集めています！

【{platform}】
{content_title}
変化: {change}
現在のエンゲージメント: {current_engagement}

この勢いを活かして、フォロワーと積極的に交流しましょう！

ダッシュボード: {cls.WEBSITE_URL}/dashboard
        """
        return EmailTemplate(
            template_type=EmailTemplateType.ENGAGEMENT_ALERT,
            subject=subject,
            html_body=cls._wrap_html(subject, "急上昇中！", html_content),
            text_body=text_body.strip(),
        )
