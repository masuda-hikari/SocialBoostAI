"""
メール通知APIルーター

メールテスト送信やメール設定管理のエンドポイントを提供する。
"""

import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from ..dependencies import get_current_user, require_plan
from ..email import EmailService, EmailTemplateManager, get_email_service

logger = logging.getLogger(__name__)

router = APIRouter()


# スキーマ定義
class EmailStatusResponse(BaseModel):
    """メール設定状態"""

    enabled: bool = Field(..., description="メール送信が有効かどうか")
    message: str = Field(..., description="状態メッセージ")


class SendTestEmailRequest(BaseModel):
    """テストメール送信リクエスト"""

    template_type: str = Field(..., description="テンプレート種別")


class SendTestEmailResponse(BaseModel):
    """テストメール送信レスポンス"""

    success: bool = Field(..., description="送信成功かどうか")
    message: str = Field(..., description="結果メッセージ")


class WeeklyReportRequest(BaseModel):
    """週次レポートメール送信リクエスト"""

    # オプション: 特定の週を指定する場合
    week_start: str | None = Field(None, description="週の開始日（YYYY-MM-DD）")


class EmailPreferencesRequest(BaseModel):
    """メール通知設定"""

    weekly_report: bool = Field(True, description="週次レポートメール")
    monthly_report: bool = Field(True, description="月次レポートメール")
    analysis_complete: bool = Field(True, description="分析完了通知")
    engagement_alerts: bool = Field(True, description="エンゲージメントアラート")
    billing_notifications: bool = Field(True, description="課金関連通知")


class EmailPreferencesResponse(BaseModel):
    """メール通知設定レスポンス"""

    weekly_report: bool
    monthly_report: bool
    analysis_complete: bool
    engagement_alerts: bool
    billing_notifications: bool
    updated_at: datetime


@router.get("/status", response_model=EmailStatusResponse)
async def get_email_status(
    current_user: dict = Depends(get_current_user),
    email_service: EmailService = Depends(get_email_service),
):
    """メール送信状態を取得"""
    if email_service.is_enabled:
        return EmailStatusResponse(
            enabled=True,
            message="メール送信が有効です",
        )
    else:
        return EmailStatusResponse(
            enabled=False,
            message="メール設定が構成されていません。環境変数（SMTP_HOST等）を設定してください。",
        )


@router.post("/test", response_model=SendTestEmailResponse)
async def send_test_email(
    request: SendTestEmailRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    email_service: EmailService = Depends(get_email_service),
):
    """
    テストメールを送信

    利用可能なテンプレート:
    - welcome: ウェルカムメール
    - analysis_complete: 分析完了通知
    - weekly_report: 週次レポート
    - engagement_alert: エンゲージメントアラート
    """
    if not email_service.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="メール送信が無効です。SMTP設定を確認してください。",
        )

    user_email = current_user.get("email")
    user_name = current_user.get("username", "ユーザー")

    # テンプレート種別に応じてテストメールを作成
    template_type = request.template_type.lower()

    if template_type == "welcome":
        template = EmailTemplateManager.welcome(user_name)
    elif template_type == "analysis_complete":
        template = EmailTemplateManager.analysis_complete(
            user_name,
            "Twitter",
            {
                "総投稿数": "150件",
                "平均エンゲージメント率": "4.5%",
                "フォロワー増加": "+120",
            },
        )
    elif template_type == "weekly_report":
        template = EmailTemplateManager.weekly_report(
            user_name,
            "2026/01/06 - 2026/01/12",
            {
                "投稿数": "25件",
                "総エンゲージメント": "12,500",
                "フォロワー増加": "+85",
            },
            [
                "火曜日の投稿が最もエンゲージメントが高かった",
                "#AI関連のハッシュタグが好調",
                "動画コンテンツの反応が良好",
            ],
            [
                "平日19時〜21時の投稿を増やすことを推奨",
                "ユーザー参加型コンテンツの投稿を検討",
                "ハッシュタグ数を3〜5個に絞ると効果的",
            ],
        )
    elif template_type == "engagement_alert":
        template = EmailTemplateManager.engagement_alert(
            user_name,
            "Twitter",
            "AIツールの使い方完全ガイド",
            "1,250 エンゲージメント",
            "+320%（1時間前比）",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不明なテンプレート種別: {template_type}。利用可能: welcome, analysis_complete, weekly_report, engagement_alert",
        )

    # バックグラウンドで送信
    async def send_email_task():
        try:
            success = await email_service.send_async(user_email, template)
            if success:
                logger.info(f"テストメール送信成功: {user_email}, template={template_type}")
            else:
                logger.error(f"テストメール送信失敗: {user_email}, template={template_type}")
        except Exception as e:
            logger.error(f"テストメール送信エラー: {e}")

    background_tasks.add_task(send_email_task)

    return SendTestEmailResponse(
        success=True,
        message=f"テストメール（{template_type}）を {user_email} に送信しています...",
    )


@router.post("/send-weekly-report", response_model=SendTestEmailResponse)
async def send_weekly_report(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_plan("pro")),
    email_service: EmailService = Depends(get_email_service),
):
    """
    週次レポートメールを送信（Pro以上）

    現在の週のレポートをメールで送信します。
    """
    if not email_service.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="メール送信が無効です。SMTP設定を確認してください。",
        )

    user_email = current_user.get("email")
    user_name = current_user.get("username", "ユーザー")

    # 実際の週次サマリーデータを取得（ここでは仮データ）
    # TODO: summary.pyから実際のデータを取得する
    period = datetime.now().strftime("%Y/%m/%d") + " 週"
    summary = {
        "分析プラットフォーム数": "3",
        "総投稿数": "45件",
        "総エンゲージメント": "8,750",
    }
    highlights = [
        "エンゲージメント率が先週比+15%",
        "木曜日の投稿が最も反応が良かった",
    ]
    recommendations = [
        "動画コンテンツの割合を増やすことを推奨",
        "朝8時台の投稿を試してみてください",
    ]

    async def send_report_task():
        try:
            success = await email_service.send_weekly_report_async(
                user_email, user_name, period, summary, highlights, recommendations
            )
            if success:
                logger.info(f"週次レポート送信成功: {user_email}")
            else:
                logger.error(f"週次レポート送信失敗: {user_email}")
        except Exception as e:
            logger.error(f"週次レポート送信エラー: {e}")

    background_tasks.add_task(send_report_task)

    return SendTestEmailResponse(
        success=True,
        message=f"週次レポートを {user_email} に送信しています...",
    )


@router.get("/preferences", response_model=EmailPreferencesResponse)
async def get_email_preferences(
    current_user: dict = Depends(get_current_user),
):
    """
    メール通知設定を取得

    TODO: データベースからユーザーの設定を取得
    """
    # 現時点ではデフォルト値を返す
    # 将来的にはDBに保存されたユーザー設定を返す
    return EmailPreferencesResponse(
        weekly_report=True,
        monthly_report=True,
        analysis_complete=True,
        engagement_alerts=True,
        billing_notifications=True,
        updated_at=datetime.now(),
    )


@router.put("/preferences", response_model=EmailPreferencesResponse)
async def update_email_preferences(
    preferences: EmailPreferencesRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    メール通知設定を更新

    TODO: データベースにユーザー設定を保存
    """
    # 現時点ではリクエストされた値をそのまま返す
    # 将来的にはDBに保存する
    logger.info(f"メール設定更新: user_id={current_user.get('id')}, preferences={preferences}")

    return EmailPreferencesResponse(
        weekly_report=preferences.weekly_report,
        monthly_report=preferences.monthly_report,
        analysis_complete=preferences.analysis_complete,
        engagement_alerts=preferences.engagement_alerts,
        billing_notifications=preferences.billing_notifications,
        updated_at=datetime.now(),
    )
