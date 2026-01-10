"""
LinkedIn分析エンドポイント
"""

import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..dependencies import CurrentUser, DbSession
from ..repositories import AnalysisRepository
from ..schemas import (
    ErrorResponse,
    LinkedInAnalysisDetail,
    LinkedInAnalysisRequest,
    LinkedInAnalysisResponse,
    LinkedInAnalysisSummary,
    LinkedInContentPattern,
    LinkedInDailyBreakdown,
    LinkedInMediaTypePerformance,
    PaginatedResponse,
)

router = APIRouter()

# プラン別制限
PLAN_LIMITS = {
    "free": {"period_days": 7, "api_calls_per_day": 100, "linkedin_enabled": False},
    "pro": {"period_days": 90, "api_calls_per_day": 1000, "linkedin_enabled": True},
    "business": {
        "period_days": 365,
        "api_calls_per_day": 10000,
        "linkedin_enabled": True,
    },
    "enterprise": {
        "period_days": 365,
        "api_calls_per_day": 100000,
        "linkedin_enabled": True,
    },
}


def _check_linkedin_access(role: str) -> None:
    """LinkedIn分析へのアクセス権をチェック"""
    limits = PLAN_LIMITS.get(role, PLAN_LIMITS["free"])
    if not limits.get("linkedin_enabled", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="LinkedIn分析はProプラン以上でご利用いただけます",
        )


@router.post(
    "/",
    response_model=LinkedInAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
async def create_linkedin_analysis(
    request: LinkedInAnalysisRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> LinkedInAnalysisResponse:
    """LinkedIn分析を作成"""
    _check_linkedin_access(current_user.role)

    limits = PLAN_LIMITS.get(current_user.role, PLAN_LIMITS["free"])

    # プランに応じた期間制限チェック
    if request.period_days > limits["period_days"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"現在のプラン（{current_user.role}）では{limits['period_days']}日までの分析が可能です",
        )

    now = datetime.now(timezone.utc)
    analysis_repo = AnalysisRepository(db)

    # 分析実行（本番では実際のLinkedIn API連携）
    # ここではモックデータを生成
    total_posts = 25
    total_articles = 3
    total_impressions = 45000
    total_likes = 1250
    total_comments = 180
    total_shares = 85
    total_clicks = 320
    engagement_rate = 4.08  # (likes + comments + shares + clicks) / impressions * 100
    click_through_rate = 0.71  # clicks / impressions * 100
    virality_rate = 0.19  # shares / impressions * 100
    avg_likes_per_post = total_likes / total_posts
    best_hour = 9
    best_days = ["火曜日", "水曜日", "木曜日"]
    top_hashtags = ["#linkedin", "#business", "#career"]

    # データベースに保存（既存のAnalysisモデルを流用）
    # total_retweets枠にtotal_impressionsを保存（LinkedIn固有）
    analysis = analysis_repo.create(
        user_id=current_user.id,
        platform="linkedin",
        period_start=now - timedelta(days=request.period_days),
        period_end=now,
        total_posts=total_posts + total_articles,
        total_likes=total_likes,
        total_retweets=total_impressions,  # LinkedIn: impressionsをretweets枠に
        engagement_rate=engagement_rate,
        best_hour=best_hour,
        top_hashtags=top_hashtags,
    )

    return LinkedInAnalysisResponse(
        id=analysis.id,
        user_id=analysis.user_id,
        platform="linkedin",
        period_start=analysis.period_start,
        period_end=analysis.period_end,
        summary=LinkedInAnalysisSummary(
            total_posts=total_posts,
            total_articles=total_articles,
            total_impressions=analysis.total_retweets,
            total_likes=analysis.total_likes,
            total_comments=total_comments,
            total_shares=total_shares,
            total_clicks=total_clicks,
            engagement_rate=analysis.engagement_rate,
            click_through_rate=click_through_rate,
            virality_rate=virality_rate,
            avg_likes_per_post=avg_likes_per_post,
            best_hour=analysis.best_hour,
            best_days=best_days,
            top_hashtags=json.loads(analysis.top_hashtags),
        ),
        created_at=analysis.created_at,
    )


@router.get(
    "/",
    response_model=PaginatedResponse,
)
async def list_linkedin_analyses(
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> PaginatedResponse:
    """LinkedIn分析一覧取得"""
    _check_linkedin_access(current_user.role)

    analysis_repo = AnalysisRepository(db)

    # LinkedInのみフィルタ
    total = analysis_repo.count_by_user_id_and_platform(current_user.id, "linkedin")

    offset = (page - 1) * per_page
    analyses = analysis_repo.get_by_user_id_and_platform(
        user_id=current_user.id,
        platform="linkedin",
        limit=per_page,
        offset=offset,
    )

    response_items = [
        LinkedInAnalysisResponse(
            id=a.id,
            user_id=a.user_id,
            platform="linkedin",
            period_start=a.period_start,
            period_end=a.period_end,
            summary=LinkedInAnalysisSummary(
                total_posts=a.total_posts,
                total_articles=0,  # 個別取得時に設定
                total_impressions=a.total_retweets,
                total_likes=a.total_likes,
                total_comments=0,  # 個別取得時に設定
                total_shares=0,  # 個別取得時に設定
                total_clicks=0,  # 個別取得時に設定
                engagement_rate=a.engagement_rate,
                click_through_rate=0.0,  # 個別取得時に計算
                virality_rate=0.0,  # 個別取得時に計算
                avg_likes_per_post=(
                    a.total_likes / a.total_posts if a.total_posts > 0 else 0
                ),
                best_hour=a.best_hour,
                best_days=[],  # 個別取得時に設定
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
    response_model=LinkedInAnalysisDetail,
    responses={404: {"model": ErrorResponse}},
)
async def get_linkedin_analysis(
    analysis_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> LinkedInAnalysisDetail:
    """LinkedIn分析詳細取得"""
    _check_linkedin_access(current_user.role)

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

    if analysis.platform != "linkedin":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LinkedIn分析が見つかりません",
        )

    # 詳細情報（本番では分析結果から取得）
    hourly_breakdown = [
        {"hour": h, "avg_likes": 50.0 + h * 2, "avg_shares": 5.0 + h * 0.5, "post_count": 1}
        for h in range(24)
    ]

    # 曜日別パフォーマンス（B2B特有）
    daily_breakdown = [
        LinkedInDailyBreakdown(
            weekday=0,
            weekday_name="月曜日",
            avg_likes=48.5,
            avg_shares=3.2,
            avg_comments=7.1,
            avg_clicks=12.5,
            avg_impressions=1800.0,
            post_count=4,
            total_engagement=71.3,
        ),
        LinkedInDailyBreakdown(
            weekday=1,
            weekday_name="火曜日",
            avg_likes=62.3,
            avg_shares=4.5,
            avg_comments=9.2,
            avg_clicks=15.8,
            avg_impressions=2200.0,
            post_count=5,
            total_engagement=91.8,
        ),
        LinkedInDailyBreakdown(
            weekday=2,
            weekday_name="水曜日",
            avg_likes=58.7,
            avg_shares=4.1,
            avg_comments=8.5,
            avg_clicks=14.2,
            avg_impressions=2100.0,
            post_count=5,
            total_engagement=85.5,
        ),
        LinkedInDailyBreakdown(
            weekday=3,
            weekday_name="木曜日",
            avg_likes=55.2,
            avg_shares=3.8,
            avg_comments=8.0,
            avg_clicks=13.5,
            avg_impressions=2000.0,
            post_count=4,
            total_engagement=80.5,
        ),
        LinkedInDailyBreakdown(
            weekday=4,
            weekday_name="金曜日",
            avg_likes=45.8,
            avg_shares=2.9,
            avg_comments=6.5,
            avg_clicks=10.2,
            avg_impressions=1650.0,
            post_count=3,
            total_engagement=65.4,
        ),
        LinkedInDailyBreakdown(
            weekday=5,
            weekday_name="土曜日",
            avg_likes=22.5,
            avg_shares=1.2,
            avg_comments=2.8,
            avg_clicks=4.5,
            avg_impressions=800.0,
            post_count=2,
            total_engagement=31.0,
        ),
        LinkedInDailyBreakdown(
            weekday=6,
            weekday_name="日曜日",
            avg_likes=18.3,
            avg_shares=0.9,
            avg_comments=2.1,
            avg_clicks=3.2,
            avg_impressions=650.0,
            post_count=2,
            total_engagement=24.5,
        ),
    ]

    content_patterns = [
        LinkedInContentPattern(
            pattern_type="thought_leadership",
            count=8,
            avg_engagement=95.5,
        ),
        LinkedInContentPattern(
            pattern_type="tips",
            count=6,
            avg_engagement=82.3,
        ),
        LinkedInContentPattern(
            pattern_type="achievement",
            count=4,
            avg_engagement=75.8,
        ),
        LinkedInContentPattern(
            pattern_type="question",
            count=3,
            avg_engagement=68.2,
        ),
    ]

    media_type_performance = [
        LinkedInMediaTypePerformance(
            media_type="IMAGE",
            avg_engagement=88.5,
        ),
        LinkedInMediaTypePerformance(
            media_type="DOCUMENT",
            avg_engagement=95.2,
        ),
        LinkedInMediaTypePerformance(
            media_type="NONE",
            avg_engagement=62.3,
        ),
        LinkedInMediaTypePerformance(
            media_type="VIDEO",
            avg_engagement=78.5,
        ),
        LinkedInMediaTypePerformance(
            media_type="ARTICLE",
            avg_engagement=72.1,
        ),
    ]

    recommendations = {
        "best_hours": [8, 9, 10],
        "best_days": ["火曜日", "水曜日", "木曜日"],
        "suggested_hashtags": json.loads(analysis.top_hashtags),
        "best_media_type": "DOCUMENT",
        "best_post_length": "medium",
        "reasoning": (
            "LinkedIn分析の結果、9時の投稿が最もエンゲージメントが高い傾向にあります。"
            "B2Bプラットフォームとして、火曜日〜木曜日の投稿が効果的です。"
            "ドキュメント（PDF等）を添付した投稿が最も高いエンゲージメントを獲得しています。"
        ),
    }

    return LinkedInAnalysisDetail(
        id=analysis.id,
        user_id=analysis.user_id,
        platform="linkedin",
        period_start=analysis.period_start,
        period_end=analysis.period_end,
        summary=LinkedInAnalysisSummary(
            total_posts=25,
            total_articles=3,
            total_impressions=analysis.total_retweets,
            total_likes=analysis.total_likes,
            total_comments=180,
            total_shares=85,
            total_clicks=320,
            engagement_rate=analysis.engagement_rate,
            click_through_rate=0.71,
            virality_rate=0.19,
            avg_likes_per_post=(
                analysis.total_likes / analysis.total_posts
                if analysis.total_posts > 0
                else 0
            ),
            best_hour=analysis.best_hour,
            best_days=["火曜日", "水曜日", "木曜日"],
            top_hashtags=json.loads(analysis.top_hashtags),
        ),
        hourly_breakdown=hourly_breakdown,
        daily_breakdown=daily_breakdown,
        content_patterns=content_patterns,
        recommendations=recommendations,
        avg_post_length=380.5,  # 平均文字数
        media_type_performance=media_type_performance,
        created_at=analysis.created_at,
    )


@router.delete(
    "/{analysis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
)
async def delete_linkedin_analysis(
    analysis_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """LinkedIn分析削除"""
    _check_linkedin_access(current_user.role)

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

    if analysis.platform != "linkedin":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LinkedIn分析が見つかりません",
        )

    analysis_repo.delete(analysis)
