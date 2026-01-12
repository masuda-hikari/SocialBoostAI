"""
使用量追跡サービス

プラン別のAPI使用量を追跡・管理する
"""

import json
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from ..db.models import ApiCallLog, DailyUsage, MonthlyUsageSummary, User
from ..schemas import (
    ApiCallLogResponse,
    ApiCallLogsResponse,
    DailyUsageResponse,
    MonthlyUsageSummaryResponse,
    PlanLimits,
    PlanTier,
    UpgradeRecommendation,
    UsageDashboardResponse,
    UsageHistoryResponse,
    UsageTrendResponse,
    UsageWithLimits,
)

logger = logging.getLogger(__name__)


# プラン別制限設定
PLAN_LIMITS: dict[str, PlanLimits] = {
    "free": PlanLimits(
        api_calls_per_day=1000,
        api_calls_per_minute=30,
        analyses_per_day=5,
        reports_per_month=1,
        scheduled_posts_per_day=0,  # Free プランでは利用不可
        ai_generations_per_day=3,
        platforms=1,
        history_days=7,
    ),
    "pro": PlanLimits(
        api_calls_per_day=5000,
        api_calls_per_minute=60,
        analyses_per_day=20,
        reports_per_month=4,
        scheduled_posts_per_day=10,
        ai_generations_per_day=20,
        platforms=1,
        history_days=90,
    ),
    "business": PlanLimits(
        api_calls_per_day=20000,
        api_calls_per_minute=120,
        analyses_per_day=100,
        reports_per_month=-1,  # 無制限
        scheduled_posts_per_day=50,
        ai_generations_per_day=100,
        platforms=3,
        history_days=-1,  # 無制限
    ),
    "enterprise": PlanLimits(
        api_calls_per_day=-1,  # 無制限
        api_calls_per_minute=300,
        analyses_per_day=-1,
        reports_per_month=-1,
        scheduled_posts_per_day=-1,
        ai_generations_per_day=-1,
        platforms=-1,
        history_days=-1,
    ),
}


class UsageService:
    """使用量追跡サービス"""

    def __init__(self, db: Session):
        self.db = db

    def get_plan_limits(self, plan: str) -> PlanLimits:
        """プランの制限を取得"""
        return PLAN_LIMITS.get(plan.lower(), PLAN_LIMITS["free"])

    def get_or_create_daily_usage(
        self, user_id: str, target_date: Optional[date] = None
    ) -> DailyUsage:
        """日次使用量レコードを取得または作成"""
        if target_date is None:
            target_date = datetime.now(timezone.utc).date()

        # 日付を datetime に変換（時刻は00:00:00 UTC）
        target_datetime = datetime.combine(
            target_date, datetime.min.time(), tzinfo=timezone.utc
        )

        usage = (
            self.db.query(DailyUsage)
            .filter(
                and_(
                    DailyUsage.user_id == user_id,
                    func.date(DailyUsage.date) == target_date,
                )
            )
            .first()
        )

        if not usage:
            usage = DailyUsage(
                user_id=user_id,
                date=target_datetime,
                api_calls=0,
                analyses_run=0,
                reports_generated=0,
                scheduled_posts=0,
                ai_generations=0,
                platform_usage="{}",
            )
            self.db.add(usage)
            self.db.commit()
            self.db.refresh(usage)

        return usage

    def increment_usage(
        self,
        user_id: str,
        usage_type: str,
        platform: Optional[str] = None,
        count: int = 1,
    ) -> DailyUsage:
        """使用量をインクリメント"""
        usage = self.get_or_create_daily_usage(user_id)

        if usage_type == "api_call":
            usage.api_calls += count
        elif usage_type == "analysis":
            usage.analyses_run += count
        elif usage_type == "report":
            usage.reports_generated += count
        elif usage_type == "scheduled_post":
            usage.scheduled_posts += count
        elif usage_type == "ai_generation":
            usage.ai_generations += count

        # プラットフォーム別使用量を更新
        if platform:
            platform_usage = json.loads(usage.platform_usage or "{}")
            platform_usage[platform] = platform_usage.get(platform, 0) + count
            usage.platform_usage = json.dumps(platform_usage)

        self.db.commit()
        self.db.refresh(usage)

        return usage

    def log_api_call(
        self,
        user_id: str,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: Optional[float] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> ApiCallLog:
        """API呼び出しをログに記録"""
        log = ApiCallLog(
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,
            request_id=request_id,
        )
        self.db.add(log)

        # 日次使用量もインクリメント
        self.increment_usage(user_id, "api_call")

        self.db.commit()
        self.db.refresh(log)

        return log

    def get_today_usage(self, user_id: str) -> DailyUsageResponse:
        """今日の使用量を取得"""
        usage = self.get_or_create_daily_usage(user_id)
        return self._to_daily_usage_response(usage)

    def get_usage_with_limits(self, user_id: str, plan: str) -> UsageWithLimits:
        """使用量と制限の統合情報を取得"""
        today = self.get_today_usage(user_id)
        limits = self.get_plan_limits(plan)

        remaining = self._calculate_remaining(today, limits)
        usage_percent = self._calculate_usage_percent(today, limits)

        return UsageWithLimits(
            today=today,
            limits=limits,
            remaining=remaining,
            usage_percent=usage_percent,
        )

    def _calculate_remaining(
        self, today: DailyUsageResponse, limits: PlanLimits
    ) -> dict[str, int]:
        """残り使用量を計算"""
        return {
            "api_calls": (
                limits.api_calls_per_day - today.api_calls
                if limits.api_calls_per_day >= 0
                else -1
            ),
            "analyses": (
                limits.analyses_per_day - today.analyses_run
                if limits.analyses_per_day >= 0
                else -1
            ),
            "scheduled_posts": (
                limits.scheduled_posts_per_day - today.scheduled_posts
                if limits.scheduled_posts_per_day >= 0
                else -1
            ),
            "ai_generations": (
                limits.ai_generations_per_day - today.ai_generations
                if limits.ai_generations_per_day >= 0
                else -1
            ),
        }

    def _calculate_usage_percent(
        self, today: DailyUsageResponse, limits: PlanLimits
    ) -> dict[str, float]:
        """使用率を計算"""
        return {
            "api_calls": (
                (today.api_calls / limits.api_calls_per_day * 100)
                if limits.api_calls_per_day > 0
                else -1
            ),
            "analyses": (
                (today.analyses_run / limits.analyses_per_day * 100)
                if limits.analyses_per_day > 0
                else -1
            ),
            "scheduled_posts": (
                (today.scheduled_posts / limits.scheduled_posts_per_day * 100)
                if limits.scheduled_posts_per_day > 0
                else -1
            ),
            "ai_generations": (
                (today.ai_generations / limits.ai_generations_per_day * 100)
                if limits.ai_generations_per_day > 0
                else -1
            ),
        }

    def get_usage_history(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        days: int = 30,
    ) -> UsageHistoryResponse:
        """使用量履歴を取得"""
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        if start_date is None:
            start_date = end_date - timedelta(days=days)

        usages = (
            self.db.query(DailyUsage)
            .filter(
                and_(
                    DailyUsage.user_id == user_id,
                    DailyUsage.date >= start_date,
                    DailyUsage.date <= end_date,
                )
            )
            .order_by(DailyUsage.date.asc())
            .all()
        )

        daily_usage = [self._to_daily_usage_response(u) for u in usages]

        # 合計と平均を計算
        total = self._calculate_total(daily_usage)
        average = self._calculate_average(daily_usage, len(daily_usage))

        return UsageHistoryResponse(
            period_start=start_date,
            period_end=end_date,
            daily_usage=daily_usage,
            total=total,
            average=average,
        )

    def _calculate_total(
        self, daily_usage: list[DailyUsageResponse]
    ) -> DailyUsageResponse:
        """合計を計算"""
        if not daily_usage:
            return DailyUsageResponse(
                date=datetime.now(timezone.utc),
                api_calls=0,
                analyses_run=0,
                reports_generated=0,
                scheduled_posts=0,
                ai_generations=0,
                platform_usage={},
            )

        total_platform_usage: dict[str, int] = {}
        for usage in daily_usage:
            for platform, count in usage.platform_usage.items():
                total_platform_usage[platform] = (
                    total_platform_usage.get(platform, 0) + count
                )

        return DailyUsageResponse(
            date=daily_usage[0].date,
            api_calls=sum(u.api_calls for u in daily_usage),
            analyses_run=sum(u.analyses_run for u in daily_usage),
            reports_generated=sum(u.reports_generated for u in daily_usage),
            scheduled_posts=sum(u.scheduled_posts for u in daily_usage),
            ai_generations=sum(u.ai_generations for u in daily_usage),
            platform_usage=total_platform_usage,
        )

    def _calculate_average(
        self, daily_usage: list[DailyUsageResponse], days: int
    ) -> DailyUsageResponse:
        """平均を計算"""
        if not daily_usage or days == 0:
            return DailyUsageResponse(
                date=datetime.now(timezone.utc),
                api_calls=0,
                analyses_run=0,
                reports_generated=0,
                scheduled_posts=0,
                ai_generations=0,
                platform_usage={},
            )

        total = self._calculate_total(daily_usage)
        avg_platform_usage = {
            k: v // days for k, v in total.platform_usage.items()
        }

        return DailyUsageResponse(
            date=total.date,
            api_calls=total.api_calls // days,
            analyses_run=total.analyses_run // days,
            reports_generated=total.reports_generated // days,
            scheduled_posts=total.scheduled_posts // days,
            ai_generations=total.ai_generations // days,
            platform_usage=avg_platform_usage,
        )

    def get_monthly_summary(
        self, user_id: str, year_month: Optional[str] = None
    ) -> Optional[MonthlyUsageSummaryResponse]:
        """月次サマリーを取得"""
        if year_month is None:
            year_month = datetime.now(timezone.utc).strftime("%Y-%m")

        summary = (
            self.db.query(MonthlyUsageSummary)
            .filter(
                and_(
                    MonthlyUsageSummary.user_id == user_id,
                    MonthlyUsageSummary.year_month == year_month,
                )
            )
            .first()
        )

        if not summary:
            # 日次データから計算
            return self._calculate_monthly_summary(user_id, year_month)

        return self._to_monthly_summary_response(summary)

    def _calculate_monthly_summary(
        self, user_id: str, year_month: str
    ) -> Optional[MonthlyUsageSummaryResponse]:
        """日次データから月次サマリーを計算"""
        year, month = map(int, year_month.split("-"))
        start_date = datetime(year, month, 1, tzinfo=timezone.utc)
        if month == 12:
            end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end_date = datetime(year, month + 1, 1, tzinfo=timezone.utc)

        usages = (
            self.db.query(DailyUsage)
            .filter(
                and_(
                    DailyUsage.user_id == user_id,
                    DailyUsage.date >= start_date,
                    DailyUsage.date < end_date,
                )
            )
            .all()
        )

        if not usages:
            return None

        total_platform_usage: dict[str, int] = {}
        peak_api_calls = 0
        peak_date = None

        for usage in usages:
            platform_data = json.loads(usage.platform_usage or "{}")
            for platform, count in platform_data.items():
                total_platform_usage[platform] = (
                    total_platform_usage.get(platform, 0) + count
                )
            if usage.api_calls > peak_api_calls:
                peak_api_calls = usage.api_calls
                peak_date = usage.date

        return MonthlyUsageSummaryResponse(
            year_month=year_month,
            total_api_calls=sum(u.api_calls for u in usages),
            total_analyses=sum(u.analyses_run for u in usages),
            total_reports=sum(u.reports_generated for u in usages),
            total_scheduled_posts=sum(u.scheduled_posts for u in usages),
            total_ai_generations=sum(u.ai_generations for u in usages),
            peak_daily_api_calls=peak_api_calls,
            peak_date=peak_date,
            platform_usage=total_platform_usage,
        )

    def get_api_call_logs(
        self,
        user_id: str,
        page: int = 1,
        per_page: int = 20,
        endpoint_filter: Optional[str] = None,
    ) -> ApiCallLogsResponse:
        """API呼び出しログを取得"""
        query = self.db.query(ApiCallLog).filter(ApiCallLog.user_id == user_id)

        if endpoint_filter:
            query = query.filter(ApiCallLog.endpoint.contains(endpoint_filter))

        total = query.count()
        pages = (total + per_page - 1) // per_page

        logs = (
            query.order_by(ApiCallLog.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        items = [
            ApiCallLogResponse(
                id=log.id,
                endpoint=log.endpoint,
                method=log.method,
                status_code=log.status_code,
                response_time_ms=log.response_time_ms,
                created_at=log.created_at,
            )
            for log in logs
        ]

        return ApiCallLogsResponse(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        )

    def get_usage_trend(
        self, user_id: str, days: int = 7
    ) -> UsageTrendResponse:
        """使用量トレンドを取得"""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        prev_start_date = start_date - timedelta(days=days)

        # 現在期間のデータ
        current_usages = (
            self.db.query(DailyUsage)
            .filter(
                and_(
                    DailyUsage.user_id == user_id,
                    DailyUsage.date >= start_date,
                    DailyUsage.date <= end_date,
                )
            )
            .order_by(DailyUsage.date.asc())
            .all()
        )

        # 前期間のデータ
        prev_usages = (
            self.db.query(DailyUsage)
            .filter(
                and_(
                    DailyUsage.user_id == user_id,
                    DailyUsage.date >= prev_start_date,
                    DailyUsage.date < start_date,
                )
            )
            .all()
        )

        data = [
            {
                "date": u.date.isoformat(),
                "api_calls": u.api_calls,
                "analyses": u.analyses_run,
                "reports": u.reports_generated,
                "scheduled_posts": u.scheduled_posts,
                "ai_generations": u.ai_generations,
            }
            for u in current_usages
        ]

        # トレンド（前期比）を計算
        current_total = sum(u.api_calls for u in current_usages)
        prev_total = sum(u.api_calls for u in prev_usages)

        trend_percent = {
            "api_calls": (
                ((current_total - prev_total) / prev_total * 100)
                if prev_total > 0
                else 0
            ),
            "analyses": self._calc_trend(
                sum(u.analyses_run for u in current_usages),
                sum(u.analyses_run for u in prev_usages),
            ),
            "reports": self._calc_trend(
                sum(u.reports_generated for u in current_usages),
                sum(u.reports_generated for u in prev_usages),
            ),
        }

        return UsageTrendResponse(
            period="daily" if days <= 7 else "weekly" if days <= 30 else "monthly",
            data=data,
            trend_percent=trend_percent,
        )

    def _calc_trend(self, current: int, prev: int) -> float:
        """トレンド（%）を計算"""
        if prev == 0:
            return 0 if current == 0 else 100
        return (current - prev) / prev * 100

    def get_upgrade_recommendation(
        self, user_id: str, plan: str
    ) -> UpgradeRecommendation:
        """アップグレード推奨を取得"""
        usage_with_limits = self.get_usage_with_limits(user_id, plan)
        today = usage_with_limits.today
        limits = usage_with_limits.limits

        # 使用率を計算
        current_usage_vs_limit = usage_with_limits.usage_percent

        # アップグレード判定
        should_upgrade = False
        reason = None
        recommended_plan = None

        if plan == "free":
            # Free プラン: 80%以上使用でアップグレード推奨
            if any(v >= 80 for v in current_usage_vs_limit.values() if v >= 0):
                should_upgrade = True
                reason = "使用量が制限の80%を超えています。Proプランへのアップグレードをお勧めします。"
                recommended_plan = PlanTier.PRO
        elif plan == "pro":
            # Pro プラン: 90%以上使用でアップグレード推奨
            if any(v >= 90 for v in current_usage_vs_limit.values() if v >= 0):
                should_upgrade = True
                reason = "使用量が制限の90%を超えています。Businessプランへのアップグレードをお勧めします。"
                recommended_plan = PlanTier.BUSINESS
        elif plan == "business":
            # Business プラン: 95%以上使用でアップグレード推奨
            if any(v >= 95 for v in current_usage_vs_limit.values() if v >= 0):
                should_upgrade = True
                reason = "使用量が制限の95%を超えています。Enterpriseプランへのアップグレードをお勧めします。"
                recommended_plan = PlanTier.ENTERPRISE

        return UpgradeRecommendation(
            should_upgrade=should_upgrade,
            reason=reason,
            recommended_plan=recommended_plan,
            current_usage_vs_limit=current_usage_vs_limit,
            projected_savings=None,  # 将来の実装
        )

    def get_usage_dashboard(
        self, user_id: str, plan: str
    ) -> UsageDashboardResponse:
        """使用量ダッシュボード情報を取得"""
        usage_with_limits = self.get_usage_with_limits(user_id, plan)
        monthly_summary = self.get_monthly_summary(user_id)
        trend = self.get_usage_trend(user_id)
        upgrade_recommendation = self.get_upgrade_recommendation(user_id, plan)

        return UsageDashboardResponse(
            current_plan=PlanTier(plan.lower()),
            usage_with_limits=usage_with_limits,
            monthly_summary=monthly_summary,
            trend=trend,
            upgrade_recommendation=upgrade_recommendation,
        )

    def check_limit(
        self, user_id: str, plan: str, usage_type: str, count: int = 1
    ) -> tuple[bool, str]:
        """
        制限をチェック

        Returns:
            tuple[bool, str]: (制限内かどうか, メッセージ)
        """
        today = self.get_today_usage(user_id)
        limits = self.get_plan_limits(plan)

        if usage_type == "api_call":
            limit = limits.api_calls_per_day
            current = today.api_calls
        elif usage_type == "analysis":
            limit = limits.analyses_per_day
            current = today.analyses_run
        elif usage_type == "report":
            # レポートは月次制限
            monthly = self.get_monthly_summary(user_id)
            limit = limits.reports_per_month
            current = monthly.total_reports if monthly else 0
        elif usage_type == "scheduled_post":
            limit = limits.scheduled_posts_per_day
            current = today.scheduled_posts
        elif usage_type == "ai_generation":
            limit = limits.ai_generations_per_day
            current = today.ai_generations
        else:
            return True, "OK"

        if limit < 0:  # 無制限
            return True, "OK"

        if current + count > limit:
            return False, f"{usage_type}の制限（{limit}/日）を超えています"

        return True, "OK"

    def _to_daily_usage_response(self, usage: DailyUsage) -> DailyUsageResponse:
        """DailyUsage を DailyUsageResponse に変換"""
        return DailyUsageResponse(
            date=usage.date,
            api_calls=usage.api_calls,
            analyses_run=usage.analyses_run,
            reports_generated=usage.reports_generated,
            scheduled_posts=usage.scheduled_posts,
            ai_generations=usage.ai_generations,
            platform_usage=json.loads(usage.platform_usage or "{}"),
        )

    def _to_monthly_summary_response(
        self, summary: MonthlyUsageSummary
    ) -> MonthlyUsageSummaryResponse:
        """MonthlyUsageSummary を MonthlyUsageSummaryResponse に変換"""
        return MonthlyUsageSummaryResponse(
            year_month=summary.year_month,
            total_api_calls=summary.total_api_calls,
            total_analyses=summary.total_analyses,
            total_reports=summary.total_reports,
            total_scheduled_posts=summary.total_scheduled_posts,
            total_ai_generations=summary.total_ai_generations,
            peak_daily_api_calls=summary.peak_daily_api_calls,
            peak_date=summary.peak_date,
            platform_usage=json.loads(summary.platform_usage or "{}"),
        )
