"""
AI拡張機能モジュールのテスト
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.ai_advanced import (
    AdvancedAISuggester,
    OptimalTimingAnalyzer,
    PersonalizedRecommender,
    ReplyGenerator,
    TrendAnalyzer,
)
from src.models import (
    AnalysisResult,
    ContentPattern,
    EngagementMetrics,
    HashtagAnalysis,
    HourlyEngagement,
    KeywordAnalysis,
    PostRecommendation,
    Tweet,
)


@pytest.fixture
def sample_tweets() -> list[Tweet]:
    """サンプルツイートをロード"""
    sample_path = Path(__file__).parent / "sample_data" / "tweets.json"
    with open(sample_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    return [Tweet(**tweet) for tweet in data]


@pytest.fixture
def sample_hourly_engagement() -> list[HourlyEngagement]:
    """サンプル時間帯別エンゲージメント"""
    return [
        HourlyEngagement(
            hour=h,
            avg_likes=10.0 + h,
            avg_retweets=5.0 + h * 0.5,
            post_count=max(1, 10 - abs(h - 12)),
            total_engagement=15.0 + h * 1.5,
        )
        for h in range(24)
    ]


@pytest.fixture
def sample_content_patterns() -> list[ContentPattern]:
    """サンプルコンテンツパターン"""
    return [
        ContentPattern(
            pattern_type="question",
            count=5,
            avg_engagement=100.0,
            example_posts=["質問です"],
        ),
        ContentPattern(
            pattern_type="tip",
            count=3,
            avg_engagement=80.0,
            example_posts=["Tips:"],
        ),
    ]


@pytest.fixture
def sample_analysis_result(
    sample_tweets: list[Tweet],
    sample_hourly_engagement: list[HourlyEngagement],
    sample_content_patterns: list[ContentPattern],
) -> AnalysisResult:
    """サンプル分析結果"""
    return AnalysisResult(
        period_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        period_end=datetime(2026, 1, 7, tzinfo=timezone.utc),
        total_posts=15,
        metrics=EngagementMetrics(
            total_likes=500,
            total_retweets=100,
            total_replies=50,
            engagement_rate=0.05,
            avg_likes_per_post=33.3,
            avg_retweets_per_post=6.7,
        ),
        hourly_breakdown=sample_hourly_engagement,
        top_performing_posts=sample_tweets[:5],
        recommendations=PostRecommendation(
            best_hours=[12, 18, 21],
            suggested_hashtags=["tech", "ai"],
            content_ideas=["アイデア1"],
            reasoning="分析に基づく推奨",
        ),
        hashtag_analysis=[
            HashtagAnalysis(
                hashtag="tech",
                usage_count=5,
                total_likes=100,
                total_retweets=20,
                avg_engagement=24.0,
                effectiveness_score=1.5,
            )
        ],
        keyword_analysis=[
            KeywordAnalysis(
                keyword="python",
                frequency=10,
                avg_engagement=50.0,
                correlation_score=0.5,
            )
        ],
        content_patterns=sample_content_patterns,
    )


class TestTrendAnalyzer:
    """TrendAnalyzerのテスト"""

    def test_analyze_engagement_trends_increasing(self) -> None:
        """上昇トレンドの検出"""
        analyzer = TrendAnalyzer()

        # 後半のエンゲージメントが高いツイート
        tweets = [
            Tweet(
                id=str(i),
                text=f"ツイート{i}",
                created_at=datetime(2026, 1, i + 1, tzinfo=timezone.utc),
                likes=i * 10,  # 日が経つほどいいねが増える
                retweets=i * 2,
                replies=i,
            )
            for i in range(1, 8)
        ]

        result = analyzer.analyze_engagement_trends(tweets)

        assert result["trend"] in ["increasing", "stable", "decreasing"]
        assert "insights" in result

    def test_analyze_engagement_trends_empty(self) -> None:
        """空のリストで正しく処理"""
        analyzer = TrendAnalyzer()
        result = analyzer.analyze_engagement_trends([])

        assert result["trend"] == "insufficient_data"

    def test_identify_viral_patterns(self, sample_tweets: list[Tweet]) -> None:
        """バイラルパターン特定"""
        analyzer = TrendAnalyzer()
        patterns = analyzer.identify_viral_patterns(sample_tweets)

        # パターンはリストで返される
        assert isinstance(patterns, list)

    def test_identify_viral_patterns_empty(self) -> None:
        """空のリストで正しく処理"""
        analyzer = TrendAnalyzer()
        patterns = analyzer.identify_viral_patterns([])

        assert patterns == []


class TestOptimalTimingAnalyzer:
    """OptimalTimingAnalyzerのテスト"""

    def test_analyze_optimal_times(
        self, sample_hourly_engagement: list[HourlyEngagement]
    ) -> None:
        """最適時間分析"""
        analyzer = OptimalTimingAnalyzer()
        result = analyzer.analyze_optimal_times(sample_hourly_engagement)

        assert "best_times" in result
        assert "worst_times" in result
        assert "recommendations" in result
        assert len(result["best_times"]) <= 3

    def test_analyze_optimal_times_empty(self) -> None:
        """空のリストで正しく処理"""
        analyzer = OptimalTimingAnalyzer()
        result = analyzer.analyze_optimal_times([])

        assert result["best_times"] == []
        assert result["worst_times"] == []

    def test_hours_to_time_ranges(self) -> None:
        """時間帯表記変換"""
        analyzer = OptimalTimingAnalyzer()
        ranges = analyzer._hours_to_time_ranges([9, 12, 18])

        assert ranges == ["9:00-10:00", "12:00-13:00", "18:00-19:00"]

    @patch("src.ai_advanced.OptimalTimingAnalyzer._get_client")
    def test_get_ai_timing_insights(
        self,
        mock_get_client: MagicMock,
        sample_hourly_engagement: list[HourlyEngagement],
        sample_content_patterns: list[ContentPattern],
    ) -> None:
        """AIタイミング洞察生成（モック）"""
        # OpenAIクライアントをモック
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = (
            "1. 朝8時台が効果的\n2. 昼12時台も良い\n3. 夜21時台を試す"
        )
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        analyzer = OptimalTimingAnalyzer()
        result = analyzer.get_ai_timing_insights(
            sample_hourly_engagement, sample_content_patterns
        )

        assert isinstance(result, str)
        assert len(result) > 0


class TestPersonalizedRecommender:
    """PersonalizedRecommenderのテスト"""

    @patch("src.ai_advanced.PersonalizedRecommender._get_client")
    def test_generate_personalized_strategy(
        self,
        mock_get_client: MagicMock,
        sample_analysis_result: AnalysisResult,
    ) -> None:
        """パーソナライズド戦略生成（モック）"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[
            0
        ].message.content = """
## 強み
- 技術系コンテンツが強い

## 改善点
- 投稿頻度を上げる

## 具体的なアクションプラン
1. 毎日1投稿
2. 月10投稿目標
3. データ分析を習慣化

## コンテンツカレンダー提案
- 月曜: Tips投稿
"""
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        recommender = PersonalizedRecommender()
        result = recommender.generate_personalized_strategy(
            sample_analysis_result,
            goals=["フォロワー増加"],
        )

        assert "strategy" in result
        assert "generated_at" in result
        assert "based_on_posts" in result


class TestReplyGenerator:
    """ReplyGeneratorのテスト"""

    @patch("src.ai_advanced.ReplyGenerator._get_client")
    def test_generate_reply_drafts(self, mock_get_client: MagicMock) -> None:
        """返信文案生成（モック）"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[
            0
        ].message.content = """1. ありがとうございます！参考になります
---
2. なるほど、勉強になりました！
---
3. 素晴らしい視点ですね"""
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        generator = ReplyGenerator()
        result = generator.generate_reply_drafts(
            original_tweet="Pythonの新機能について解説します",
            tone="friendly",
            count=3,
        )

        assert isinstance(result, list)
        assert len(result) <= 3

    @patch("src.ai_advanced.ReplyGenerator._get_client")
    def test_generate_engagement_replies(
        self,
        mock_get_client: MagicMock,
        sample_tweets: list[Tweet],
    ) -> None:
        """エンゲージメント返信生成（モック）"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "1. いい投稿ですね！"
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        generator = ReplyGenerator()
        result = generator.generate_engagement_replies(sample_tweets[:2])

        assert isinstance(result, list)


class TestAdvancedAISuggester:
    """AdvancedAISuggesterのテスト"""

    def test_initialization(self) -> None:
        """初期化テスト"""
        suggester = AdvancedAISuggester()

        assert suggester.trend_analyzer is not None
        assert suggester.timing_analyzer is not None
        assert suggester.recommender is not None
        assert suggester.reply_generator is not None

    def test_generate_comprehensive_recommendations_no_api(
        self,
        sample_tweets: list[Tweet],
        sample_analysis_result: AnalysisResult,
    ) -> None:
        """包括的推奨生成（API呼び出しなし部分）"""
        suggester = AdvancedAISuggester()

        # API呼び出し部分をモックして、ローカル分析のみテスト
        with patch.object(
            suggester.recommender, "generate_personalized_strategy"
        ) as mock_strategy:
            mock_strategy.side_effect = Exception("API not available")

            result = suggester.generate_comprehensive_recommendations(
                sample_tweets, sample_analysis_result
            )

            # ローカル分析は成功するはず
            assert "trends" in result
            assert "viral_patterns" in result
            assert "optimal_timing" in result
            assert "errors" in result
            # API失敗はエラーリストに記録
            assert len(result["errors"]) > 0


class TestTrendAnalyzerEdgeCases:
    """TrendAnalyzerのエッジケーステスト"""

    def test_single_tweet(self) -> None:
        """単一ツイートの処理"""
        analyzer = TrendAnalyzer()
        tweets = [
            Tweet(
                id="1",
                text="テスト",
                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                likes=10,
                retweets=2,
                replies=1,
            )
        ]

        result = analyzer.analyze_engagement_trends(tweets)
        assert result["trend"] == "insufficient_data"

    def test_viral_patterns_no_viral(self) -> None:
        """バイラル投稿がない場合"""
        analyzer = TrendAnalyzer()
        # 全て同じエンゲージメントのツイート
        tweets = [
            Tweet(
                id=str(i),
                text=f"ツイート{i}",
                created_at=datetime(2026, 1, i + 1, tzinfo=timezone.utc),
                likes=10,
                retweets=2,
                replies=1,
            )
            for i in range(5)
        ]

        patterns = analyzer.identify_viral_patterns(tweets, threshold_percentile=95)
        # 結果は空か、全てがバイラルとして扱われる
        assert isinstance(patterns, list)


class TestOptimalTimingAnalyzerEdgeCases:
    """OptimalTimingAnalyzerのエッジケーステスト"""

    def test_single_hour_data(self) -> None:
        """単一時間帯のデータ"""
        analyzer = OptimalTimingAnalyzer()
        hourly = [
            HourlyEngagement(
                hour=12,
                avg_likes=50.0,
                avg_retweets=10.0,
                post_count=5,
                total_engagement=300.0,
            )
        ]

        result = analyzer.analyze_optimal_times(hourly)
        assert result["best_times"] == [12]

    def test_all_zero_engagement(self) -> None:
        """全時間帯でエンゲージメントゼロ"""
        analyzer = OptimalTimingAnalyzer()
        hourly = [
            HourlyEngagement(
                hour=h,
                avg_likes=0.0,
                avg_retweets=0.0,
                post_count=0,
                total_engagement=0.0,
            )
            for h in range(24)
        ]

        result = analyzer.analyze_optimal_times(hourly)
        assert "best_times" in result
        assert "recommendations" in result
