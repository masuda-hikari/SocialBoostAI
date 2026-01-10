"""
リアルタイムダッシュボードAPIルーター
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from ..db import get_db
from ..db.models import Analysis, Report, User
from ..dependencies import CurrentUser
from ..websocket import get_notification_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ========================
# レスポンスモデル
# ========================


class PlatformMetrics(BaseModel):
    """プラットフォーム別メトリクス"""

    platform: str
    total_posts: int = 0
    total_likes: int = 0
    total_engagement: int = 0
    engagement_rate: float = 0.0
    last_analysis: Optional[str] = None


class TrendingHashtag(BaseModel):
    """トレンドハッシュタグ"""

    tag: str
    count: int
    engagement_rate: float = 0.0


class RealtimeDashboardResponse(BaseModel):
    """リアルタイムダッシュボードレスポンス"""

    user_id: str
    timestamp: str
    total_analyses: int = 0
    total_reports: int = 0
    platforms: list[PlatformMetrics] = Field(default_factory=list)
    trending_hashtags: list[TrendingHashtag] = Field(default_factory=list)
    recent_activity: list[dict[str, Any]] = Field(default_factory=list)
    best_posting_times: dict[str, list[int]] = Field(default_factory=dict)
    week_over_week: dict[str, float] = Field(default_factory=dict)


class LiveMetricsResponse(BaseModel):
    """ライブメトリクスレスポンス"""

    timestamp: str
    is_connected: bool
    metrics: dict[str, Any] = Field(default_factory=dict)


class ActivityItem(BaseModel):
    """アクティビティ項目"""

    type: str  # analysis, report
    id: str
    platform: str
    created_at: str
    summary: dict[str, Any] = Field(default_factory=dict)


# ========================
# エンドポイント
# ========================


@router.get("/dashboard", response_model=RealtimeDashboardResponse)
async def get_realtime_dashboard(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    days: int = Query(default=7, ge=1, le=90, description="集計日数"),
):
    """
    リアルタイムダッシュボードデータを取得

    最新の分析結果、メトリクス、トレンドを集約して返す。

    Args:
        current_user: 現在のユーザー
        db: データベースセッション
        days: 集計日数（デフォルト7日）

    Returns:
        ダッシュボードデータ
    """
    now = datetime.now(timezone.utc)
    period_start = now - timedelta(days=days)
    previous_period_start = period_start - timedelta(days=days)

    # 分析件数
    total_analyses = db.query(func.count(Analysis.id)).filter(
        Analysis.user_id == current_user.id
    ).scalar() or 0

    # レポート件数
    total_reports = db.query(func.count(Report.id)).filter(
        Report.user_id == current_user.id
    ).scalar() or 0

    # プラットフォーム別メトリクス
    platforms_data = db.query(
        Analysis.platform,
        func.sum(Analysis.total_posts).label("total_posts"),
        func.sum(Analysis.total_likes).label("total_likes"),
        func.sum(Analysis.total_retweets).label("total_engagement"),
        func.avg(Analysis.engagement_rate).label("avg_engagement"),
        func.max(Analysis.created_at).label("last_analysis"),
    ).filter(
        Analysis.user_id == current_user.id,
        Analysis.created_at >= period_start,
    ).group_by(Analysis.platform).all()

    platforms = [
        PlatformMetrics(
            platform=row.platform or "twitter",
            total_posts=int(row.total_posts or 0),
            total_likes=int(row.total_likes or 0),
            total_engagement=int(row.total_engagement or 0),
            engagement_rate=float(row.avg_engagement or 0.0),
            last_analysis=row.last_analysis.isoformat() if row.last_analysis else None,
        )
        for row in platforms_data
    ]

    # トレンドハッシュタグ（最新分析から抽出）
    trending_hashtags = []
    recent_analyses = db.query(Analysis).filter(
        Analysis.user_id == current_user.id,
        Analysis.created_at >= period_start,
    ).order_by(Analysis.created_at.desc()).limit(10).all()

    hashtag_counts: dict[str, int] = {}
    for analysis in recent_analyses:
        try:
            tags = json.loads(analysis.top_hashtags) if analysis.top_hashtags else []
            for tag in tags:
                if isinstance(tag, str):
                    hashtag_counts[tag] = hashtag_counts.get(tag, 0) + 1
        except (json.JSONDecodeError, TypeError):
            pass

    trending_hashtags = [
        TrendingHashtag(tag=tag, count=count)
        for tag, count in sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ]

    # 最近のアクティビティ
    recent_activity = []

    # 最新分析
    for analysis in recent_analyses[:5]:
        recent_activity.append({
            "type": "analysis",
            "id": analysis.id,
            "platform": analysis.platform or "twitter",
            "created_at": analysis.created_at.isoformat(),
            "summary": {
                "total_posts": analysis.total_posts,
                "engagement_rate": analysis.engagement_rate,
            },
        })

    # 最新レポート
    recent_reports = db.query(Report).filter(
        Report.user_id == current_user.id,
    ).order_by(Report.created_at.desc()).limit(5).all()

    for report in recent_reports:
        recent_activity.append({
            "type": "report",
            "id": report.id,
            "platform": report.platform or "twitter",
            "created_at": report.created_at.isoformat(),
            "summary": {
                "report_type": report.report_type,
            },
        })

    # 時系列でソート
    recent_activity.sort(key=lambda x: x["created_at"], reverse=True)
    recent_activity = recent_activity[:10]

    # 最適投稿時間（プラットフォーム別）
    best_posting_times: dict[str, list[int]] = {}
    for analysis in recent_analyses:
        platform = analysis.platform or "twitter"
        if analysis.best_hour is not None:
            if platform not in best_posting_times:
                best_posting_times[platform] = []
            best_posting_times[platform].append(analysis.best_hour)

    # 各プラットフォームの最頻出時間を計算
    for platform in best_posting_times:
        hours = best_posting_times[platform]
        if hours:
            # 頻度でソートして上位3つを返す
            hour_counts = {}
            for h in hours:
                hour_counts[h] = hour_counts.get(h, 0) + 1
            sorted_hours = sorted(hour_counts.keys(), key=lambda x: hour_counts[x], reverse=True)
            best_posting_times[platform] = sorted_hours[:3]

    # 週間比較（エンゲージメント率の変化）
    current_period = db.query(
        func.avg(Analysis.engagement_rate).label("avg_engagement")
    ).filter(
        Analysis.user_id == current_user.id,
        Analysis.created_at >= period_start,
    ).scalar() or 0.0

    previous_period = db.query(
        func.avg(Analysis.engagement_rate).label("avg_engagement")
    ).filter(
        Analysis.user_id == current_user.id,
        Analysis.created_at >= previous_period_start,
        Analysis.created_at < period_start,
    ).scalar() or 0.0

    week_over_week = {
        "current": float(current_period),
        "previous": float(previous_period),
        "change": float(current_period - previous_period) if previous_period else 0.0,
        "change_percent": (
            ((current_period - previous_period) / previous_period * 100)
            if previous_period > 0 else 0.0
        ),
    }

    return RealtimeDashboardResponse(
        user_id=current_user.id,
        timestamp=now.isoformat(),
        total_analyses=total_analyses,
        total_reports=total_reports,
        platforms=platforms,
        trending_hashtags=trending_hashtags,
        recent_activity=recent_activity,
        best_posting_times=best_posting_times,
        week_over_week=week_over_week,
    )


@router.get("/live-metrics", response_model=LiveMetricsResponse)
async def get_live_metrics(
    current_user: CurrentUser,
):
    """
    ライブメトリクスを取得

    WebSocket接続状態とリアルタイムメトリクスを返す。

    Args:
        current_user: 現在のユーザー

    Returns:
        ライブメトリクス
    """
    notification_service = get_notification_service()
    is_connected = notification_service.is_user_online(current_user.id)
    stats = notification_service.get_stats()

    return LiveMetricsResponse(
        timestamp=datetime.now(timezone.utc).isoformat(),
        is_connected=is_connected,
        metrics={
            "user_connections": stats.get("users", {}).get(current_user.id, 0),
            "total_connections": stats.get("total_connections", 0),
        },
    )


@router.get("/activity", response_model=list[ActivityItem])
async def get_recent_activity(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100, description="取得件数"),
    activity_type: Optional[str] = Query(default=None, description="フィルタ: analysis, report"),
):
    """
    最近のアクティビティを取得

    分析とレポートの履歴を時系列で返す。

    Args:
        current_user: 現在のユーザー
        db: データベースセッション
        limit: 取得件数
        activity_type: フィルタ（analysis または report）

    Returns:
        アクティビティリスト
    """
    activities = []

    # 分析履歴
    if activity_type is None or activity_type == "analysis":
        analyses = db.query(Analysis).filter(
            Analysis.user_id == current_user.id,
        ).order_by(Analysis.created_at.desc()).limit(limit).all()

        for analysis in analyses:
            activities.append(ActivityItem(
                type="analysis",
                id=analysis.id,
                platform=analysis.platform or "twitter",
                created_at=analysis.created_at.isoformat(),
                summary={
                    "total_posts": analysis.total_posts,
                    "engagement_rate": analysis.engagement_rate,
                    "best_hour": analysis.best_hour,
                },
            ))

    # レポート履歴
    if activity_type is None or activity_type == "report":
        reports = db.query(Report).filter(
            Report.user_id == current_user.id,
        ).order_by(Report.created_at.desc()).limit(limit).all()

        for report in reports:
            activities.append(ActivityItem(
                type="report",
                id=report.id,
                platform=report.platform or "twitter",
                created_at=report.created_at.isoformat(),
                summary={
                    "report_type": report.report_type,
                    "html_url": report.html_url,
                },
            ))

    # 時系列でソート
    activities.sort(key=lambda x: x.created_at, reverse=True)
    return activities[:limit]


@router.get("/platform-comparison")
async def get_platform_comparison(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    days: int = Query(default=30, ge=1, le=365, description="集計日数"),
):
    """
    プラットフォーム別比較データを取得

    各プラットフォームのパフォーマンスを比較可能な形式で返す。

    Args:
        current_user: 現在のユーザー
        db: データベースセッション
        days: 集計日数

    Returns:
        プラットフォーム比較データ
    """
    period_start = datetime.now(timezone.utc) - timedelta(days=days)

    # プラットフォーム別集計
    platforms_data = db.query(
        Analysis.platform,
        func.count(Analysis.id).label("analysis_count"),
        func.sum(Analysis.total_posts).label("total_posts"),
        func.sum(Analysis.total_likes).label("total_likes"),
        func.sum(Analysis.total_retweets).label("total_engagement"),
        func.avg(Analysis.engagement_rate).label("avg_engagement"),
        func.min(Analysis.engagement_rate).label("min_engagement"),
        func.max(Analysis.engagement_rate).label("max_engagement"),
    ).filter(
        Analysis.user_id == current_user.id,
        Analysis.created_at >= period_start,
    ).group_by(Analysis.platform).all()

    comparison = []
    for row in platforms_data:
        comparison.append({
            "platform": row.platform or "twitter",
            "analysis_count": int(row.analysis_count or 0),
            "total_posts": int(row.total_posts or 0),
            "total_likes": int(row.total_likes or 0),
            "total_engagement": int(row.total_engagement or 0),
            "engagement_rate": {
                "average": float(row.avg_engagement or 0.0),
                "min": float(row.min_engagement or 0.0),
                "max": float(row.max_engagement or 0.0),
            },
        })

    # 総合勝者を決定
    winner = None
    if comparison:
        winner = max(comparison, key=lambda x: x["engagement_rate"]["average"])["platform"]

    return {
        "period_days": days,
        "platforms": comparison,
        "winner": winner,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
