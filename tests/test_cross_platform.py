"""
クロスプラットフォーム比較機能テスト
"""

import pytest
from datetime import datetime, UTC, timedelta

from src.models import (
    AnalysisResult,
    InstagramAnalysisResult,
    EngagementMetrics,
    InstagramEngagementMetrics,
    HourlyEngagement,
    HashtagAnalysis,
    ContentPattern,
    CrossPlatformComparison,
    PlatformPerformance,
    PlatformComparisonItem,
    PlatformType,
)
from src.cross_platform import (
    extract_twitter_performance,
    extract_instagram_performance,
    compare_metrics,
    determine_overall_winner,
    generate_cross_platform_insights,
    generate_strategic_recommendations,
    generate_synergy_opportunities,
    compare_platforms,
)


# =============================================================================
# テストフィクスチャ
# =============================================================================


@pytest.fixture
def sample_twitter_analysis() -> AnalysisResult:
    """サンプルTwitter分析結果"""
    now = datetime.now(UTC)
    return AnalysisResult(
        period_start=now - timedelta(days=7),
        period_end=now,
        total_posts=50,
        metrics=EngagementMetrics(
            total_likes=1000,
            total_retweets=200,
            total_replies=100,
            engagement_rate=2.5,
            avg_likes_per_post=20.0,
            avg_retweets_per_post=4.0,
        ),
        hourly_breakdown=[
            HourlyEngagement(
                hour=h,
                avg_likes=20 if h == 12 else 10,
                avg_retweets=5 if h == 12 else 2,
                post_count=5 if h == 12 else 2,
                total_engagement=25 if h == 12 else 12,
            )
            for h in range(24)
        ],
        top_performing_posts=[],
        hashtag_analysis=[
            HashtagAnalysis(hashtag="python", usage_count=10, effectiveness_score=1.5),
            HashtagAnalysis(hashtag="ai", usage_count=8, effectiveness_score=1.3),
        ],
        content_patterns=[
            ContentPattern(
                pattern_type="tip",
                count=15,
                avg_engagement=25.0,
            ),
        ],
    )


@pytest.fixture
def sample_instagram_analysis() -> InstagramAnalysisResult:
    """サンプルInstagram分析結果"""
    now = datetime.now(UTC)
    return InstagramAnalysisResult(
        period_start=now - timedelta(days=7),
        period_end=now,
        total_posts=30,
        total_reels=10,
        metrics=InstagramEngagementMetrics(
            total_likes=2000,
            total_comments=300,
            total_saves=150,
            total_shares=50,
            total_impressions=50000,
            total_reach=30000,
            engagement_rate=3.5,
            avg_likes_per_post=66.7,
            avg_comments_per_post=10.0,
            avg_saves_per_post=5.0,
        ),
        hourly_breakdown=[
            HourlyEngagement(
                hour=h,
                avg_likes=50 if h == 18 else 30,
                avg_retweets=10 if h == 18 else 5,  # commentsとして使用
                post_count=4 if h == 18 else 1,
                total_engagement=60 if h == 18 else 35,
            )
            for h in range(24)
        ],
        top_performing_posts=[],
        top_performing_reels=[],
        hashtag_analysis=[
            HashtagAnalysis(hashtag="photography", usage_count=15, effectiveness_score=2.0),
            HashtagAnalysis(hashtag="instagood", usage_count=12, effectiveness_score=1.8),
        ],
        content_patterns=[
            ContentPattern(
                pattern_type="tutorial",
                count=10,
                avg_engagement=80.0,
            ),
        ],
    )


# =============================================================================
# extract_twitter_performance テスト
# =============================================================================


class TestExtractTwitterPerformance:
    """Twitterパフォーマンス抽出テスト"""

    def test_基本抽出(self, sample_twitter_analysis: AnalysisResult):
        """基本的なパフォーマンス抽出"""
        perf = extract_twitter_performance(sample_twitter_analysis)

        assert perf.platform == PlatformType.TWITTER
        assert perf.total_posts == 50
        assert perf.total_engagement == 1300  # 1000 + 200 + 100
        assert perf.avg_engagement_rate == 2.5
        assert perf.avg_likes_per_post == 20.0
        assert perf.best_hour == 12
        assert "python" in perf.top_hashtags

    def test_コンテンツインサイト生成(self, sample_twitter_analysis: AnalysisResult):
        """コンテンツインサイトが正しく生成されること"""
        perf = extract_twitter_performance(sample_twitter_analysis)

        assert len(perf.content_insights) > 0
        assert "Tips/ノウハウ" in perf.content_insights[0]


# =============================================================================
# extract_instagram_performance テスト
# =============================================================================


class TestExtractInstagramPerformance:
    """Instagramパフォーマンス抽出テスト"""

    def test_基本抽出(self, sample_instagram_analysis: InstagramAnalysisResult):
        """基本的なパフォーマンス抽出"""
        perf = extract_instagram_performance(sample_instagram_analysis)

        assert perf.platform == PlatformType.INSTAGRAM
        assert perf.total_posts == 40  # 30 + 10
        assert perf.total_engagement == 2450  # 2000 + 300 + 150
        assert perf.avg_engagement_rate == 3.5
        assert perf.avg_likes_per_post == 66.7
        assert perf.best_hour == 18
        assert "photography" in perf.top_hashtags

    def test_コンテンツインサイト生成(self, sample_instagram_analysis: InstagramAnalysisResult):
        """コンテンツインサイトが正しく生成されること"""
        perf = extract_instagram_performance(sample_instagram_analysis)

        assert len(perf.content_insights) > 0
        assert "チュートリアル" in perf.content_insights[0]


# =============================================================================
# compare_metrics テスト
# =============================================================================


class TestCompareMetrics:
    """指標比較テスト"""

    def test_両プラットフォーム比較(
        self,
        sample_twitter_analysis: AnalysisResult,
        sample_instagram_analysis: InstagramAnalysisResult,
    ):
        """両プラットフォームの比較"""
        twitter_perf = extract_twitter_performance(sample_twitter_analysis)
        instagram_perf = extract_instagram_performance(sample_instagram_analysis)

        items = compare_metrics(twitter_perf, instagram_perf)

        assert len(items) == 6  # 6つの比較項目

        # 投稿数比較
        post_item = next(i for i in items if i.metric_name == "投稿数")
        assert post_item.twitter_value == 50
        assert post_item.instagram_value == 40

        # エンゲージメント率比較
        er_item = next(i for i in items if i.metric_name == "エンゲージメント率")
        assert er_item.twitter_value == 2.5
        assert er_item.instagram_value == 3.5
        assert er_item.winner == "instagram"

    def test_Twitterのみ(self, sample_twitter_analysis: AnalysisResult):
        """Twitterのみの場合"""
        twitter_perf = extract_twitter_performance(sample_twitter_analysis)

        items = compare_metrics(twitter_perf, None)

        assert len(items) == 6
        for item in items:
            assert item.twitter_value is not None
            assert item.instagram_value is None
            assert item.winner == "twitter"

    def test_Instagramのみ(self, sample_instagram_analysis: InstagramAnalysisResult):
        """Instagramのみの場合"""
        instagram_perf = extract_instagram_performance(sample_instagram_analysis)

        items = compare_metrics(None, instagram_perf)

        assert len(items) == 6
        for item in items:
            assert item.twitter_value is None
            assert item.instagram_value is not None
            assert item.winner == "instagram"


# =============================================================================
# determine_overall_winner テスト
# =============================================================================


class TestDetermineOverallWinner:
    """総合勝者決定テスト"""

    def test_Instagramが勝つケース(
        self,
        sample_twitter_analysis: AnalysisResult,
        sample_instagram_analysis: InstagramAnalysisResult,
    ):
        """Instagramが総合的に勝つケース"""
        twitter_perf = extract_twitter_performance(sample_twitter_analysis)
        instagram_perf = extract_instagram_performance(sample_instagram_analysis)

        items = compare_metrics(twitter_perf, instagram_perf)
        winner = determine_overall_winner(items)

        # Instagram has higher engagement rate (weighted more)
        assert winner == "instagram"

    def test_空の比較項目(self):
        """比較項目が空の場合"""
        winner = determine_overall_winner([])
        assert winner == "tie"


# =============================================================================
# generate_cross_platform_insights テスト
# =============================================================================


class TestGenerateCrossPlatformInsights:
    """クロスプラットフォームインサイト生成テスト"""

    def test_インサイト生成(
        self,
        sample_twitter_analysis: AnalysisResult,
        sample_instagram_analysis: InstagramAnalysisResult,
    ):
        """インサイトが正しく生成されること"""
        twitter_perf = extract_twitter_performance(sample_twitter_analysis)
        instagram_perf = extract_instagram_performance(sample_instagram_analysis)
        items = compare_metrics(twitter_perf, instagram_perf)
        winner = determine_overall_winner(items)

        insights = generate_cross_platform_insights(
            twitter_perf, instagram_perf, items, winner
        )

        assert len(insights) > 0
        # 総合評価が含まれること
        assert any("総合評価" in i for i in insights)


# =============================================================================
# generate_strategic_recommendations テスト
# =============================================================================


class TestGenerateStrategicRecommendations:
    """戦略レコメンデーション生成テスト"""

    def test_レコメンデーション生成(
        self,
        sample_twitter_analysis: AnalysisResult,
        sample_instagram_analysis: InstagramAnalysisResult,
    ):
        """レコメンデーションが正しく生成されること"""
        twitter_perf = extract_twitter_performance(sample_twitter_analysis)
        instagram_perf = extract_instagram_performance(sample_instagram_analysis)
        items = compare_metrics(twitter_perf, instagram_perf)
        winner = determine_overall_winner(items)

        recommendations = generate_strategic_recommendations(
            twitter_perf, instagram_perf, items, winner
        )

        assert len(recommendations) > 0
        # 主力プラットフォームの提案が含まれること
        assert any("主力" in r or "プラットフォーム" in r for r in recommendations)


# =============================================================================
# generate_synergy_opportunities テスト
# =============================================================================


class TestGenerateSynergyOpportunities:
    """シナジー機会生成テスト"""

    def test_シナジー機会生成(
        self,
        sample_twitter_analysis: AnalysisResult,
        sample_instagram_analysis: InstagramAnalysisResult,
    ):
        """シナジー機会が正しく生成されること"""
        twitter_perf = extract_twitter_performance(sample_twitter_analysis)
        instagram_perf = extract_instagram_performance(sample_instagram_analysis)

        opportunities = generate_synergy_opportunities(twitter_perf, instagram_perf)

        assert len(opportunities) > 0
        # 連携に関する提案が含まれること
        assert any("🔗" in o for o in opportunities)


# =============================================================================
# compare_platforms テスト
# =============================================================================


class TestComparePlatforms:
    """プラットフォーム比較統合テスト"""

    def test_両プラットフォーム比較(
        self,
        sample_twitter_analysis: AnalysisResult,
        sample_instagram_analysis: InstagramAnalysisResult,
    ):
        """両プラットフォームの完全な比較"""
        result = compare_platforms(
            twitter_analysis=sample_twitter_analysis,
            instagram_analysis=sample_instagram_analysis,
        )

        assert isinstance(result, CrossPlatformComparison)
        assert len(result.platforms_analyzed) == 2
        assert "twitter" in result.platforms_analyzed
        assert "instagram" in result.platforms_analyzed
        assert result.twitter_performance is not None
        assert result.instagram_performance is not None
        assert len(result.comparison_items) > 0
        assert result.overall_winner is not None
        assert len(result.cross_platform_insights) > 0
        assert len(result.strategic_recommendations) > 0
        assert len(result.synergy_opportunities) > 0

    def test_Twitterのみ(self, sample_twitter_analysis: AnalysisResult):
        """Twitterのみの比較"""
        result = compare_platforms(
            twitter_analysis=sample_twitter_analysis,
            instagram_analysis=None,
        )

        assert len(result.platforms_analyzed) == 1
        assert "twitter" in result.platforms_analyzed
        assert result.twitter_performance is not None
        assert result.instagram_performance is None

    def test_Instagramのみ(self, sample_instagram_analysis: InstagramAnalysisResult):
        """Instagramのみの比較"""
        result = compare_platforms(
            twitter_analysis=None,
            instagram_analysis=sample_instagram_analysis,
        )

        assert len(result.platforms_analyzed) == 1
        assert "instagram" in result.platforms_analyzed
        assert result.twitter_performance is None
        assert result.instagram_performance is not None

    def test_両方なし(self):
        """両方なしの場合"""
        result = compare_platforms(
            twitter_analysis=None,
            instagram_analysis=None,
        )

        assert len(result.platforms_analyzed) == 0
        assert result.twitter_performance is None
        assert result.instagram_performance is None

    def test_期間指定(
        self,
        sample_twitter_analysis: AnalysisResult,
        sample_instagram_analysis: InstagramAnalysisResult,
    ):
        """期間を指定した比較"""
        now = datetime.now(UTC)
        period_start = now - timedelta(days=30)
        period_end = now

        result = compare_platforms(
            twitter_analysis=sample_twitter_analysis,
            instagram_analysis=sample_instagram_analysis,
            period_start=period_start,
            period_end=period_end,
        )

        assert result.period_start == period_start
        assert result.period_end == period_end


# =============================================================================
# モデルテスト
# =============================================================================


class TestCrossPlatformModels:
    """クロスプラットフォームモデルテスト"""

    def test_PlatformPerformance作成(self):
        """PlatformPerformanceモデルの作成"""
        perf = PlatformPerformance(
            platform="twitter",
            total_posts=100,
            total_engagement=5000,
            avg_engagement_rate=5.0,
            avg_likes_per_post=30.0,
            avg_comments_per_post=10.0,
            avg_shares_per_post=10.0,
            best_hour=12,
            top_hashtags=["python", "ai"],
            content_insights=["Tipsが効果的"],
        )

        assert perf.platform == "twitter"
        assert perf.total_posts == 100

    def test_PlatformComparisonItem作成(self):
        """PlatformComparisonItemモデルの作成"""
        item = PlatformComparisonItem(
            metric_name="エンゲージメント率",
            twitter_value=2.5,
            instagram_value=3.5,
            difference_percent=40.0,
            winner="instagram",
            insight="Instagramのエンゲージメント率が40%高い",
        )

        assert item.metric_name == "エンゲージメント率"
        assert item.winner == "instagram"

    def test_CrossPlatformComparison作成(self):
        """CrossPlatformComparisonモデルの作成"""
        now = datetime.now(UTC)
        comparison = CrossPlatformComparison(
            period_start=now - timedelta(days=7),
            period_end=now,
            platforms_analyzed=["twitter", "instagram"],
            twitter_performance=PlatformPerformance(
                platform="twitter",
                total_posts=50,
                total_engagement=1000,
            ),
            instagram_performance=PlatformPerformance(
                platform="instagram",
                total_posts=30,
                total_engagement=2000,
            ),
            comparison_items=[],
            overall_winner="instagram",
            cross_platform_insights=["Instagramが優勢"],
            strategic_recommendations=["Instagramに注力"],
            synergy_opportunities=["連携投稿"],
        )

        assert len(comparison.platforms_analyzed) == 2
        assert comparison.overall_winner == "instagram"
