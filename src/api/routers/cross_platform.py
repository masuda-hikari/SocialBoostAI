"""
クロスプラットフォーム比較APIルーター
"""

import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...cross_platform import compare_platforms
from ...models import AnalysisResult, InstagramAnalysisResult
from ..db.base import get_db
from ..db.models import Analysis as AnalysisModel
from ..db.models import CrossPlatformComparison as ComparisonModel
from ..db.models import User
from ..dependencies import get_current_user
from ..repositories.comparison_repository import CrossPlatformComparisonRepository
from ..schemas import (
    ComparisonItemResponse,
    CrossPlatformComparisonRequest,
    CrossPlatformComparisonResponse,
    CrossPlatformComparisonSummary,
    ErrorResponse,
    PaginatedResponse,
    PlatformPerformanceSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/comparisons", tags=["cross-platform"])

# プラン別制限（比較機能はBusinessプラン以上）
COMPARISON_ALLOWED_ROLES = ["business", "enterprise"]


def _check_comparison_access(user: User) -> None:
    """比較機能アクセス権限チェック"""
    if user.role not in COMPARISON_ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="クロスプラットフォーム比較はBusinessプラン以上で利用可能です",
        )


def _db_to_response(comparison: ComparisonModel) -> CrossPlatformComparisonResponse:
    """DBモデルをレスポンスに変換"""
    twitter_perf = None
    instagram_perf = None

    if comparison.twitter_performance:
        twitter_data = json.loads(comparison.twitter_performance)
        twitter_perf = PlatformPerformanceSummary(**twitter_data)

    if comparison.instagram_performance:
        instagram_data = json.loads(comparison.instagram_performance)
        instagram_perf = PlatformPerformanceSummary(**instagram_data)

    comparison_items = [
        ComparisonItemResponse(**item)
        for item in json.loads(comparison.comparison_items)
    ]

    return CrossPlatformComparisonResponse(
        id=comparison.id,
        user_id=comparison.user_id,
        period_start=comparison.period_start,
        period_end=comparison.period_end,
        platforms_analyzed=json.loads(comparison.platforms_analyzed),
        twitter_performance=twitter_perf,
        instagram_performance=instagram_perf,
        comparison_items=comparison_items,
        overall_winner=comparison.overall_winner,
        cross_platform_insights=json.loads(comparison.cross_platform_insights),
        strategic_recommendations=json.loads(comparison.strategic_recommendations),
        synergy_opportunities=json.loads(comparison.synergy_opportunities),
        created_at=comparison.created_at,
    )


def _db_to_summary(comparison: ComparisonModel) -> CrossPlatformComparisonSummary:
    """DBモデルをサマリーに変換"""
    platforms = json.loads(comparison.platforms_analyzed)
    insights = json.loads(comparison.cross_platform_insights)

    # 総投稿数・エンゲージメント計算
    total_posts = 0
    total_engagement = 0

    if comparison.twitter_performance:
        twitter_data = json.loads(comparison.twitter_performance)
        total_posts += twitter_data.get("total_posts", 0)
        total_engagement += twitter_data.get("total_engagement", 0)

    if comparison.instagram_performance:
        instagram_data = json.loads(comparison.instagram_performance)
        total_posts += instagram_data.get("total_posts", 0)
        total_engagement += instagram_data.get("total_engagement", 0)

    return CrossPlatformComparisonSummary(
        id=comparison.id,
        user_id=comparison.user_id,
        period_start=comparison.period_start,
        period_end=comparison.period_end,
        platforms=platforms,
        total_posts=total_posts,
        total_engagement=total_engagement,
        best_platform=comparison.overall_winner,
        key_insight=insights[0] if insights else "",
        created_at=comparison.created_at,
    )


def _create_mock_twitter_analysis(
    period_start: datetime,
    period_end: datetime,
    analysis_model: Optional[AnalysisModel] = None,
) -> AnalysisResult:
    """モック/DB分析からAnalysisResultを作成"""
    from ...models import (
        ContentPattern,
        EngagementMetrics,
        HashtagAnalysis,
        HourlyEngagement,
    )

    if analysis_model:
        # DBから復元
        top_hashtags = (
            json.loads(analysis_model.top_hashtags)
            if analysis_model.top_hashtags
            else []
        )
        return AnalysisResult(
            period_start=analysis_model.period_start,
            period_end=analysis_model.period_end,
            total_posts=analysis_model.total_posts,
            metrics=EngagementMetrics(
                total_likes=analysis_model.total_likes,
                total_retweets=analysis_model.total_retweets,
                engagement_rate=analysis_model.engagement_rate,
                avg_likes_per_post=analysis_model.total_likes
                / max(1, analysis_model.total_posts),
                avg_retweets_per_post=analysis_model.total_retweets
                / max(1, analysis_model.total_posts),
            ),
            hourly_breakdown=[
                HourlyEngagement(
                    hour=h,
                    avg_likes=0,
                    avg_retweets=0,
                    post_count=0,
                    total_engagement=0,
                )
                for h in range(24)
            ],
            top_performing_posts=[],
            hashtag_analysis=[
                HashtagAnalysis(hashtag=tag, usage_count=1, effectiveness_score=1.0)
                for tag in top_hashtags[:5]
            ],
            content_patterns=[],
        )

    # デモ用モックデータ
    return AnalysisResult(
        period_start=period_start,
        period_end=period_end,
        total_posts=0,
        metrics=EngagementMetrics(),
        hourly_breakdown=[],
        top_performing_posts=[],
    )


def _create_mock_instagram_analysis(
    period_start: datetime,
    period_end: datetime,
    analysis_model: Optional[AnalysisModel] = None,
) -> InstagramAnalysisResult:
    """モック/DB分析からInstagramAnalysisResultを作成"""
    from ...models import (
        HashtagAnalysis,
        HourlyEngagement,
        InstagramEngagementMetrics,
    )

    if analysis_model:
        # DBから復元（Instagramデータ）
        top_hashtags = (
            json.loads(analysis_model.top_hashtags)
            if analysis_model.top_hashtags
            else []
        )
        return InstagramAnalysisResult(
            period_start=analysis_model.period_start,
            period_end=analysis_model.period_end,
            total_posts=analysis_model.total_posts,
            total_reels=0,
            metrics=InstagramEngagementMetrics(
                total_likes=analysis_model.total_likes,
                total_comments=analysis_model.total_retweets,  # retweets -> comments
                engagement_rate=analysis_model.engagement_rate,
                avg_likes_per_post=analysis_model.total_likes
                / max(1, analysis_model.total_posts),
                avg_comments_per_post=analysis_model.total_retweets
                / max(1, analysis_model.total_posts),
            ),
            hourly_breakdown=[
                HourlyEngagement(
                    hour=h,
                    avg_likes=0,
                    avg_retweets=0,
                    post_count=0,
                    total_engagement=0,
                )
                for h in range(24)
            ],
            top_performing_posts=[],
            top_performing_reels=[],
            hashtag_analysis=[
                HashtagAnalysis(hashtag=tag, usage_count=1, effectiveness_score=1.0)
                for tag in top_hashtags[:5]
            ],
            content_patterns=[],
        )

    # デモ用モックデータ
    return InstagramAnalysisResult(
        period_start=period_start,
        period_end=period_end,
        total_posts=0,
        total_reels=0,
        metrics=InstagramEngagementMetrics(),
    )


@router.post(
    "",
    response_model=CrossPlatformComparisonResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        403: {"model": ErrorResponse},
        400: {"model": ErrorResponse},
    },
)
async def create_comparison(
    request: CrossPlatformComparisonRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CrossPlatformComparisonResponse:
    """クロスプラットフォーム比較を実行

    Businessプラン以上で利用可能。
    Twitter分析IDとInstagram分析IDを指定して比較を実行します。
    """
    _check_comparison_access(current_user)

    # 期間設定
    now = datetime.now(UTC)
    period_end = now
    period_start = now - timedelta(days=request.period_days)

    # Twitter分析データ取得
    twitter_analysis = None
    if request.twitter_analysis_id:
        twitter_model = (
            db.query(AnalysisModel)
            .filter(
                AnalysisModel.id == request.twitter_analysis_id,
                AnalysisModel.user_id == current_user.id,
                AnalysisModel.platform == "twitter",
            )
            .first()
        )
        if twitter_model:
            twitter_analysis = _create_mock_twitter_analysis(
                period_start, period_end, twitter_model
            )

    # Instagram分析データ取得
    instagram_analysis = None
    if request.instagram_analysis_id:
        instagram_model = (
            db.query(AnalysisModel)
            .filter(
                AnalysisModel.id == request.instagram_analysis_id,
                AnalysisModel.user_id == current_user.id,
                AnalysisModel.platform == "instagram",
            )
            .first()
        )
        if instagram_model:
            instagram_analysis = _create_mock_instagram_analysis(
                period_start, period_end, instagram_model
            )

    # 両方のデータがない場合はエラー
    if not twitter_analysis and not instagram_analysis:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="比較には最低1つのプラットフォームの分析データが必要です",
        )

    # 比較実行
    comparison_result = compare_platforms(
        twitter_analysis=twitter_analysis,
        instagram_analysis=instagram_analysis,
        period_start=period_start,
        period_end=period_end,
    )

    # DBに保存
    repo = CrossPlatformComparisonRepository(db)

    twitter_perf_dict = None
    if comparison_result.twitter_performance:
        twitter_perf_dict = comparison_result.twitter_performance.model_dump()

    instagram_perf_dict = None
    if comparison_result.instagram_performance:
        instagram_perf_dict = comparison_result.instagram_performance.model_dump()

    comparison_items_dict = [
        item.model_dump() for item in comparison_result.comparison_items
    ]

    db_comparison = repo.create(
        user_id=current_user.id,
        period_start=comparison_result.period_start,
        period_end=comparison_result.period_end,
        platforms_analyzed=comparison_result.platforms_analyzed,
        twitter_analysis_id=request.twitter_analysis_id,
        instagram_analysis_id=request.instagram_analysis_id,
        twitter_performance=twitter_perf_dict,
        instagram_performance=instagram_perf_dict,
        comparison_items=comparison_items_dict,
        overall_winner=comparison_result.overall_winner,
        cross_platform_insights=comparison_result.cross_platform_insights,
        strategic_recommendations=comparison_result.strategic_recommendations,
        synergy_opportunities=comparison_result.synergy_opportunities,
    )

    logger.info(f"比較作成: user_id={current_user.id}, id={db_comparison.id}")

    return _db_to_response(db_comparison)


@router.get(
    "",
    response_model=PaginatedResponse,
)
async def list_comparisons(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> PaginatedResponse:
    """比較履歴一覧を取得"""
    _check_comparison_access(current_user)

    repo = CrossPlatformComparisonRepository(db)
    total = repo.count_by_user_id(current_user.id)
    offset = (page - 1) * per_page
    comparisons = repo.get_by_user_id(current_user.id, limit=per_page, offset=offset)

    items = [_db_to_summary(c) for c in comparisons]
    pages = (total + per_page - 1) // per_page if per_page > 0 else 0

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get(
    "/{comparison_id}",
    response_model=CrossPlatformComparisonResponse,
    responses={
        404: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
    },
)
async def get_comparison(
    comparison_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CrossPlatformComparisonResponse:
    """比較詳細を取得"""
    _check_comparison_access(current_user)

    repo = CrossPlatformComparisonRepository(db)
    comparison = repo.get_by_id(comparison_id)

    if not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="比較が見つかりません",
        )

    if comparison.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="アクセス権限がありません",
        )

    return _db_to_response(comparison)


@router.delete(
    "/{comparison_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
    },
)
async def delete_comparison(
    comparison_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """比較を削除"""
    _check_comparison_access(current_user)

    repo = CrossPlatformComparisonRepository(db)
    comparison = repo.get_by_id(comparison_id)

    if not comparison:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="比較が見つかりません",
        )

    if comparison.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="アクセス権限がありません",
        )

    repo.delete(comparison_id)
    logger.info(f"比較削除: user_id={current_user.id}, id={comparison_id}")
