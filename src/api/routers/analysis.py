"""
分析エンドポイント
"""

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..routers.auth import get_current_user
from ..schemas import (
    AnalysisRequest,
    AnalysisResponse,
    AnalysisSummary,
    ErrorResponse,
    PaginatedResponse,
    UserRole,
)

router = APIRouter()

# 仮のインメモリストレージ（本番ではDBを使用）
_analyses_db: dict[str, dict] = {}

# プラン別制限
PLAN_LIMITS = {
    UserRole.FREE: {"period_days": 7, "api_calls_per_day": 100},
    UserRole.PRO: {"period_days": 90, "api_calls_per_day": 1000},
    UserRole.BUSINESS: {"period_days": 365, "api_calls_per_day": 10000},
    UserRole.ENTERPRISE: {"period_days": 365, "api_calls_per_day": 100000},
}


def _generate_analysis_id() -> str:
    """分析ID生成"""
    return f"analysis_{secrets.token_hex(8)}"


@router.post(
    "/",
    response_model=AnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
async def create_analysis(
    request: AnalysisRequest,
    current_user: dict = Depends(get_current_user),
) -> AnalysisResponse:
    """分析を作成"""
    user_role = current_user["role"]
    limits = PLAN_LIMITS[user_role]

    # プランに応じた期間制限チェック
    if request.period_days > limits["period_days"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"現在のプラン（{user_role.value}）では{limits['period_days']}日までの分析が可能です",
        )

    now = datetime.now(timezone.utc)
    analysis_id = _generate_analysis_id()

    # 分析実行（本番では実際のTwitter API連携）
    # ここではモックデータを返す
    summary = AnalysisSummary(
        total_posts=25,
        total_likes=1250,
        total_retweets=320,
        engagement_rate=4.8,
        best_hour=21,
        top_hashtags=["#Python", "#AI", "#Tech"],
    )

    analysis = {
        "id": analysis_id,
        "user_id": current_user["id"],
        "platform": request.platform,
        "period_start": now - timedelta(days=request.period_days),
        "period_end": now,
        "summary": summary,
        "created_at": now,
    }

    _analyses_db[analysis_id] = analysis

    return AnalysisResponse(
        id=analysis_id,
        user_id=current_user["id"],
        platform=request.platform,
        period_start=analysis["period_start"],
        period_end=analysis["period_end"],
        summary=summary,
        created_at=now,
    )


@router.get(
    "/",
    response_model=PaginatedResponse,
)
async def list_analyses(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
) -> PaginatedResponse:
    """分析一覧取得"""
    user_analyses = [
        a for a in _analyses_db.values() if a["user_id"] == current_user["id"]
    ]

    # ソート（新しい順）
    user_analyses.sort(key=lambda x: x["created_at"], reverse=True)

    # ページネーション
    total = len(user_analyses)
    start = (page - 1) * per_page
    end = start + per_page
    items = user_analyses[start:end]

    # AnalysisResponseに変換
    response_items = [
        AnalysisResponse(
            id=a["id"],
            user_id=a["user_id"],
            platform=a["platform"],
            period_start=a["period_start"],
            period_end=a["period_end"],
            summary=a["summary"],
            created_at=a["created_at"],
        )
        for a in items
    ]

    return PaginatedResponse(
        items=response_items,
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page if total > 0 else 1,
    )


@router.get(
    "/{analysis_id}",
    response_model=AnalysisResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_analysis(
    analysis_id: str,
    current_user: dict = Depends(get_current_user),
) -> AnalysisResponse:
    """分析詳細取得"""
    analysis = _analyses_db.get(analysis_id)

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析が見つかりません",
        )

    if analysis["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析が見つかりません",
        )

    return AnalysisResponse(
        id=analysis["id"],
        user_id=analysis["user_id"],
        platform=analysis["platform"],
        period_start=analysis["period_start"],
        period_end=analysis["period_end"],
        summary=analysis["summary"],
        created_at=analysis["created_at"],
    )


@router.delete(
    "/{analysis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
)
async def delete_analysis(
    analysis_id: str,
    current_user: dict = Depends(get_current_user),
) -> None:
    """分析削除"""
    analysis = _analyses_db.get(analysis_id)

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析が見つかりません",
        )

    if analysis["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析が見つかりません",
        )

    del _analyses_db[analysis_id]
