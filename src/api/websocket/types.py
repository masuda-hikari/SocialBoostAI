"""
WebSocket通知タイプ定義
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class NotificationType(str, Enum):
    """通知タイプ"""

    # 分析関連
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_PROGRESS = "analysis_progress"
    ANALYSIS_COMPLETE = "analysis_complete"
    ANALYSIS_FAILED = "analysis_failed"

    # レポート関連
    REPORT_GENERATING = "report_generating"
    REPORT_READY = "report_ready"
    REPORT_FAILED = "report_failed"

    # サブスクリプション関連
    SUBSCRIPTION_UPDATED = "subscription_updated"
    SUBSCRIPTION_EXPIRING = "subscription_expiring"
    PAYMENT_FAILED = "payment_failed"

    # システム通知
    SYSTEM_NOTIFICATION = "system_notification"
    MAINTENANCE_SCHEDULED = "maintenance_scheduled"

    # リアルタイムダッシュボード
    DASHBOARD_UPDATE = "dashboard_update"
    METRICS_UPDATE = "metrics_update"


@dataclass
class AnalysisCompletePayload:
    """分析完了ペイロード"""

    analysis_id: str
    platform: str
    period_start: str
    period_end: str
    total_posts: int
    engagement_rate: float
    best_hour: Optional[int] = None
    top_hashtags: list[str] = field(default_factory=list)


@dataclass
class ReportReadyPayload:
    """レポート完了ペイロード"""

    report_id: str
    report_type: str  # weekly, monthly, custom
    platform: str
    period_start: str
    period_end: str
    html_url: Optional[str] = None


@dataclass
class SystemNotificationPayload:
    """システム通知ペイロード"""

    title: str
    message: str
    severity: str = "info"  # info, warning, error, success
    action_url: Optional[str] = None


@dataclass
class SubscriptionUpdatePayload:
    """サブスクリプション更新ペイロード"""

    plan: str
    status: str
    previous_plan: Optional[str] = None
    current_period_end: Optional[str] = None


@dataclass
class DashboardUpdatePayload:
    """ダッシュボード更新ペイロード"""

    platform: str
    metrics: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class MetricsUpdatePayload:
    """メトリクス更新ペイロード"""

    total_followers: Optional[int] = None
    engagement_rate: Optional[float] = None
    posts_today: Optional[int] = None
    trending_hashtags: list[str] = field(default_factory=list)


@dataclass
class Notification:
    """通知メッセージ"""

    type: NotificationType
    payload: dict[str, Any]
    timestamp: str = ""
    notification_id: str = ""

    def __post_init__(self):
        import secrets
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if not self.notification_id:
            self.notification_id = f"notif_{secrets.token_hex(8)}"

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換"""
        return {
            "type": self.type.value,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "notification_id": self.notification_id,
        }
