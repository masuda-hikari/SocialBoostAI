"""
Instagram関連モデル・クライアントのテスト
"""

from datetime import UTC, datetime, timedelta

import pytest

from src.models import (
    CrossPlatformMetrics,
    InstagramAccount,
    InstagramEngagementMetrics,
    InstagramPost,
    InstagramReel,
    InstagramStory,
    PlatformType,
    Tweet,
    UnifiedPost,
)
from src.instagram_client import (
    InstagramAPIError,
    InstagramClient,
    load_sample_instagram_posts,
)


# =============================================================================
# InstagramPost モデルテスト
# =============================================================================


class TestInstagramPostModel:
    """InstagramPostモデルのテスト"""

    def test_create_basic_post(self):
        """基本的な投稿作成"""
        post = InstagramPost(
            id="12345",
            media_type="IMAGE",
            created_at=datetime.now(UTC),
            likes=100,
            comments=10,
        )
        assert post.id == "12345"
        assert post.media_type == "IMAGE"
        assert post.likes == 100
        assert post.comments == 10

    def test_create_post_with_all_fields(self):
        """全フィールドを含む投稿作成"""
        created = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
        post = InstagramPost(
            id="12345",
            caption="テスト投稿 #test #instagram",
            media_type="CAROUSEL_ALBUM",
            media_url="https://example.com/image.jpg",
            thumbnail_url="https://example.com/thumb.jpg",
            permalink="https://instagram.com/p/12345",
            created_at=created,
            likes=500,
            comments=50,
            saves=30,
            shares=10,
            impressions=5000,
            reach=4000,
            engagement=590,
            author_id="user123",
        )
        assert post.caption == "テスト投稿 #test #instagram"
        assert post.saves == 30
        assert post.impressions == 5000
        assert post.reach == 4000

    def test_default_values(self):
        """デフォルト値の確認"""
        post = InstagramPost(
            id="12345",
            media_type="IMAGE",
            created_at=datetime.now(UTC),
        )
        assert post.likes == 0
        assert post.comments == 0
        assert post.saves is None
        assert post.caption is None

    def test_negative_likes_validation(self):
        """負の値はバリデーションエラー"""
        with pytest.raises(ValueError):
            InstagramPost(
                id="12345",
                media_type="IMAGE",
                created_at=datetime.now(UTC),
                likes=-1,
            )


class TestInstagramReelModel:
    """InstagramReelモデルのテスト"""

    def test_create_reel(self):
        """リール作成"""
        reel = InstagramReel(
            id="reel123",
            caption="リールテスト",
            created_at=datetime.now(UTC),
            likes=1000,
            comments=100,
            plays=10000,
        )
        assert reel.id == "reel123"
        assert reel.plays == 10000
        assert reel.likes == 1000


class TestInstagramStoryModel:
    """InstagramStoryモデルのテスト"""

    def test_create_story(self):
        """ストーリー作成"""
        now = datetime.now(UTC)
        story = InstagramStory(
            id="story123",
            media_type="VIDEO",
            created_at=now,
            expires_at=now + timedelta(hours=24),
            impressions=500,
            replies=5,
        )
        assert story.id == "story123"
        assert story.media_type == "VIDEO"
        assert story.expires_at > story.created_at


class TestInstagramEngagementMetrics:
    """InstagramEngagementMetricsモデルのテスト"""

    def test_default_metrics(self):
        """デフォルト値のテスト"""
        metrics = InstagramEngagementMetrics()
        assert metrics.total_likes == 0
        assert metrics.total_comments == 0
        assert metrics.engagement_rate == 0.0

    def test_metrics_with_values(self):
        """値を持つメトリクス"""
        metrics = InstagramEngagementMetrics(
            total_likes=1000,
            total_comments=100,
            total_saves=50,
            engagement_rate=5.5,
            avg_likes_per_post=100.0,
        )
        assert metrics.total_likes == 1000
        assert metrics.engagement_rate == 5.5


class TestInstagramAccount:
    """InstagramAccountモデルのテスト"""

    def test_create_account(self):
        """アカウント作成"""
        account = InstagramAccount(
            id="acc123",
            username="testuser",
            name="Test User",
            followers_count=10000,
            following_count=500,
            media_count=100,
            is_business_account=True,
        )
        assert account.username == "testuser"
        assert account.followers_count == 10000
        assert account.is_business_account is True


# =============================================================================
# UnifiedPost（統一投稿モデル）テスト
# =============================================================================


class TestUnifiedPost:
    """UnifiedPostモデルのテスト"""

    def test_from_tweet(self):
        """TweetからUnifiedPostへの変換"""
        tweet = Tweet(
            id="tweet123",
            text="テストツイート #test",
            created_at=datetime.now(UTC),
            likes=100,
            retweets=20,
            replies=10,
            impressions=1000,
            author_id="user123",
        )

        unified = UnifiedPost.from_tweet(tweet)

        assert unified.id == "tweet123"
        assert unified.platform == PlatformType.TWITTER
        assert unified.content == "テストツイート #test"
        assert unified.likes == 100
        assert unified.shares == 20
        assert unified.comments == 10
        assert unified.impressions == 1000
        # エンゲージメント率: (100+20+10)/1000 * 100 = 13%
        assert unified.engagement_rate == pytest.approx(13.0)

    def test_from_tweet_no_impressions(self):
        """インプレッションなしのツイート変換"""
        tweet = Tweet(
            id="tweet123",
            text="テスト",
            created_at=datetime.now(UTC),
            likes=50,
            retweets=5,
            replies=5,
        )

        unified = UnifiedPost.from_tweet(tweet)

        assert unified.engagement_rate == 0.0

    def test_from_instagram_post(self):
        """InstagramPostからUnifiedPostへの変換"""
        post = InstagramPost(
            id="ig123",
            caption="テスト投稿 #instagram",
            media_type="IMAGE",
            created_at=datetime.now(UTC),
            likes=500,
            comments=50,
            saves=30,
            shares=10,
            reach=5000,
            permalink="https://instagram.com/p/ig123",
            author_id="user456",
        )

        unified = UnifiedPost.from_instagram_post(post)

        assert unified.id == "ig123"
        assert unified.platform == PlatformType.INSTAGRAM
        assert unified.content == "テスト投稿 #instagram"
        assert unified.media_type == "image"
        assert unified.likes == 500
        assert unified.comments == 50
        assert unified.shares == 10
        assert unified.reach == 5000
        # エンゲージメント率: (500+50+30)/5000 * 100 = 11.6%
        assert unified.engagement_rate == pytest.approx(11.6)


class TestCrossPlatformMetrics:
    """CrossPlatformMetricsモデルのテスト"""

    def test_create_metrics(self):
        """クロスプラットフォーム指標の作成"""
        metrics = CrossPlatformMetrics(
            platforms=["twitter", "instagram"],
            period_start=datetime(2026, 1, 1, tzinfo=UTC),
            period_end=datetime(2026, 1, 7, tzinfo=UTC),
            total_posts=100,
            total_engagement=5000,
            avg_engagement_rate=5.0,
            platform_breakdown={
                "twitter": {"posts": 60, "engagement": 3000},
                "instagram": {"posts": 40, "engagement": 2000},
            },
            best_performing_platform="twitter",
            recommendations=["Twitterの投稿頻度を維持", "Instagramのハッシュタグを最適化"],
        )

        assert len(metrics.platforms) == 2
        assert metrics.best_performing_platform == "twitter"
        assert len(metrics.recommendations) == 2


# =============================================================================
# InstagramClient テスト
# =============================================================================


class TestInstagramClient:
    """InstagramClientのテスト"""

    def test_client_initialization(self):
        """クライアント初期化"""
        client = InstagramClient()
        assert client._access_token is None
        assert client._business_id is None

    def test_missing_access_token(self, monkeypatch):
        """アクセストークン未設定時のエラー"""
        monkeypatch.delenv("INSTAGRAM_ACCESS_TOKEN", raising=False)
        client = InstagramClient()

        with pytest.raises(InstagramAPIError) as exc_info:
            client._get_access_token()

        assert "INSTAGRAM_ACCESS_TOKEN" in str(exc_info.value)

    def test_missing_business_id(self, monkeypatch):
        """ビジネスID未設定時のエラー"""
        monkeypatch.delenv("INSTAGRAM_BUSINESS_ID", raising=False)
        client = InstagramClient()

        with pytest.raises(InstagramAPIError) as exc_info:
            client._get_business_id()

        assert "INSTAGRAM_BUSINESS_ID" in str(exc_info.value)


class TestInstagramEngagementCalculation:
    """エンゲージメント計算のテスト"""

    def test_calculate_engagement_metrics(self):
        """エンゲージメント指標の計算"""
        posts = [
            InstagramPost(
                id="1",
                media_type="IMAGE",
                created_at=datetime.now(UTC),
                likes=100,
                comments=10,
                saves=5,
            ),
            InstagramPost(
                id="2",
                media_type="IMAGE",
                created_at=datetime.now(UTC),
                likes=200,
                comments=20,
                saves=10,
            ),
        ]

        client = InstagramClient()
        metrics = client.calculate_engagement_metrics(posts, follower_count=1000)

        assert metrics.total_likes == 300
        assert metrics.total_comments == 30
        assert metrics.total_saves == 15
        assert metrics.avg_likes_per_post == 150.0
        assert metrics.avg_comments_per_post == 15.0
        # エンゲージメント率: (300+30+15)/2/1000 * 100 = 17.25%
        assert metrics.engagement_rate == pytest.approx(17.25)

    def test_calculate_empty_posts(self):
        """空の投稿リストでの計算"""
        client = InstagramClient()
        metrics = client.calculate_engagement_metrics([], follower_count=1000)

        assert metrics.total_likes == 0
        assert metrics.engagement_rate == 0.0

    def test_calculate_zero_followers(self):
        """フォロワー0の場合"""
        posts = [
            InstagramPost(
                id="1",
                media_type="IMAGE",
                created_at=datetime.now(UTC),
                likes=100,
                comments=10,
            ),
        ]

        client = InstagramClient()
        metrics = client.calculate_engagement_metrics(posts, follower_count=0)

        assert metrics.total_likes == 100
        assert metrics.engagement_rate == 0.0


class TestInstagramAPIError:
    """InstagramAPIErrorのテスト"""

    def test_error_with_code(self):
        """エラーコード付きのエラー"""
        error = InstagramAPIError("アクセス拒否", code=403)
        assert str(error) == "アクセス拒否"
        assert error.code == 403

    def test_error_without_code(self):
        """エラーコードなしのエラー"""
        error = InstagramAPIError("不明なエラー")
        assert str(error) == "不明なエラー"
        assert error.code is None
