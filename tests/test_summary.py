# -*- coding: utf-8 -*-
"""
週次/月次サマリー機能のテスト

v0.4: レポート機能拡張
"""

from datetime import datetime, timedelta

import pytest

from src.models import (
    EngagementMetrics,
    MonthlySummary,
    PeriodComparison,
    Tweet,
    WeeklySummary,
)
from src.summary import (
    calculate_comparison,
    calculate_engagement_metrics,
    generate_monthly_insights,
    generate_monthly_summary,
    generate_period_report,
    generate_weekly_insights,
    generate_weekly_summary,
    get_month_range,
    get_week_range,
)


# テストデータ生成用ヘルパー
def create_test_tweet(
    tweet_id: str,
    text: str,
    created_at: datetime,
    likes: int = 10,
    retweets: int = 5,
    replies: int = 2,
) -> Tweet:
    """テスト用ツイートを生成"""
    return Tweet(
        id=tweet_id,
        text=text,
        created_at=created_at,
        likes=likes,
        retweets=retweets,
        replies=replies,
    )


class TestCalculateEngagementMetrics:
    """calculate_engagement_metricsのテスト"""

    def test_empty_tweets(self):
        """空のツイートリストの場合"""
        result = calculate_engagement_metrics([])
        assert result.total_likes == 0
        assert result.total_retweets == 0
        assert result.avg_likes_per_post == 0.0

    def test_single_tweet(self):
        """1件のツイートの場合"""
        tweets = [
            create_test_tweet(
                "1", "テスト", datetime(2026, 1, 1), likes=100, retweets=50
            )
        ]
        result = calculate_engagement_metrics(tweets)
        assert result.total_likes == 100
        assert result.total_retweets == 50
        assert result.avg_likes_per_post == 100.0

    def test_multiple_tweets(self):
        """複数ツイートの場合"""
        tweets = [
            create_test_tweet(
                "1", "テスト1", datetime(2026, 1, 1), likes=100, retweets=50
            ),
            create_test_tweet(
                "2", "テスト2", datetime(2026, 1, 2), likes=200, retweets=100
            ),
        ]
        result = calculate_engagement_metrics(tweets)
        assert result.total_likes == 300
        assert result.total_retweets == 150
        assert result.avg_likes_per_post == 150.0


class TestCalculateComparison:
    """calculate_comparisonのテスト"""

    def test_comparison_increase(self):
        """増加の場合"""
        current = EngagementMetrics(total_likes=200, total_retweets=100)
        previous = EngagementMetrics(total_likes=100, total_retweets=50)
        result = calculate_comparison(current, previous)

        likes_comp = next(c for c in result if c.metric_name == "総いいね数")
        assert likes_comp.change_percent == 100.0
        assert likes_comp.trend == "up"

    def test_comparison_decrease(self):
        """減少の場合"""
        current = EngagementMetrics(total_likes=50, total_retweets=25)
        previous = EngagementMetrics(total_likes=100, total_retweets=50)
        result = calculate_comparison(current, previous)

        likes_comp = next(c for c in result if c.metric_name == "総いいね数")
        assert likes_comp.change_percent == -50.0
        assert likes_comp.trend == "down"

    def test_comparison_stable(self):
        """安定の場合"""
        current = EngagementMetrics(total_likes=100, total_retweets=50)
        previous = EngagementMetrics(total_likes=100, total_retweets=50)
        result = calculate_comparison(current, previous)

        likes_comp = next(c for c in result if c.metric_name == "総いいね数")
        assert likes_comp.change_percent == 0.0
        assert likes_comp.trend == "stable"

    def test_comparison_from_zero(self):
        """前期間がゼロの場合"""
        current = EngagementMetrics(total_likes=100, total_retweets=50)
        previous = EngagementMetrics(total_likes=0, total_retweets=0)
        result = calculate_comparison(current, previous)

        likes_comp = next(c for c in result if c.metric_name == "総いいね数")
        assert likes_comp.change_percent == 100.0
        assert likes_comp.trend == "up"


class TestGetWeekRange:
    """get_week_rangeのテスト"""

    def test_monday_start(self):
        """月曜日が週の開始"""
        # 2026-01-05は月曜日
        test_date = datetime(2026, 1, 5, 12, 0, 0)
        start, end = get_week_range(test_date)
        assert start.weekday() == 0  # 月曜日
        assert end.weekday() == 6  # 日曜日

    def test_midweek(self):
        """週の中日の場合"""
        # 2026-01-07は水曜日
        test_date = datetime(2026, 1, 7, 12, 0, 0)
        start, end = get_week_range(test_date)
        assert start == datetime(2026, 1, 5, 0, 0, 0)
        assert end.date() == datetime(2026, 1, 11).date()


class TestGetMonthRange:
    """get_month_rangeのテスト"""

    def test_january(self):
        """1月の場合"""
        start, end = get_month_range(2026, 1)
        assert start == datetime(2026, 1, 1)
        assert end.month == 1
        assert end.day == 31

    def test_february_non_leap(self):
        """2月（非閏年）の場合"""
        start, end = get_month_range(2026, 2)
        assert start == datetime(2026, 2, 1)
        assert end.day == 28

    def test_december(self):
        """12月の場合"""
        start, end = get_month_range(2026, 12)
        assert start == datetime(2026, 12, 1)
        assert end.day == 31


class TestGenerateWeeklySummary:
    """generate_weekly_summaryのテスト"""

    def test_basic_weekly_summary(self):
        """基本的な週次サマリー生成"""
        # 2026-01-05週のツイート
        tweets = [
            create_test_tweet(
                "1", "月曜ツイート", datetime(2026, 1, 5, 10, 0), likes=100
            ),
            create_test_tweet(
                "2", "火曜ツイート", datetime(2026, 1, 6, 10, 0), likes=50
            ),
            create_test_tweet(
                "3", "水曜ツイート", datetime(2026, 1, 7, 10, 0), likes=200
            ),
        ]

        result = generate_weekly_summary(tweets, datetime(2026, 1, 7))

        assert result.total_posts == 3
        assert result.metrics.total_likes == 350
        assert result.best_performing_day == "水曜日"
        assert result.top_post is not None
        assert result.top_post.likes == 200

    def test_empty_tweets(self):
        """ツイートなしの場合"""
        result = generate_weekly_summary([], datetime(2026, 1, 7))

        assert result.total_posts == 0
        assert result.metrics.total_likes == 0
        assert result.best_performing_day == "データなし"

    def test_with_comparison(self):
        """前週比較ありの場合"""
        current_week = [
            create_test_tweet("1", "今週", datetime(2026, 1, 5, 10, 0), likes=200),
        ]
        previous_week = [
            create_test_tweet("2", "先週", datetime(2025, 12, 29, 10, 0), likes=100),
        ]

        result = generate_weekly_summary(
            current_week, datetime(2026, 1, 5), previous_week
        )

        assert result.comparison is not None
        assert len(result.comparison) > 0

    def test_insights_generated(self):
        """インサイトが生成されること"""
        tweets = [
            create_test_tweet("1", "テスト", datetime(2026, 1, 5, 10, 0), likes=100),
        ]

        result = generate_weekly_summary(tweets, datetime(2026, 1, 7))

        assert len(result.insights) > 0


class TestGenerateMonthlySummary:
    """generate_monthly_summaryのテスト"""

    def test_basic_monthly_summary(self):
        """基本的な月次サマリー生成"""
        tweets = [
            create_test_tweet("1", "1月1日", datetime(2026, 1, 1, 10, 0), likes=100),
            create_test_tweet("2", "1月15日", datetime(2026, 1, 15, 10, 0), likes=200),
            create_test_tweet("3", "1月30日", datetime(2026, 1, 30, 10, 0), likes=150),
        ]

        result = generate_monthly_summary(tweets, 2026, 1)

        assert result.month == 1
        assert result.year == 2026
        assert result.total_posts == 3
        assert result.metrics.total_likes == 450
        assert len(result.top_posts) <= 5

    def test_weekly_summaries_included(self):
        """週次サマリーが含まれること"""
        tweets = [
            create_test_tweet("1", "1月1日", datetime(2026, 1, 1, 10, 0), likes=100),
            create_test_tweet("2", "1月15日", datetime(2026, 1, 15, 10, 0), likes=200),
        ]

        result = generate_monthly_summary(tweets, 2026, 1)

        assert len(result.weekly_summaries) > 0

    def test_with_previous_month_comparison(self):
        """前月比較ありの場合"""
        # 同じエンゲージメント構成でlikesのみ2倍
        current_month = [
            create_test_tweet(
                "1",
                "1月",
                datetime(2026, 1, 15, 10, 0),
                likes=200,
                retweets=10,
                replies=4,
            ),
        ]
        previous_month = [
            create_test_tweet(
                "2",
                "12月",
                datetime(2025, 12, 15, 10, 0),
                likes=100,
                retweets=5,
                replies=2,
            ),
        ]

        result = generate_monthly_summary(current_month, 2026, 1, previous_month)

        assert result.comparison is not None
        assert result.growth_rate is not None
        # 総エンゲージメント: 現在214 (200+10+4), 前月107 (100+5+2) -> 100%増
        assert result.growth_rate == 100.0

    def test_empty_month(self):
        """投稿なしの月の場合"""
        result = generate_monthly_summary([], 2026, 1)

        assert result.total_posts == 0
        assert result.metrics.total_likes == 0


class TestGeneratePeriodReport:
    """generate_period_reportのテスト"""

    def test_weekly_report(self):
        """週次レポート生成"""
        tweets = [
            create_test_tweet("1", "テスト", datetime(2026, 1, 5, 10, 0), likes=100),
        ]

        result = generate_period_report(tweets, "weekly", datetime(2026, 1, 7))

        assert isinstance(result, WeeklySummary)

    def test_monthly_report(self):
        """月次レポート生成"""
        tweets = [
            create_test_tweet("1", "テスト", datetime(2026, 1, 15, 10, 0), likes=100),
        ]

        result = generate_period_report(tweets, "monthly", datetime(2026, 1, 15))

        assert isinstance(result, MonthlySummary)

    def test_invalid_period_type(self):
        """不正なperiod_typeの場合"""
        with pytest.raises(ValueError) as exc_info:
            generate_period_report([], "daily", datetime(2026, 1, 1))

        assert "不正なperiod_type" in str(exc_info.value)

    def test_default_date(self):
        """日付指定なしの場合"""
        result = generate_period_report([], "weekly")

        assert isinstance(result, WeeklySummary)


class TestInsightGeneration:
    """インサイト生成のテスト"""

    def test_weekly_low_post_count_insight(self):
        """投稿数が少ない場合のインサイト"""
        summary = WeeklySummary(
            week_number=1,
            year=2026,
            period_start=datetime(2026, 1, 5),
            period_end=datetime(2026, 1, 11),
            total_posts=1,
            metrics=EngagementMetrics(total_likes=10),
            best_performing_day="月曜日",
        )

        insights = generate_weekly_insights(summary, None)

        assert any("投稿数" in i for i in insights)

    def test_monthly_growth_insight(self):
        """成長率に関するインサイト"""
        summary = MonthlySummary(
            month=1,
            year=2026,
            period_start=datetime(2026, 1, 1),
            period_end=datetime(2026, 1, 31),
            total_posts=10,
            metrics=EngagementMetrics(total_likes=100),
            growth_rate=50.0,
        )

        insights = generate_monthly_insights(summary, None)

        assert any("成長" in i for i in insights)


class TestEdgeCases:
    """エッジケースのテスト"""

    def test_tweets_outside_week_range(self):
        """週の範囲外のツイートは除外される"""
        tweets = [
            create_test_tweet("1", "範囲内", datetime(2026, 1, 5, 10, 0), likes=100),
            create_test_tweet("2", "範囲外", datetime(2026, 1, 1, 10, 0), likes=999),
        ]

        result = generate_weekly_summary(tweets, datetime(2026, 1, 7))

        # 1月5日週のみカウント
        assert result.total_posts == 1
        assert result.metrics.total_likes == 100

    def test_tweets_outside_month_range(self):
        """月の範囲外のツイートは除外される"""
        tweets = [
            create_test_tweet("1", "1月", datetime(2026, 1, 15, 10, 0), likes=100),
            create_test_tweet("2", "2月", datetime(2026, 2, 15, 10, 0), likes=999),
        ]

        result = generate_monthly_summary(tweets, 2026, 1)

        assert result.total_posts == 1
        assert result.metrics.total_likes == 100

    def test_year_boundary(self):
        """年をまたぐ場合"""
        tweets = [
            create_test_tweet("1", "12月", datetime(2025, 12, 31, 10, 0), likes=100),
        ]

        result = generate_monthly_summary(tweets, 2025, 12)

        assert result.month == 12
        assert result.year == 2025
        assert result.total_posts == 1
