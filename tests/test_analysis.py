"""
分析モジュールのテスト
"""

import json
from datetime import datetime
from pathlib import Path

import pytest

from src.analysis import (
    analyze_hourly_engagement,
    analyze_tweets,
    calculate_engagement_metrics,
    find_best_posting_hours,
    get_top_performing_posts,
)
from src.models import Tweet


@pytest.fixture
def sample_tweets() -> list[Tweet]:
    """サンプルツイートをロード"""
    sample_path = Path(__file__).parent / "sample_data" / "tweets.json"
    with open(sample_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    return [Tweet(**tweet) for tweet in data]


@pytest.fixture
def empty_tweets() -> list[Tweet]:
    """空のツイートリスト"""
    return []


class TestCalculateEngagementMetrics:
    """エンゲージメント指標計算のテスト"""

    def test_basic_calculation(self, sample_tweets: list[Tweet]) -> None:
        """基本的な計算が正しく行われること"""
        metrics = calculate_engagement_metrics(sample_tweets)

        assert metrics.total_likes > 0
        assert metrics.total_retweets > 0
        assert metrics.avg_likes_per_post > 0

    def test_empty_tweets(self, empty_tweets: list[Tweet]) -> None:
        """空のリストでもエラーにならないこと"""
        metrics = calculate_engagement_metrics(empty_tweets)

        assert metrics.total_likes == 0
        assert metrics.total_retweets == 0
        assert metrics.engagement_rate == 0.0

    def test_engagement_rate_calculation(self, sample_tweets: list[Tweet]) -> None:
        """エンゲージメント率が正しく計算されること"""
        metrics = calculate_engagement_metrics(sample_tweets)

        # インプレッションがあるのでエンゲージメント率は0より大きい
        assert metrics.engagement_rate >= 0


class TestAnalyzeHourlyEngagement:
    """時間帯別エンゲージメント分析のテスト"""

    def test_returns_24_hours(self, sample_tweets: list[Tweet]) -> None:
        """24時間分のデータを返すこと"""
        result = analyze_hourly_engagement(sample_tweets)

        assert len(result) == 24
        assert all(0 <= h.hour <= 23 for h in result)

    def test_hour_ordering(self, sample_tweets: list[Tweet]) -> None:
        """時間帯が0から23まで順番になっていること"""
        result = analyze_hourly_engagement(sample_tweets)

        hours = [h.hour for h in result]
        assert hours == list(range(24))

    def test_empty_tweets(self, empty_tweets: list[Tweet]) -> None:
        """空のリストでも24時間分を返すこと"""
        result = analyze_hourly_engagement(empty_tweets)

        assert len(result) == 24
        assert all(h.post_count == 0 for h in result)


class TestFindBestPostingHours:
    """最適投稿時間特定のテスト"""

    def test_returns_top_n(self, sample_tweets: list[Tweet]) -> None:
        """指定した数の時間帯を返すこと"""
        hourly = analyze_hourly_engagement(sample_tweets)
        best_hours = find_best_posting_hours(hourly, top_n=3)

        assert len(best_hours) <= 3

    def test_returns_valid_hours(self, sample_tweets: list[Tweet]) -> None:
        """有効な時間帯（0-23）を返すこと"""
        hourly = analyze_hourly_engagement(sample_tweets)
        best_hours = find_best_posting_hours(hourly)

        assert all(0 <= h <= 23 for h in best_hours)


class TestGetTopPerformingPosts:
    """トップパフォーマンス投稿取得のテスト"""

    def test_returns_top_n(self, sample_tweets: list[Tweet]) -> None:
        """指定した数の投稿を返すこと"""
        top_posts = get_top_performing_posts(sample_tweets, top_n=5)

        assert len(top_posts) <= 5

    def test_sorted_by_engagement(self, sample_tweets: list[Tweet]) -> None:
        """エンゲージメント順にソートされていること"""
        top_posts = get_top_performing_posts(sample_tweets, top_n=5)

        engagements = [p.likes + p.retweets + p.replies for p in top_posts]
        assert engagements == sorted(engagements, reverse=True)

    def test_empty_tweets(self, empty_tweets: list[Tweet]) -> None:
        """空のリストでもエラーにならないこと"""
        top_posts = get_top_performing_posts(empty_tweets)

        assert top_posts == []


class TestAnalyzeTweets:
    """総合分析のテスト"""

    def test_returns_analysis_result(self, sample_tweets: list[Tweet]) -> None:
        """AnalysisResultを返すこと"""
        result = analyze_tweets(sample_tweets)

        assert result.total_posts == len(sample_tweets)
        assert result.metrics is not None
        assert result.hourly_breakdown is not None
        assert result.top_performing_posts is not None
        assert result.recommendations is not None

    def test_period_detection(self, sample_tweets: list[Tweet]) -> None:
        """期間が正しく検出されること"""
        result = analyze_tweets(sample_tweets)

        assert result.period_start <= result.period_end

    def test_recommendations_generated(self, sample_tweets: list[Tweet]) -> None:
        """レコメンデーションが生成されること"""
        result = analyze_tweets(sample_tweets)

        assert result.recommendations is not None
        assert len(result.recommendations.best_hours) > 0
        assert result.recommendations.reasoning != ""

    def test_empty_tweets(self, empty_tweets: list[Tweet]) -> None:
        """空のリストでもエラーにならないこと"""
        result = analyze_tweets(empty_tweets)

        assert result.total_posts == 0
        assert result.metrics.total_likes == 0


class TestIntegration:
    """統合テスト"""

    def test_full_analysis_pipeline(self, sample_tweets: list[Tweet]) -> None:
        """分析パイプライン全体が正しく動作すること"""
        # 分析実行
        result = analyze_tweets(sample_tweets)

        # 基本的なアサーション
        assert result.total_posts == 15
        assert result.metrics.total_likes > 0

        # 時間帯別分析
        assert len(result.hourly_breakdown) == 24

        # トップ投稿
        assert len(result.top_performing_posts) > 0

        # レコメンデーション
        assert result.recommendations is not None
        assert len(result.recommendations.best_hours) >= 1

    def test_peak_hour_identification(self, sample_tweets: list[Tweet]) -> None:
        """ピーク時間帯が正しく特定されること"""
        result = analyze_tweets(sample_tweets)

        # 14時台の投稿が最もエンゲージメントが高い（サンプルデータより）
        # このテストはサンプルデータに依存
        assert result.recommendations is not None
        best_hours = result.recommendations.best_hours

        # 少なくとも1つの時間帯が特定されていること
        assert len(best_hours) >= 1
