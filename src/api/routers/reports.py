"""
レポートエンドポイント
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..dependencies import CurrentUser, DbSession
from ..repositories import ReportRepository
from ..schemas import (
    ErrorResponse,
    PaginatedResponse,
    ReportRequest,
    ReportResponse,
    ReportType,
)

router = APIRouter()

# プラン別制限
PLAN_REPORT_LIMITS = {
    "free": {"reports_per_month": 1, "types": ["weekly"]},
    "pro": {"reports_per_month": 4, "types": ["weekly", "monthly"]},
    "business": {"reports_per_month": -1, "types": ["weekly", "monthly", "custom"]},
    "enterprise": {"reports_per_month": -1, "types": ["weekly", "monthly", "custom"]},
}


@router.post(
    "/",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
async def create_report(
    request: ReportRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> ReportResponse:
    """レポート生成"""
    limits = PLAN_REPORT_LIMITS.get(current_user.role, PLAN_REPORT_LIMITS["free"])

    # レポートタイプ制限チェック
    if request.report_type.value not in limits["types"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"現在のプラン（{current_user.role}）では{request.report_type.value}レポートを利用できません",
        )

    now = datetime.now(timezone.utc)
    report_repo = ReportRepository(db)

    # 期間設定
    if request.report_type == ReportType.WEEKLY:
        period_start = now - timedelta(days=7)
        period_end = now
    elif request.report_type == ReportType.MONTHLY:
        period_start = now - timedelta(days=30)
        period_end = now
    else:
        # カスタム期間
        period_start = request.start_date or (now - timedelta(days=7))
        period_end = request.end_date or now

    # レポート作成
    report = report_repo.create(
        user_id=current_user.id,
        report_type=request.report_type.value,
        platform=request.platform,
        period_start=period_start,
        period_end=period_end,
        html_url=None,  # 後で生成
    )

    # HTML URLを設定
    html_url = f"/api/v1/reports/{report.id}/html"
    report = report_repo.update_html_url(report, html_url)

    return ReportResponse(
        id=report.id,
        user_id=report.user_id,
        report_type=ReportType(report.report_type),
        platform=report.platform,
        period_start=report.period_start,
        period_end=report.period_end,
        html_url=report.html_url,
        created_at=report.created_at,
    )


@router.get(
    "/",
    response_model=PaginatedResponse,
)
async def list_reports(
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    report_type: ReportType | None = None,
) -> PaginatedResponse:
    """レポート一覧取得"""
    report_repo = ReportRepository(db)

    # 総数取得
    report_type_str = report_type.value if report_type else None
    total = report_repo.count_by_user_id(
        user_id=current_user.id,
        report_type=report_type_str,
    )

    # ページネーション
    offset = (page - 1) * per_page
    reports = report_repo.get_by_user_id(
        user_id=current_user.id,
        report_type=report_type_str,
        limit=per_page,
        offset=offset,
    )

    # ReportResponseに変換
    response_items = [
        ReportResponse(
            id=r.id,
            user_id=r.user_id,
            report_type=ReportType(r.report_type),
            platform=r.platform,
            period_start=r.period_start,
            period_end=r.period_end,
            html_url=r.html_url,
            created_at=r.created_at,
        )
        for r in reports
    ]

    return PaginatedResponse(
        items=response_items,
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page if total > 0 else 1,
    )


@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_report(
    report_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> ReportResponse:
    """レポート詳細取得"""
    report_repo = ReportRepository(db)
    report = report_repo.get_by_id(report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="レポートが見つかりません",
        )

    if report.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="レポートが見つかりません",
        )

    return ReportResponse(
        id=report.id,
        user_id=report.user_id,
        report_type=ReportType(report.report_type),
        platform=report.platform,
        period_start=report.period_start,
        period_end=report.period_end,
        html_url=report.html_url,
        created_at=report.created_at,
    )


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
)
async def delete_report(
    report_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """レポート削除"""
    report_repo = ReportRepository(db)
    report = report_repo.get_by_id(report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="レポートが見つかりません",
        )

    if report.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="レポートが見つかりません",
        )

    report_repo.delete(report)
