"""
TikTok分析エンドポイント
"""

import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..dependencies import CurrentUser, DbSession
from ..repositories import AnalysisRepository
from ..schemas import (
    ErrorResponse,
    PaginatedResponse,
    TikTokAnalysisDetail,
    TikTokAnalysisRequest,
    TikTokAnalysisResponse,
    TikTokAnalysisSummary,
    TikTokContentPattern,
    TikTokSoundInfo,
)

router = APIRouter()

# プラン別制限
PLAN_LIMITS = {
    "free": {"period_days": 7, "api_calls_per_day": 100, "tiktok_enabled": False},
    "pro": {"period_days": 90, "api_calls_per_day": 1000, "tiktok_enabled": True},
    "business": {
        "period_days": 365,
        "api_calls_per_day": 10000,
        "tiktok_enabled": True,
    },
    "enterprise": {
        "period_days": 365,
        "api_calls_per_day": 100000,
        "tiktok_enabled": True,
    },
}


def _check_tiktok_access(role: str) -> None:
    """TikTok分析へのアクセス権をチェック"""
    limits = PLAN_LIMITS.get(role, PLAN_LIMITS["free"])
    if not limits.get("tiktok_enabled", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="TikTok分析はProプラン以上でご利用いただけます",
        )


@router.post(
    "/",
    response_model=TikTokAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
async def create_tiktok_analysis(
    request: TikTokAnalysisRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> TikTokAnalysisResponse:
    """TikTok分析を作成"""
    _check_tiktok_access(current_user.role)

    limits = PLAN_LIMITS.get(current_user.role, PLAN_LIMITS["free"])

    # プランに応じた期間制限チェック
    if request.period_days > limits["period_days"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"現在のプラン（{current_user.role}）では{limits['period_days']}日までの分析が可能です",
        )

    now = datetime.now(timezone.utc)
    analysis_repo = AnalysisRepository(db)

    # 分析実行（本番では実際のTikTok API連携）
    # ここではモックデータを生成
    total_videos = 25
    total_views = 125000
    total_likes = 8500
    total_comments = 420
    total_shares = 180
    engagement_rate = 7.28  # (likes + comments + shares) / views * 100
    view_to_like_ratio = 6.8  # likes / views * 100
    best_hour = 21
    best_duration_range = "15-30s"
    top_hashtags = ["#fyp", "#tiktok", "#viral"]

    # データベースに保存（既存のAnalysisモデルを流用）
    # total_retweets枠にtotal_viewsを保存（TikTok固有）
    analysis = analysis_repo.create(
        user_id=current_user.id,
        platform="tiktok",
        period_start=now - timedelta(days=request.period_days),
        period_end=now,
        total_posts=total_videos,
        total_likes=total_likes,
        total_retweets=total_views,  # TikTok: viewsをretweets枠に
        engagement_rate=engagement_rate,
        best_hour=best_hour,
        top_hashtags=top_hashtags,
    )

    return TikTokAnalysisResponse(
        id=analysis.id,
        user_id=analysis.user_id,
        platform="tiktok",
        period_start=analysis.period_start,
        period_end=analysis.period_end,
        summary=TikTokAnalysisSummary(
            total_videos=analysis.total_posts,
            total_views=analysis.total_retweets,
            total_likes=analysis.total_likes,
            total_comments=total_comments,
            total_shares=total_shares,
            engagement_rate=analysis.engagement_rate,
            view_to_like_ratio=view_to_like_ratio,
            avg_views_per_video=total_views / total_videos if total_videos > 0 else 0,
            best_hour=analysis.best_hour,
            best_duration_range=best_duration_range,
            top_hashtags=json.loads(analysis.top_hashtags),
        ),
        created_at=analysis.created_at,
    )


@router.get(
    "/",
    response_model=PaginatedResponse,
)
async def list_tiktok_analyses(
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> PaginatedResponse:
    """TikTok分析一覧取得"""
    _check_tiktok_access(current_user.role)

    analysis_repo = AnalysisRepository(db)

    # TikTokのみフィルタ
    total = analysis_repo.count_by_user_id_and_platform(current_user.id, "tiktok")

    offset = (page - 1) * per_page
    analyses = analysis_repo.get_by_user_id_and_platform(
        user_id=current_user.id,
        platform="tiktok",
        limit=per_page,
        offset=offset,
    )

    response_items = [
        TikTokAnalysisResponse(
            id=a.id,
            user_id=a.user_id,
            platform="tiktok",
            period_start=a.period_start,
            period_end=a.period_end,
            summary=TikTokAnalysisSummary(
                total_videos=a.total_posts,
                total_views=a.total_retweets,
                total_likes=a.total_likes,
                total_comments=0,  # 個別取得時に設定
                total_shares=0,  # 個別取得時に設定
                engagement_rate=a.engagement_rate,
                view_to_like_ratio=0.0,  # 個別取得時に計算
                avg_views_per_video=(
                    a.total_retweets / a.total_posts if a.total_posts > 0 else 0
                ),
                best_hour=a.best_hour,
                best_duration_range=None,  # 個別取得時に設定
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
    response_model=TikTokAnalysisDetail,
    responses={404: {"model": ErrorResponse}},
)
async def get_tiktok_analysis(
    analysis_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> TikTokAnalysisDetail:
    """TikTok分析詳細取得"""
    _check_tiktok_access(current_user.role)

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

    if analysis.platform != "tiktok":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="TikTok分析が見つかりません",
        )

    # 詳細情報（本番では分析結果から取得）
    hourly_breakdown = [
        {"hour": h, "avg_likes": 80.0 + h * 3, "avg_views": 3000.0 + h * 100, "post_count": 2}
        for h in range(24)
    ]
    content_patterns = [
        TikTokContentPattern(
            pattern_type="tutorial",
            count=8,
            avg_engagement=450.5,
        ),
        TikTokContentPattern(
            pattern_type="challenge",
            count=5,
            avg_engagement=680.2,
        ),
        TikTokContentPattern(
            pattern_type="transformation",
            count=3,
            avg_engagement=520.8,
        ),
    ]
    sound_analysis = [
        TikTokSoundInfo(
            sound_id="sound_001",
            sound_name="Original Sound - Creator",
            usage_count=10,
            avg_engagement=380.5,
            is_trending=False,
        ),
        TikTokSoundInfo(
            sound_id="sound_002",
            sound_name="Trending Beat 2026",
            usage_count=5,
            avg_engagement=750.2,
            is_trending=True,
        ),
    ]
    recommendations = {
        "best_hours": [19, 20, 21],
        "suggested_hashtags": json.loads(analysis.top_hashtags),
        "best_duration": "15-30s",
        "trending_sounds": ["Trending Beat 2026"],
        "reasoning": "21時前後の投稿が最もエンゲージメントが高い傾向にあります。15-30秒の動画が最も効果的です。",
    }

    return TikTokAnalysisDetail(
        id=analysis.id,
        user_id=analysis.user_id,
        platform="tiktok",
        period_start=analysis.period_start,
        period_end=analysis.period_end,
        summary=TikTokAnalysisSummary(
            total_videos=analysis.total_posts,
            total_views=analysis.total_retweets,
            total_likes=analysis.total_likes,
            total_comments=420,
            total_shares=180,
            engagement_rate=analysis.engagement_rate,
            view_to_like_ratio=6.8,
            avg_views_per_video=(
                analysis.total_retweets / analysis.total_posts
                if analysis.total_posts > 0
                else 0
            ),
            best_hour=analysis.best_hour,
            best_duration_range="15-30s",
            top_hashtags=json.loads(analysis.top_hashtags),
        ),
        hourly_breakdown=hourly_breakdown,
        content_patterns=content_patterns,
        sound_analysis=sound_analysis,
        recommendations=recommendations,
        avg_video_duration=22.5,
        duet_performance=380.5,
        stitch_performance=290.2,
        created_at=analysis.created_at,
    )


@router.delete(
    "/{analysis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
)
async def delete_tiktok_analysis(
    analysis_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """TikTok分析削除"""
    _check_tiktok_access(current_user.role)

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

    if analysis.platform != "tiktok":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="TikTok分析が見つかりません",
        )

    analysis_repo.delete(analysis)
