"""
週次/月次サマリー生成モジュール

v0.4: レポート機能拡張
"""

import logging
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Optional

from .models import (
    EngagementMetrics,
    MonthlySummary,
    PeriodComparison,
    Tweet,
    WeeklySummary,
)

logger = logging.getLogger(__name__)

# 曜日名（日本語）
WEEKDAY_NAMES = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]


def calculate_engagement_metrics(tweets: list[Tweet]) -> EngagementMetrics:
    """ツイートリストからエンゲージメント指標を計算

    Args:
        tweets: ツイートリスト

    Returns:
        EngagementMetrics: エンゲージメント指標
    """
    if not tweets:
        return EngagementMetrics()

    total_likes = sum(t.likes for t in tweets)
    total_retweets = sum(t.retweets for t in tweets)
    total_replies = sum(t.replies for t in tweets)
    total_impressions = sum(t.impressions or 0 for t in tweets)
    total_engagement = total_likes + total_retweets + total_replies
    count = len(tweets)

    engagement_rate = 0.0
    if total_impressions > 0:
        engagement_rate = (total_engagement / total_impressions) * 100

    return EngagementMetrics(
        total_likes=total_likes,
        total_retweets=total_retweets,
        total_replies=total_replies,
        engagement_rate=round(engagement_rate, 2),
        avg_likes_per_post=round(total_likes / count, 2),
        avg_retweets_per_post=round(total_retweets / count, 2),
    )


def calculate_comparison(
    current: EngagementMetrics,
    previous: EngagementMetrics,
) -> list[PeriodComparison]:
    """2つの期間のメトリクスを比較

    Args:
        current: 現在期間のメトリクス
        previous: 前期間のメトリクス

    Returns:
        list[PeriodComparison]: 比較結果リスト
    """
    comparisons = []

    metrics_to_compare = [
        ("総いいね数", current.total_likes, previous.total_likes),
        ("総リツイート数", current.total_retweets, previous.total_retweets),
        ("平均いいね/投稿", current.avg_likes_per_post, previous.avg_likes_per_post),
        (
            "平均リツイート/投稿",
            current.avg_retweets_per_post,
            previous.avg_retweets_per_post,
        ),
        ("エンゲージメント率", current.engagement_rate, previous.engagement_rate),
    ]

    for name, curr_val, prev_val in metrics_to_compare:
        if prev_val == 0:
            change_percent = 100.0 if curr_val > 0 else 0.0
        else:
            change_percent = ((curr_val - prev_val) / prev_val) * 100

        if change_percent > 5:
            trend = "up"
        elif change_percent < -5:
            trend = "down"
        else:
            trend = "stable"

        comparisons.append(
            PeriodComparison(
                metric_name=name,
                current_value=float(curr_val),
                previous_value=float(prev_val),
                change_percent=round(change_percent, 2),
                trend=trend,
            )
        )

    return comparisons


def generate_weekly_insights(
    summary: WeeklySummary,
    comparison: Optional[list[PeriodComparison]],
) -> list[str]:
    """週次インサイトを生成

    Args:
        summary: 週次サマリー
        comparison: 前週との比較データ

    Returns:
        list[str]: インサイトリスト
    """
    insights = []

    # 投稿数に基づくインサイト
    if summary.total_posts == 0:
        insights.append(
            "今週は投稿がありませんでした。投稿頻度を上げることを検討してください。"
        )
    elif summary.total_posts < 3:
        insights.append(
            f"今週の投稿数は{summary.total_posts}件でした。週に5〜7件の投稿を目指しましょう。"
        )
    elif summary.total_posts >= 7:
        insights.append(
            f"今週は{summary.total_posts}件の投稿を達成しました。素晴らしい継続性です！"
        )

    # ベストパフォーマンス日
    insights.append(
        f"{summary.best_performing_day}が最もエンゲージメントの高い日でした。"
    )

    # 比較に基づくインサイト
    if comparison:
        for comp in comparison:
            if comp.metric_name == "総いいね数" and comp.trend == "up":
                insights.append(
                    f"いいね数が前週比{comp.change_percent:.1f}%増加しました！"
                )
            elif comp.metric_name == "総いいね数" and comp.trend == "down":
                insights.append(
                    f"いいね数が前週比{abs(comp.change_percent):.1f}%減少しました。コンテンツ戦略の見直しを検討してください。"
                )

    # トップ投稿に基づくインサイト
    if summary.top_post:
        total_eng = (
            summary.top_post.likes
            + summary.top_post.retweets
            + summary.top_post.replies
        )
        insights.append(
            f"今週のトップ投稿は{total_eng}のエンゲージメントを獲得しました。"
        )

    return insights


def generate_monthly_insights(
    summary: MonthlySummary,
    comparison: Optional[list[PeriodComparison]],
) -> list[str]:
    """月次インサイトを生成

    Args:
        summary: 月次サマリー
        comparison: 前月との比較データ

    Returns:
        list[str]: インサイトリスト
    """
    insights = []

    # 投稿数に基づくインサイト
    if summary.total_posts == 0:
        insights.append("今月は投稿がありませんでした。")
    else:
        avg_per_week = summary.total_posts / max(len(summary.weekly_summaries), 1)
        insights.append(
            f"今月の投稿数は{summary.total_posts}件（週平均{avg_per_week:.1f}件）でした。"
        )

    # ベスト週
    if summary.best_performing_week:
        insights.append(
            f"第{summary.best_performing_week}週が最もパフォーマンスが良好でした。"
        )

    # 成長率
    if summary.growth_rate is not None:
        if summary.growth_rate > 0:
            insights.append(f"前月比{summary.growth_rate:.1f}%の成長を達成しました！")
        elif summary.growth_rate < 0:
            insights.append(
                f"前月比{abs(summary.growth_rate):.1f}%の減少がありました。改善策を検討しましょう。"
            )
        else:
            insights.append("前月と同水準のパフォーマンスを維持しています。")

    # 比較に基づくインサイト
    if comparison:
        up_metrics = [c for c in comparison if c.trend == "up"]
        down_metrics = [c for c in comparison if c.trend == "down"]

        if up_metrics:
            names = "、".join(c.metric_name for c in up_metrics[:2])
            insights.append(f"{names}が向上しています。")

        if down_metrics:
            names = "、".join(c.metric_name for c in down_metrics[:2])
            insights.append(f"{names}に改善の余地があります。")

    return insights


def get_week_range(date: datetime) -> tuple[datetime, datetime]:
    """指定日が属する週の開始日と終了日を取得（月曜始まり）

    Args:
        date: 対象日

    Returns:
        tuple[datetime, datetime]: (週開始日, 週終了日)
    """
    # 月曜日を週の開始とする
    start_of_week = date - timedelta(days=date.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
    return start_of_week, end_of_week


def get_month_range(year: int, month: int) -> tuple[datetime, datetime]:
    """指定月の開始日と終了日を取得

    Args:
        year: 年
        month: 月

    Returns:
        tuple[datetime, datetime]: (月開始日, 月終了日)
    """
    start_of_month = datetime(year, month, 1)
    if month == 12:
        end_of_month = datetime(year + 1, 1, 1) - timedelta(seconds=1)
    else:
        end_of_month = datetime(year, month + 1, 1) - timedelta(seconds=1)
    return start_of_month, end_of_month


def generate_weekly_summary(
    tweets: list[Tweet],
    target_date: Optional[datetime] = None,
    previous_week_tweets: Optional[list[Tweet]] = None,
) -> WeeklySummary:
    """週次サマリーを生成

    Args:
        tweets: 対象週のツイートリスト
        target_date: 対象日（指定なしの場合は現在日時）
        previous_week_tweets: 前週のツイートリスト（比較用、オプション）

    Returns:
        WeeklySummary: 週次サマリー
    """
    if target_date is None:
        target_date = datetime.now(UTC).replace(tzinfo=None)

    week_start, week_end = get_week_range(target_date)
    week_number = target_date.isocalendar()[1]
    year = target_date.year

    # 対象週のツイートをフィルタ
    week_tweets = [
        t for t in tweets if week_start <= t.created_at.replace(tzinfo=None) <= week_end
    ]

    # メトリクス計算
    metrics = calculate_engagement_metrics(week_tweets)

    # 曜日別エンゲージメント計算
    daily_engagement: dict[int, float] = defaultdict(float)
    for t in week_tweets:
        weekday = t.created_at.weekday()
        daily_engagement[weekday] += t.likes + t.retweets + t.replies

    # ベストパフォーマンス日を特定
    if daily_engagement:
        best_day_num = max(daily_engagement, key=lambda k: daily_engagement[k])
        best_performing_day = WEEKDAY_NAMES[best_day_num]
    else:
        best_performing_day = "データなし"

    # トップ投稿を特定
    top_post = None
    if week_tweets:
        top_post = max(week_tweets, key=lambda t: t.likes + t.retweets + t.replies)

    # 前週との比較
    comparison = None
    if previous_week_tweets:
        prev_metrics = calculate_engagement_metrics(previous_week_tweets)
        comparison = calculate_comparison(metrics, prev_metrics)

    summary = WeeklySummary(
        week_number=week_number,
        year=year,
        period_start=week_start,
        period_end=week_end,
        total_posts=len(week_tweets),
        metrics=metrics,
        best_performing_day=best_performing_day,
        top_post=top_post,
        comparison=comparison,
    )

    # インサイト生成
    summary.insights = generate_weekly_insights(summary, comparison)

    return summary


def generate_monthly_summary(
    tweets: list[Tweet],
    year: int,
    month: int,
    previous_month_tweets: Optional[list[Tweet]] = None,
) -> MonthlySummary:
    """月次サマリーを生成

    Args:
        tweets: 対象月のツイートリスト
        year: 年
        month: 月
        previous_month_tweets: 前月のツイートリスト（比較用、オプション）

    Returns:
        MonthlySummary: 月次サマリー
    """
    month_start, month_end = get_month_range(year, month)

    # 対象月のツイートをフィルタ
    month_tweets = [
        t
        for t in tweets
        if month_start <= t.created_at.replace(tzinfo=None) <= month_end
    ]

    # メトリクス計算
    metrics = calculate_engagement_metrics(month_tweets)

    # 週次サマリー生成
    weekly_summaries: list[WeeklySummary] = []
    current_date = month_start
    while current_date <= month_end:
        week_start, week_end = get_week_range(current_date)
        # 週の開始が月内または週の終了が月内の場合に処理
        if week_start <= month_end and week_end >= month_start:
            weekly_summary = generate_weekly_summary(tweets, current_date)
            # 重複を避ける
            if not any(
                ws.week_number == weekly_summary.week_number
                and ws.year == weekly_summary.year
                for ws in weekly_summaries
            ):
                weekly_summaries.append(weekly_summary)
        current_date += timedelta(days=7)

    # ベスト週を特定
    best_performing_week = None
    if weekly_summaries:
        best_week = max(
            weekly_summaries,
            key=lambda w: w.metrics.total_likes + w.metrics.total_retweets,
        )
        best_performing_week = best_week.week_number

    # トップ投稿（上位5件）
    top_posts = sorted(
        month_tweets,
        key=lambda t: t.likes + t.retweets + t.replies,
        reverse=True,
    )[:5]

    # 前月との比較
    comparison = None
    growth_rate = None
    if previous_month_tweets:
        prev_metrics = calculate_engagement_metrics(previous_month_tweets)
        comparison = calculate_comparison(metrics, prev_metrics)

        # 成長率計算（総エンゲージメントベース）
        prev_total = (
            prev_metrics.total_likes
            + prev_metrics.total_retweets
            + prev_metrics.total_replies
        )
        curr_total = (
            metrics.total_likes + metrics.total_retweets + metrics.total_replies
        )
        if prev_total > 0:
            growth_rate = ((curr_total - prev_total) / prev_total) * 100
        elif curr_total > 0:
            growth_rate = 100.0
        else:
            growth_rate = 0.0
        growth_rate = round(growth_rate, 2)

    summary = MonthlySummary(
        month=month,
        year=year,
        period_start=month_start,
        period_end=month_end,
        total_posts=len(month_tweets),
        metrics=metrics,
        weekly_summaries=weekly_summaries,
        best_performing_week=best_performing_week,
        top_posts=top_posts,
        comparison=comparison,
        growth_rate=growth_rate,
    )

    # インサイト生成
    summary.insights = generate_monthly_insights(summary, comparison)

    return summary


def generate_period_report(
    tweets: list[Tweet],
    period_type: str,
    target_date: Optional[datetime] = None,
    include_comparison: bool = True,
) -> WeeklySummary | MonthlySummary:
    """指定期間のレポートを生成

    Args:
        tweets: 全ツイートリスト
        period_type: "weekly" または "monthly"
        target_date: 対象日（指定なしの場合は現在日時）
        include_comparison: 前期間との比較を含めるか

    Returns:
        WeeklySummary | MonthlySummary: サマリー

    Raises:
        ValueError: 不正なperiod_typeが指定された場合
    """
    if target_date is None:
        target_date = datetime.now(UTC).replace(tzinfo=None)

    if period_type == "weekly":
        previous_tweets = None
        if include_comparison:
            prev_start, prev_end = get_week_range(target_date - timedelta(days=7))
            previous_tweets = [
                t
                for t in tweets
                if prev_start <= t.created_at.replace(tzinfo=None) <= prev_end
            ]
        return generate_weekly_summary(tweets, target_date, previous_tweets)

    elif period_type == "monthly":
        previous_tweets = None
        if include_comparison:
            # 前月の範囲を計算
            if target_date.month == 1:
                prev_year = target_date.year - 1
                prev_month = 12
            else:
                prev_year = target_date.year
                prev_month = target_date.month - 1
            prev_start, prev_end = get_month_range(prev_year, prev_month)
            previous_tweets = [
                t
                for t in tweets
                if prev_start <= t.created_at.replace(tzinfo=None) <= prev_end
            ]
        return generate_monthly_summary(
            tweets, target_date.year, target_date.month, previous_tweets
        )

    else:
        raise ValueError(
            f"不正なperiod_type: {period_type}（'weekly'または'monthly'を指定）"
        )
