"""
データモデルのテスト
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.models import (
    AnalysisResult,
    EngagementMetrics,
    HourlyEngagement,
    PostRecommendation,
    Tweet,
    UserAccount,
)


class TestTweet:
    """Tweetモデルのテスト"""

    def test_valid_tweet(self) -> None:
        """有効なツイートを作成できること"""
        tweet = Tweet(
            id="123",
            text="Hello World!",
            created_at=datetime.now(),
            likes=10,
            retweets=5,
            replies=2,
        )

        assert tweet.id == "123"
        assert tweet.likes == 10

    def test_default_values(self) -> None:
        """デフォルト値が正しく設定されること"""
        tweet = Tweet(
            id="123",
            text="Test",
            created_at=datetime.now(),
        )

        assert tweet.likes == 0
        assert tweet.retweets == 0
        assert tweet.replies == 0
        assert tweet.impressions is None

    def test_negative_likes_rejected(self) -> None:
        """負のいいね数は拒否されること"""
        with pytest.raises(ValidationError):
            Tweet(
                id="123",
                text="Test",
                created_at=datetime.now(),
                likes=-1,
            )


class TestEngagementMetrics:
    """EngagementMetricsモデルのテスト"""

    def test_default_values(self) -> None:
        """デフォルト値が正しく設定されること"""
        metrics = EngagementMetrics()

        assert metrics.total_likes == 0
        assert metrics.engagement_rate == 0.0


class TestHourlyEngagement:
    """HourlyEngagementモデルのテスト"""

    def test_valid_hour(self) -> None:
        """有効な時間帯を作成できること"""
        hourly = HourlyEngagement(
            hour=14,
            avg_likes=50.0,
            avg_retweets=10.0,
            post_count=5,
            total_engagement=60.0,
        )

        assert hourly.hour == 14

    def test_invalid_hour_rejected(self) -> None:
        """無効な時間帯は拒否されること"""
        with pytest.raises(ValidationError):
            HourlyEngagement(
                hour=25,  # 無効
                avg_likes=50.0,
                avg_retweets=10.0,
                post_count=5,
                total_engagement=60.0,
            )


class TestPostRecommendation:
    """PostRecommendationモデルのテスト"""

    def test_valid_recommendation(self) -> None:
        """有効なレコメンデーションを作成できること"""
        rec = PostRecommendation(
            best_hours=[9, 14, 19],
            suggested_hashtags=["Python", "プログラミング"],
            content_ideas=["Tip of the day", "今日の学び"],
            reasoning="14時台の投稿が最もエンゲージメントが高いです。",
        )

        assert len(rec.best_hours) == 3
        assert len(rec.suggested_hashtags) == 2


class TestUserAccount:
    """UserAccountモデルのテスト"""

    def test_valid_account(self) -> None:
        """有効なアカウントを作成できること"""
        account = UserAccount(
            id="12345",
            platform="twitter",
            username="testuser",
            follower_count=1000,
            following_count=500,
        )

        assert account.username == "testuser"
        assert account.follower_count == 1000
