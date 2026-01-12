"""
使用量モニタリングAPI

プラン別のAPI使用量を確認・管理するエンドポイント
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db.base import get_db
from ..db.models import User
from ..dependencies import get_current_user
from ..schemas import (
    ApiCallLogsResponse,
    DailyUsageResponse,
    MonthlyUsageSummaryResponse,
    PlanLimits,
    UpgradeRecommendation,
    UsageDashboardResponse,
    UsageHistoryResponse,
    UsageTrendResponse,
    UsageWithLimits,
)
from ..usage.service import UsageService

router = APIRouter(prefix="/usage", tags=["Usage"])


@router.get(
    "/dashboard",
    response_model=UsageDashboardResponse,
    summary="使用量ダッシュボード取得",
    description="現在の使用量、制限、トレンド、アップグレード推奨を含むダッシュボード情報を取得",
)
async def get_usage_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UsageDashboardResponse:
    """使用量ダッシュボード情報を取得"""
    service = UsageService(db)
    return service.get_usage_dashboard(current_user.id, current_user.role)


@router.get(
    "/today",
    response_model=DailyUsageResponse,
    summary="今日の使用量取得",
    description="今日のAPI使用量を取得",
)
async def get_today_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DailyUsageResponse:
    """今日の使用量を取得"""
    service = UsageService(db)
    return service.get_today_usage(current_user.id)


@router.get(
    "/with-limits",
    response_model=UsageWithLimits,
    summary="使用量と制限取得",
    description="今日の使用量とプラン制限、残り使用量、使用率を取得",
)
async def get_usage_with_limits(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UsageWithLimits:
    """使用量と制限の統合情報を取得"""
    service = UsageService(db)
    return service.get_usage_with_limits(current_user.id, current_user.role)


@router.get(
    "/limits",
    response_model=PlanLimits,
    summary="プラン制限取得",
    description="現在のプランの制限情報を取得",
)
async def get_plan_limits(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PlanLimits:
    """プラン制限を取得"""
    service = UsageService(db)
    return service.get_plan_limits(current_user.role)


@router.get(
    "/history",
    response_model=UsageHistoryResponse,
    summary="使用量履歴取得",
    description="指定期間の使用量履歴を取得",
)
async def get_usage_history(
    days: int = Query(default=30, ge=1, le=90, description="取得する日数"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UsageHistoryResponse:
    """使用量履歴を取得"""
    service = UsageService(db)
    return service.get_usage_history(current_user.id, days=days)


@router.get(
    "/monthly",
    response_model=Optional[MonthlyUsageSummaryResponse],
    summary="月次使用量サマリー取得",
    description="指定月の使用量サマリーを取得",
)
async def get_monthly_summary(
    year_month: Optional[str] = Query(
        default=None,
        description="対象年月（YYYY-MM形式）。未指定の場合は今月",
        pattern=r"^\d{4}-\d{2}$",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Optional[MonthlyUsageSummaryResponse]:
    """月次サマリーを取得"""
    service = UsageService(db)
    return service.get_monthly_summary(current_user.id, year_month)


@router.get(
    "/trend",
    response_model=UsageTrendResponse,
    summary="使用量トレンド取得",
    description="使用量のトレンドデータを取得",
)
async def get_usage_trend(
    days: int = Query(default=7, ge=1, le=30, description="取得する日数"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UsageTrendResponse:
    """使用量トレンドを取得"""
    service = UsageService(db)
    return service.get_usage_trend(current_user.id, days)


@router.get(
    "/logs",
    response_model=ApiCallLogsResponse,
    summary="API呼び出しログ取得",
    description="API呼び出しの詳細ログを取得",
)
async def get_api_call_logs(
    page: int = Query(default=1, ge=1, description="ページ番号"),
    per_page: int = Query(default=20, ge=1, le=100, description="1ページあたりの件数"),
    endpoint: Optional[str] = Query(
        default=None, description="エンドポイントでフィルター"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiCallLogsResponse:
    """API呼び出しログを取得"""
    service = UsageService(db)
    return service.get_api_call_logs(
        current_user.id,
        page=page,
        per_page=per_page,
        endpoint_filter=endpoint,
    )


@router.get(
    "/upgrade-recommendation",
    response_model=UpgradeRecommendation,
    summary="アップグレード推奨取得",
    description="現在の使用状況に基づくアップグレード推奨を取得",
)
async def get_upgrade_recommendation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UpgradeRecommendation:
    """アップグレード推奨を取得"""
    service = UsageService(db)
    return service.get_upgrade_recommendation(current_user.id, current_user.role)


@router.get(
    "/check/{usage_type}",
    summary="使用量制限チェック",
    description="指定された使用タイプの制限をチェック",
)
async def check_usage_limit(
    usage_type: str,
    count: int = Query(default=1, ge=1, description="使用する数量"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """使用量制限をチェック"""
    service = UsageService(db)
    allowed, message = service.check_limit(
        current_user.id, current_user.role, usage_type, count
    )
    return {
        "allowed": allowed,
        "message": message,
        "usage_type": usage_type,
        "requested_count": count,
    }
