"""
エンゲージメント分析モジュール
"""

import logging
from collections import defaultdict
from datetime import datetime
from typing import Optional

from .models import (
    AnalysisResult,
    EngagementMetrics,
    HourlyEngagement,
    PostRecommendation,
    Tweet,
)

logger = logging.getLogger(__name__)


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
    total_engagement = total_likes + total_retweets + total_replies

    post_count = len(tweets)

    # インプレッションがあればエンゲージメント率を計算
    total_impressions = sum(t.impressions or 0 for t in tweets)
    engagement_rate = (
        (total_engagement / total_impressions * 100) if total_impressions > 0 else 0.0
    )

    return EngagementMetrics(
        total_likes=total_likes,
        total_retweets=total_retweets,
        total_replies=total_replies,
        engagement_rate=round(engagement_rate, 2),
        avg_likes_per_post=round(total_likes / post_count, 2),
        avg_retweets_per_post=round(total_retweets / post_count, 2),
    )


def analyze_hourly_engagement(tweets: list[Tweet]) -> list[HourlyEngagement]:
    """時間帯別エンゲージメントを分析

    Args:
        tweets: ツイートリスト

    Returns:
        list[HourlyEngagement]: 時間帯別エンゲージメントリスト（0-23時）
    """
    hourly_data: dict[int, dict[str, list[int]]] = defaultdict(
        lambda: {"likes": [], "retweets": []}
    )

    for tweet in tweets:
        hour = tweet.created_at.hour
        hourly_data[hour]["likes"].append(tweet.likes)
        hourly_data[hour]["retweets"].append(tweet.retweets)

    results: list[HourlyEngagement] = []
    for hour in range(24):
        data = hourly_data[hour]
        likes = data["likes"]
        retweets = data["retweets"]

        if likes:
            avg_likes = sum(likes) / len(likes)
            avg_retweets = sum(retweets) / len(retweets)
            total_engagement = avg_likes + avg_retweets
        else:
            avg_likes = 0.0
            avg_retweets = 0.0
            total_engagement = 0.0

        results.append(
            HourlyEngagement(
                hour=hour,
                avg_likes=round(avg_likes, 2),
                avg_retweets=round(avg_retweets, 2),
                post_count=len(likes),
                total_engagement=round(total_engagement, 2),
            )
        )

    return results


def find_best_posting_hours(
    hourly_engagement: list[HourlyEngagement],
    top_n: int = 3,
    min_posts: int = 2,
) -> list[int]:
    """最適な投稿時間を特定

    Args:
        hourly_engagement: 時間帯別エンゲージメントリスト
        top_n: 上位何件を返すか
        min_posts: 最低投稿数（信頼性のため）

    Returns:
        list[int]: 最適な投稿時間（時）のリスト
    """
    # 十分な投稿数がある時間帯のみを考慮
    valid_hours = [h for h in hourly_engagement if h.post_count >= min_posts]

    if not valid_hours:
        # データが不十分な場合は全時間帯を考慮
        valid_hours = hourly_engagement

    # エンゲージメントでソート
    sorted_hours = sorted(
        valid_hours, key=lambda h: h.total_engagement, reverse=True
    )

    return [h.hour for h in sorted_hours[:top_n]]


def get_top_performing_posts(
    tweets: list[Tweet],
    top_n: int = 5,
) -> list[Tweet]:
    """最もエンゲージメントの高いツイートを取得

    Args:
        tweets: ツイートリスト
        top_n: 上位何件を返すか

    Returns:
        list[Tweet]: 上位ツイートリスト
    """
    sorted_tweets = sorted(
        tweets,
        key=lambda t: t.likes + t.retweets + t.replies,
        reverse=True,
    )
    return sorted_tweets[:top_n]


def analyze_tweets(
    tweets: list[Tweet],
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
) -> AnalysisResult:
    """ツイートを総合分析

    Args:
        tweets: ツイートリスト
        period_start: 分析期間開始（指定なしの場合は最古のツイートから）
        period_end: 分析期間終了（指定なしの場合は最新のツイートまで）

    Returns:
        AnalysisResult: 分析結果
    """
    if not tweets:
        now = datetime.utcnow()
        return AnalysisResult(
            period_start=period_start or now,
            period_end=period_end or now,
            total_posts=0,
            metrics=EngagementMetrics(),
            hourly_breakdown=[],
            top_performing_posts=[],
        )

    # 期間を決定
    tweet_dates = [t.created_at for t in tweets]
    actual_start = period_start or min(tweet_dates)
    actual_end = period_end or max(tweet_dates)

    # 各分析を実行
    metrics = calculate_engagement_metrics(tweets)
    hourly_breakdown = analyze_hourly_engagement(tweets)
    top_posts = get_top_performing_posts(tweets)
    best_hours = find_best_posting_hours(hourly_breakdown)

    # 基本的なレコメンデーション生成
    recommendations = PostRecommendation(
        best_hours=best_hours,
        suggested_hashtags=[],  # AI機能で後で実装
        content_ideas=[],  # AI機能で後で実装
        reasoning=_generate_recommendation_reasoning(metrics, best_hours),
    )

    logger.info(f"{len(tweets)}件のツイートを分析しました")

    return AnalysisResult(
        period_start=actual_start,
        period_end=actual_end,
        total_posts=len(tweets),
        metrics=metrics,
        hourly_breakdown=hourly_breakdown,
        top_performing_posts=top_posts,
        recommendations=recommendations,
    )


def _generate_recommendation_reasoning(
    metrics: EngagementMetrics,
    best_hours: list[int],
) -> str:
    """レコメンデーションの理由を生成

    Args:
        metrics: エンゲージメント指標
        best_hours: 最適な投稿時間

    Returns:
        str: 理由の説明文
    """
    hour_strs = [f"{h}時" for h in best_hours]
    hours_text = "、".join(hour_strs)

    return (
        f"分析の結果、{hours_text}の投稿が最もエンゲージメントが高い傾向にあります。"
        f"平均いいね数は{metrics.avg_likes_per_post}、"
        f"平均リツイート数は{metrics.avg_retweets_per_post}です。"
    )
