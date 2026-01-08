"""
分析エンドポイント
"""

import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..dependencies import CurrentUser, DbSession
from ..repositories import AnalysisRepository
from ..schemas import (
    AnalysisRequest,
    AnalysisResponse,
    AnalysisSummary,
    ErrorResponse,
    PaginatedResponse,
    UserRole,
)

router = APIRouter()

# プラン別制限
PLAN_LIMITS = {
    "free": {"period_days": 7, "api_calls_per_day": 100},
    "pro": {"period_days": 90, "api_calls_per_day": 1000},
    "business": {"period_days": 365, "api_calls_per_day": 10000},
    "enterprise": {"period_days": 365, "api_calls_per_day": 100000},
}


@router.post(
    "/",
    response_model=AnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
async def create_analysis(
    request: AnalysisRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> AnalysisResponse:
    """分析を作成"""
    limits = PLAN_LIMITS.get(current_user.role, PLAN_LIMITS["free"])

    # プランに応じた期間制限チェック
    if request.period_days > limits["period_days"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"現在のプラン（{current_user.role}）では{limits['period_days']}日までの分析が可能です",
        )

    now = datetime.now(timezone.utc)
    analysis_repo = AnalysisRepository(db)

    # 分析実行（本番では実際のTwitter API連携）
    # ここではモックデータを生成
    total_posts = 25
    total_likes = 1250
    total_retweets = 320
    engagement_rate = 4.8
    best_hour = 21
    top_hashtags = ["#Python", "#AI", "#Tech"]

    # データベースに保存
    analysis = analysis_repo.create(
        user_id=current_user.id,
        platform=request.platform,
        period_start=now - timedelta(days=request.period_days),
        period_end=now,
        total_posts=total_posts,
        total_likes=total_likes,
        total_retweets=total_retweets,
        engagement_rate=engagement_rate,
        best_hour=best_hour,
        top_hashtags=top_hashtags,
    )

    return AnalysisResponse(
        id=analysis.id,
        user_id=analysis.user_id,
        platform=analysis.platform,
        period_start=analysis.period_start,
        period_end=analysis.period_end,
        summary=AnalysisSummary(
            total_posts=analysis.total_posts,
            total_likes=analysis.total_likes,
            total_retweets=analysis.total_retweets,
            engagement_rate=analysis.engagement_rate,
            best_hour=analysis.best_hour,
            top_hashtags=json.loads(analysis.top_hashtags),
        ),
        created_at=analysis.created_at,
    )


@router.get(
    "/",
    response_model=PaginatedResponse,
)
async def list_analyses(
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> PaginatedResponse:
    """分析一覧取得"""
    analysis_repo = AnalysisRepository(db)

    # 総数取得
    total = analysis_repo.count_by_user_id(current_user.id)

    # ページネーション
    offset = (page - 1) * per_page
    analyses = analysis_repo.get_by_user_id(
        user_id=current_user.id,
        limit=per_page,
        offset=offset,
    )

    # AnalysisResponseに変換
    response_items = [
        AnalysisResponse(
            id=a.id,
            user_id=a.user_id,
            platform=a.platform,
            period_start=a.period_start,
            period_end=a.period_end,
            summary=AnalysisSummary(
                total_posts=a.total_posts,
                total_likes=a.total_likes,
                total_retweets=a.total_retweets,
                engagement_rate=a.engagement_rate,
                best_hour=a.best_hour,
                top_hashtags=json.loads(a.top_hashtags),
            ),
            created_at=a.created_at,
        )
        for a in analyses
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
    db: DbSession,
    current_user: CurrentUser,
) -> AnalysisResponse:
    """分析詳細取得"""
    analysis_repo = AnalysisRepository(db)
    analysis = analysis_repo.get_by_id(analysis_id)

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析が見つかりません",
        )

    if analysis.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析が見つかりません",
        )

    return AnalysisResponse(
        id=analysis.id,
        user_id=analysis.user_id,
        platform=analysis.platform,
        period_start=analysis.period_start,
        period_end=analysis.period_end,
        summary=AnalysisSummary(
            total_posts=analysis.total_posts,
            total_likes=analysis.total_likes,
            total_retweets=analysis.total_retweets,
            engagement_rate=analysis.engagement_rate,
            best_hour=analysis.best_hour,
            top_hashtags=json.loads(analysis.top_hashtags),
        ),
        created_at=analysis.created_at,
    )


@router.delete(
    "/{analysis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
)
async def delete_analysis(
    analysis_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """分析削除"""
    analysis_repo = AnalysisRepository(db)
    analysis = analysis_repo.get_by_id(analysis_id)

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析が見つかりません",
        )

    if analysis.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分析が見つかりません",
        )

    analysis_repo.delete(analysis)
