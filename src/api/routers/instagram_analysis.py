"""
Instagram分析エンドポイント
"""

import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..dependencies import CurrentUser, DbSession
from ..repositories import AnalysisRepository
from ..schemas import (
    ErrorResponse,
    InstagramAnalysisDetail,
    InstagramAnalysisRequest,
    InstagramAnalysisResponse,
    InstagramAnalysisSummary,
    InstagramContentPattern,
    PaginatedResponse,
)

router = APIRouter()

# プラン別制限
PLAN_LIMITS = {
    "free": {"period_days": 7, "api_calls_per_day": 100, "instagram_enabled": False},
    "pro": {"period_days": 90, "api_calls_per_day": 1000, "instagram_enabled": True},
    "business": {
        "period_days": 365,
        "api_calls_per_day": 10000,
        "instagram_enabled": True,
    },
    "enterprise": {
        "period_days": 365,
        "api_calls_per_day": 100000,
        "instagram_enabled": True,
    },
}


def _check_instagram_access(role: str) -> None:
    """Instagram分析へのアクセス権をチェック"""
    limits = PLAN_LIMITS.get(role, PLAN_LIMITS["free"])
    if not limits.get("instagram_enabled", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Instagram分析はProプラン以上でご利用いただけます",
        )


@router.post(
    "/",
    response_model=InstagramAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
async def create_instagram_analysis(
    request: InstagramAnalysisRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> InstagramAnalysisResponse:
    """Instagram分析を作成"""
    _check_instagram_access(current_user.role)

    limits = PLAN_LIMITS.get(current_user.role, PLAN_LIMITS["free"])

    # プランに応じた期間制限チェック
    if request.period_days > limits["period_days"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"現在のプラン（{current_user.role}）では{limits['period_days']}日までの分析が可能です",
        )

    now = datetime.now(timezone.utc)
    analysis_repo = AnalysisRepository(db)

    # 分析実行（本番では実際のInstagram API連携）
    # ここではモックデータを生成
    total_posts = 18
    total_reels = 5
    total_likes = 2450
    total_comments = 185
    total_saves = 320
    engagement_rate = 5.2
    best_hour = 19
    top_hashtags = ["#fashion", "#lifestyle", "#ootd"]

    # データベースに保存（既存のAnalysisモデルを流用）
    analysis = analysis_repo.create(
        user_id=current_user.id,
        platform="instagram",
        period_start=now - timedelta(days=request.period_days),
        period_end=now,
        total_posts=total_posts,
        total_likes=total_likes,
        total_retweets=total_comments,  # Instagram: commentsをretweets枠に
        engagement_rate=engagement_rate,
        best_hour=best_hour,
        top_hashtags=top_hashtags,
    )

    return InstagramAnalysisResponse(
        id=analysis.id,
        user_id=analysis.user_id,
        platform="instagram",
        period_start=analysis.period_start,
        period_end=analysis.period_end,
        summary=InstagramAnalysisSummary(
            total_posts=analysis.total_posts,
            total_reels=total_reels,
            total_likes=analysis.total_likes,
            total_comments=analysis.total_retweets,
            total_saves=total_saves,
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
async def list_instagram_analyses(
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> PaginatedResponse:
    """Instagram分析一覧取得"""
    _check_instagram_access(current_user.role)

    analysis_repo = AnalysisRepository(db)

    # Instagramのみフィルタ
    total = analysis_repo.count_by_user_id_and_platform(current_user.id, "instagram")

    offset = (page - 1) * per_page
    analyses = analysis_repo.get_by_user_id_and_platform(
        user_id=current_user.id,
        platform="instagram",
        limit=per_page,
        offset=offset,
    )

    response_items = [
        InstagramAnalysisResponse(
            id=a.id,
            user_id=a.user_id,
            platform="instagram",
            period_start=a.period_start,
            period_end=a.period_end,
            summary=InstagramAnalysisSummary(
                total_posts=a.total_posts,
                total_reels=0,  # 個別取得時に設定
                total_likes=a.total_likes,
                total_comments=a.total_retweets,
                total_saves=0,  # 個別取得時に設定
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
    response_model=InstagramAnalysisDetail,
    responses={404: {"model": ErrorResponse}},
)
async def get_instagram_analysis(
    analysis_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> InstagramAnalysisDetail:
    """Instagram分析詳細取得"""
    _check_instagram_access(current_user.role)

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

    if analysis.platform != "instagram":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instagram分析が見つかりません",
        )

    # 詳細情報（本番では分析結果から取得）
    hourly_breakdown = [
        {"hour": h, "avg_likes": 50.0 + h * 2, "post_count": 2} for h in range(24)
    ]
    content_patterns = [
        InstagramContentPattern(
            pattern_type="tutorial",
            count=5,
            avg_engagement=125.5,
        ),
        InstagramContentPattern(
            pattern_type="behind_scenes",
            count=3,
            avg_engagement=98.2,
        ),
    ]
    recommendations = {
        "best_hours": [19, 20, 21],
        "suggested_hashtags": json.loads(analysis.top_hashtags),
        "reasoning": "19時〜21時の投稿が最もエンゲージメントが高い傾向にあります。",
    }

    return InstagramAnalysisDetail(
        id=analysis.id,
        user_id=analysis.user_id,
        platform="instagram",
        period_start=analysis.period_start,
        period_end=analysis.period_end,
        summary=InstagramAnalysisSummary(
            total_posts=analysis.total_posts,
            total_reels=5,
            total_likes=analysis.total_likes,
            total_comments=analysis.total_retweets,
            total_saves=320,
            engagement_rate=analysis.engagement_rate,
            best_hour=analysis.best_hour,
            top_hashtags=json.loads(analysis.top_hashtags),
        ),
        hourly_breakdown=hourly_breakdown,
        content_patterns=content_patterns,
        recommendations=recommendations,
        created_at=analysis.created_at,
    )


@router.delete(
    "/{analysis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
)
async def delete_instagram_analysis(
    analysis_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Instagram分析削除"""
    _check_instagram_access(current_user.role)

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

    if analysis.platform != "instagram":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instagram分析が見つかりません",
        )

    analysis_repo.delete(analysis)
