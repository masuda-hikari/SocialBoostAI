"""
YouTube分析エンドポイント
"""

import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..dependencies import CurrentUser, DbSession
from ..repositories import AnalysisRepository
from ..schemas import (
    ErrorResponse,
    PaginatedResponse,
    YouTubeAnalysisDetail,
    YouTubeAnalysisRequest,
    YouTubeAnalysisResponse,
    YouTubeAnalysisSummary,
    YouTubeCategoryInfo,
    YouTubeContentPattern,
    YouTubeShortsVsVideoComparison,
    YouTubeTagInfo,
)

router = APIRouter()

# プラン別制限
PLAN_LIMITS = {
    "free": {"period_days": 7, "api_calls_per_day": 100, "youtube_enabled": False},
    "pro": {"period_days": 90, "api_calls_per_day": 1000, "youtube_enabled": True},
    "business": {
        "period_days": 365,
        "api_calls_per_day": 10000,
        "youtube_enabled": True,
    },
    "enterprise": {
        "period_days": 365,
        "api_calls_per_day": 100000,
        "youtube_enabled": True,
    },
}


def _check_youtube_access(role: str) -> None:
    """YouTube分析へのアクセス権をチェック"""
    limits = PLAN_LIMITS.get(role, PLAN_LIMITS["free"])
    if not limits.get("youtube_enabled", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="YouTube分析はProプラン以上でご利用いただけます",
        )


@router.post(
    "/",
    response_model=YouTubeAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
async def create_youtube_analysis(
    request: YouTubeAnalysisRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> YouTubeAnalysisResponse:
    """YouTube分析を作成"""
    _check_youtube_access(current_user.role)

    limits = PLAN_LIMITS.get(current_user.role, PLAN_LIMITS["free"])

    # プランに応じた期間制限チェック
    if request.period_days > limits["period_days"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"現在のプラン（{current_user.role}）では{limits['period_days']}日までの分析が可能です",
        )

    now = datetime.now(timezone.utc)
    analysis_repo = AnalysisRepository(db)

    # 分析実行（本番では実際のYouTube API連携）
    # ここではモックデータを生成
    total_videos = 18
    total_shorts = 7
    total_views = 250000
    total_likes = 12500
    total_comments = 850
    engagement_rate = 5.34  # (likes + comments) / views * 100
    view_to_like_ratio = 5.0  # likes / views * 100
    best_hour = 18
    best_duration_range = "10-20min"
    top_tags = ["#youtube", "#vlog", "#tutorial"]

    # データベースに保存（既存のAnalysisモデルを流用）
    # total_retweets枠にtotal_viewsを保存（YouTube固有）
    analysis = analysis_repo.create(
        user_id=current_user.id,
        platform="youtube",
        period_start=now - timedelta(days=request.period_days),
        period_end=now,
        total_posts=total_videos + total_shorts,
        total_likes=total_likes,
        total_retweets=total_views,  # YouTube: viewsをretweets枠に
        engagement_rate=engagement_rate,
        best_hour=best_hour,
        top_hashtags=top_tags,
    )

    return YouTubeAnalysisResponse(
        id=analysis.id,
        user_id=analysis.user_id,
        platform="youtube",
        period_start=analysis.period_start,
        period_end=analysis.period_end,
        summary=YouTubeAnalysisSummary(
            total_videos=total_videos,
            total_shorts=total_shorts,
            total_views=analysis.total_retweets,
            total_likes=analysis.total_likes,
            total_comments=total_comments,
            engagement_rate=analysis.engagement_rate,
            view_to_like_ratio=view_to_like_ratio,
            avg_views_per_video=total_views / (total_videos + total_shorts) if (total_videos + total_shorts) > 0 else 0,
            best_hour=analysis.best_hour,
            best_duration_range=best_duration_range,
            top_tags=json.loads(analysis.top_hashtags),
        ),
        created_at=analysis.created_at,
    )


@router.get(
    "/",
    response_model=PaginatedResponse,
)
async def list_youtube_analyses(
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> PaginatedResponse:
    """YouTube分析一覧取得"""
    _check_youtube_access(current_user.role)

    analysis_repo = AnalysisRepository(db)

    # YouTubeのみフィルタ
    total = analysis_repo.count_by_user_id_and_platform(current_user.id, "youtube")

    offset = (page - 1) * per_page
    analyses = analysis_repo.get_by_user_id_and_platform(
        user_id=current_user.id,
        platform="youtube",
        limit=per_page,
        offset=offset,
    )

    response_items = [
        YouTubeAnalysisResponse(
            id=a.id,
            user_id=a.user_id,
            platform="youtube",
            period_start=a.period_start,
            period_end=a.period_end,
            summary=YouTubeAnalysisSummary(
                total_videos=a.total_posts,
                total_shorts=0,  # 個別取得時に設定
                total_views=a.total_retweets,
                total_likes=a.total_likes,
                total_comments=0,  # 個別取得時に設定
                engagement_rate=a.engagement_rate,
                view_to_like_ratio=0.0,  # 個別取得時に計算
                avg_views_per_video=(
                    a.total_retweets / a.total_posts if a.total_posts > 0 else 0
                ),
                best_hour=a.best_hour,
                best_duration_range=None,  # 個別取得時に設定
                top_tags=json.loads(a.top_hashtags),
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
    response_model=YouTubeAnalysisDetail,
    responses={404: {"model": ErrorResponse}},
)
async def get_youtube_analysis(
    analysis_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> YouTubeAnalysisDetail:
    """YouTube分析詳細取得"""
    _check_youtube_access(current_user.role)

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

    if analysis.platform != "youtube":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="YouTube分析が見つかりません",
        )

    # 詳細情報（本番では分析結果から取得）
    hourly_breakdown = [
        {"hour": h, "avg_likes": 120.0 + h * 5, "avg_views": 8000.0 + h * 300, "post_count": 1}
        for h in range(24)
    ]
    content_patterns = [
        YouTubeContentPattern(
            pattern_type="tutorial",
            count=6,
            avg_engagement=850.5,
        ),
        YouTubeContentPattern(
            pattern_type="vlog",
            count=4,
            avg_engagement=620.2,
        ),
        YouTubeContentPattern(
            pattern_type="review",
            count=3,
            avg_engagement=780.8,
        ),
    ]
    tag_analysis = [
        YouTubeTagInfo(
            tag="tutorial",
            usage_count=6,
            total_views=85000,
            avg_engagement=850.5,
            effectiveness_score=1.35,
        ),
        YouTubeTagInfo(
            tag="vlog",
            usage_count=4,
            total_views=52000,
            avg_engagement=620.2,
            effectiveness_score=1.12,
        ),
    ]
    category_analysis = [
        YouTubeCategoryInfo(
            category_id="26",
            category_name="ハウツーとスタイル",
            video_count=8,
            total_views=95000,
            avg_engagement=920.5,
        ),
        YouTubeCategoryInfo(
            category_id="22",
            category_name="ブログ",
            video_count=5,
            total_views=62000,
            avg_engagement=680.2,
        ),
    ]
    shorts_vs_video = YouTubeShortsVsVideoComparison(
        shorts_count=7,
        shorts_avg_views=18000.0,
        shorts_avg_engagement=420.5,
        regular_count=18,
        regular_avg_views=12000.0,
        regular_avg_engagement=680.2,
        views_ratio=1.5,
        engagement_ratio=0.62,
    )
    recommendations = {
        "best_hours": [17, 18, 19],
        "suggested_hashtags": json.loads(analysis.top_hashtags),
        "best_duration": "10-20min",
        "shorts_recommendation": "Shortsは視聴数が高いがエンゲージメントは通常動画より低い傾向",
        "reasoning": "18時前後の投稿が最もエンゲージメントが高い傾向にあります。10-20分の動画が最も効果的です。",
    }

    return YouTubeAnalysisDetail(
        id=analysis.id,
        user_id=analysis.user_id,
        platform="youtube",
        period_start=analysis.period_start,
        period_end=analysis.period_end,
        summary=YouTubeAnalysisSummary(
            total_videos=18,
            total_shorts=7,
            total_views=analysis.total_retweets,
            total_likes=analysis.total_likes,
            total_comments=850,
            engagement_rate=analysis.engagement_rate,
            view_to_like_ratio=5.0,
            avg_views_per_video=(
                analysis.total_retweets / analysis.total_posts
                if analysis.total_posts > 0
                else 0
            ),
            best_hour=analysis.best_hour,
            best_duration_range="10-20min",
            top_tags=json.loads(analysis.top_hashtags),
        ),
        hourly_breakdown=hourly_breakdown,
        content_patterns=content_patterns,
        tag_analysis=tag_analysis,
        category_analysis=category_analysis,
        recommendations=recommendations,
        avg_video_duration=720.0,  # 12分
        shorts_vs_video=shorts_vs_video,
        created_at=analysis.created_at,
    )


@router.delete(
    "/{analysis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
)
async def delete_youtube_analysis(
    analysis_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """YouTube分析削除"""
    _check_youtube_access(current_user.role)

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

    if analysis.platform != "youtube":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="YouTube分析が見つかりません",
        )

    analysis_repo.delete(analysis)
