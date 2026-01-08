"""
レポートエンドポイント
"""

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..routers.auth import get_current_user
from ..schemas import (
    ErrorResponse,
    PaginatedResponse,
    ReportRequest,
    ReportResponse,
    ReportType,
    UserRole,
)

router = APIRouter()

# 仮のインメモリストレージ（本番ではDBを使用）
_reports_db: dict[str, dict] = {}

# プラン別制限
PLAN_REPORT_LIMITS = {
    UserRole.FREE: {"reports_per_month": 1, "types": [ReportType.WEEKLY]},
    UserRole.PRO: {
        "reports_per_month": 4,
        "types": [ReportType.WEEKLY, ReportType.MONTHLY],
    },
    UserRole.BUSINESS: {
        "reports_per_month": -1,
        "types": [ReportType.WEEKLY, ReportType.MONTHLY, ReportType.CUSTOM],
    },
    UserRole.ENTERPRISE: {
        "reports_per_month": -1,
        "types": [ReportType.WEEKLY, ReportType.MONTHLY, ReportType.CUSTOM],
    },
}


def _generate_report_id() -> str:
    """レポートID生成"""
    return f"report_{secrets.token_hex(8)}"


@router.post(
    "/",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
async def create_report(
    request: ReportRequest,
    current_user: dict = Depends(get_current_user),
) -> ReportResponse:
    """レポート生成"""
    user_role = current_user["role"]
    limits = PLAN_REPORT_LIMITS[user_role]

    # レポートタイプ制限チェック
    if request.report_type not in limits["types"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"現在のプラン（{user_role.value}）では{request.report_type.value}レポートを利用できません",
        )

    now = datetime.now(timezone.utc)
    report_id = _generate_report_id()

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

    # レポート生成（本番では実際のレポート生成処理）
    # ここではモックデータを返す
    report = {
        "id": report_id,
        "user_id": current_user["id"],
        "report_type": request.report_type,
        "platform": request.platform,
        "period_start": period_start,
        "period_end": period_end,
        "html_url": f"/reports/{report_id}/html",
        "created_at": now,
    }

    _reports_db[report_id] = report

    return ReportResponse(
        id=report_id,
        user_id=current_user["id"],
        report_type=request.report_type,
        platform=request.platform,
        period_start=period_start,
        period_end=period_end,
        html_url=f"/api/v1/reports/{report_id}/html",
        created_at=now,
    )


@router.get(
    "/",
    response_model=PaginatedResponse,
)
async def list_reports(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    report_type: ReportType | None = None,
    current_user: dict = Depends(get_current_user),
) -> PaginatedResponse:
    """レポート一覧取得"""
    user_reports = [
        r for r in _reports_db.values() if r["user_id"] == current_user["id"]
    ]

    # タイプフィルタ
    if report_type:
        user_reports = [r for r in user_reports if r["report_type"] == report_type]

    # ソート（新しい順）
    user_reports.sort(key=lambda x: x["created_at"], reverse=True)

    # ページネーション
    total = len(user_reports)
    start = (page - 1) * per_page
    end = start + per_page
    items = user_reports[start:end]

    # ReportResponseに変換
    response_items = [
        ReportResponse(
            id=r["id"],
            user_id=r["user_id"],
            report_type=r["report_type"],
            platform=r["platform"],
            period_start=r["period_start"],
            period_end=r["period_end"],
            html_url=r["html_url"],
            created_at=r["created_at"],
        )
        for r in items
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
    current_user: dict = Depends(get_current_user),
) -> ReportResponse:
    """レポート詳細取得"""
    report = _reports_db.get(report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="レポートが見つかりません",
        )

    if report["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="レポートが見つかりません",
        )

    return ReportResponse(
        id=report["id"],
        user_id=report["user_id"],
        report_type=report["report_type"],
        platform=report["platform"],
        period_start=report["period_start"],
        period_end=report["period_end"],
        html_url=report["html_url"],
        created_at=report["created_at"],
    )


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
)
async def delete_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
) -> None:
    """レポート削除"""
    report = _reports_db.get(report_id)

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="レポートが見つかりません",
        )

    if report["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="レポートが見つかりません",
        )

    del _reports_db[report_id]
