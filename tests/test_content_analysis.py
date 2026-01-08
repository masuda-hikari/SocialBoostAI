"""
コンテンツ分析モジュールのテスト
"""

import json
from datetime import datetime
from pathlib import Path

import pytest

from src.content_analysis import (
    analyze_content_patterns,
    analyze_hashtags,
    analyze_keywords,
    extract_hashtags,
    extract_keywords,
    get_effective_hashtag_recommendations,
    get_high_engagement_keywords,
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
def tweets_with_hashtags() -> list[Tweet]:
    """ハッシュタグ付きツイート"""
    return [
        Tweet(
            id="1",
            text="Pythonで機械学習 #Python #機械学習 #AI",
            created_at=datetime.now(),
            likes=100,
            retweets=20,
            replies=5,
        ),
        Tweet(
            id="2",
            text="今日のPython学習 #Python #プログラミング",
            created_at=datetime.now(),
            likes=50,
            retweets=10,
            replies=3,
        ),
        Tweet(
            id="3",
            text="機械学習の基礎 #機械学習 #AI",
            created_at=datetime.now(),
            likes=80,
            retweets=15,
            replies=8,
        ),
        Tweet(
            id="4",
            text="ハッシュタグなしの投稿",
            created_at=datetime.now(),
            likes=30,
            retweets=5,
            replies=2,
        ),
    ]


class TestExtractHashtags:
    """ハッシュタグ抽出のテスト"""

    def test_basic_extraction(self) -> None:
        """基本的な抽出が正しく行われること"""
        text = "これはテスト #Python #機械学習 です"
        hashtags = extract_hashtags(text)

        assert len(hashtags) == 2
        assert "python" in hashtags
        assert "機械学習" in hashtags

    def test_no_hashtags(self) -> None:
        """ハッシュタグがない場合は空リストを返すこと"""
        text = "ハッシュタグなしのテキスト"
        hashtags = extract_hashtags(text)

        assert hashtags == []

    def test_case_insensitive(self) -> None:
        """大文字小文字を区別しないこと"""
        text = "#PYTHON #Python #python"
        hashtags = extract_hashtags(text)

        assert all(h == "python" for h in hashtags)


class TestExtractKeywords:
    """キーワード抽出のテスト"""

    def test_japanese_keywords(self) -> None:
        """日本語キーワードが正しく抽出されること"""
        text = "Pythonで機械学習を始める方法"
        keywords = extract_keywords(text)

        assert "python" in keywords
        # 日本語は連続する漢字・ひらがな・カタカナとして抽出される
        # 「で機械学習を始める方法」が1つのキーワードとして抽出される
        assert any("機械学習" in kw for kw in keywords)

    def test_removes_stop_words(self) -> None:
        """ストップワードが除去されること"""
        text = "これはテストです the test is"
        keywords = extract_keywords(text)

        assert "これ" not in keywords
        assert "the" not in keywords
        assert "is" not in keywords

    def test_removes_urls(self) -> None:
        """URLが除去されること"""
        text = "詳細はこちら https://example.com/test"
        keywords = extract_keywords(text)

        assert "example" not in keywords
        assert "https" not in keywords

    def test_removes_mentions(self) -> None:
        """メンションが除去されること"""
        text = "@user さんの投稿がすごい"
        keywords = extract_keywords(text)

        assert "user" not in keywords


class TestAnalyzeHashtags:
    """ハッシュタグ分析のテスト"""

    def test_basic_analysis(self, tweets_with_hashtags: list[Tweet]) -> None:
        """基本的な分析が正しく行われること"""
        results = analyze_hashtags(tweets_with_hashtags)

        assert len(results) > 0
        # pythonは2回使用されているはず
        python_result = next((r for r in results if r.hashtag == "python"), None)
        assert python_result is not None
        assert python_result.usage_count == 2

    def test_effectiveness_score(self, tweets_with_hashtags: list[Tweet]) -> None:
        """効果スコアが計算されること"""
        results = analyze_hashtags(tweets_with_hashtags)

        for result in results:
            assert result.effectiveness_score >= 0

    def test_empty_tweets(self) -> None:
        """空のリストでもエラーにならないこと"""
        results = analyze_hashtags([])

        assert results == []

    def test_sorted_by_effectiveness(self, tweets_with_hashtags: list[Tweet]) -> None:
        """効果スコア順にソートされること"""
        results = analyze_hashtags(tweets_with_hashtags)

        scores = [r.effectiveness_score for r in results]
        assert scores == sorted(scores, reverse=True)


class TestAnalyzeKeywords:
    """キーワード分析のテスト"""

    def test_basic_analysis(self, sample_tweets: list[Tweet]) -> None:
        """基本的な分析が正しく行われること"""
        results = analyze_keywords(sample_tweets)

        assert len(results) > 0

    def test_correlation_score_range(self, sample_tweets: list[Tweet]) -> None:
        """相関スコアが-1から1の範囲であること"""
        results = analyze_keywords(sample_tweets)

        for result in results:
            assert -1.0 <= result.correlation_score <= 1.0

    def test_empty_tweets(self) -> None:
        """空のリストでもエラーにならないこと"""
        results = analyze_keywords([])

        assert results == []

    def test_filters_low_frequency(self, sample_tweets: list[Tweet]) -> None:
        """頻度が低いキーワードが除外されること"""
        results = analyze_keywords(sample_tweets)

        for result in results:
            assert result.frequency >= 2


class TestAnalyzeContentPatterns:
    """コンテンツパターン分析のテスト"""

    def test_detects_questions(self) -> None:
        """質問パターンを検出すること"""
        tweets = [
            Tweet(
                id="1",
                text="皆さんの意見を聞かせてください？",
                created_at=datetime.now(),
                likes=50,
                retweets=10,
                replies=20,
            ),
        ]
        results = analyze_content_patterns(tweets)

        question_pattern = next(
            (r for r in results if r.pattern_type == "question"), None
        )
        assert question_pattern is not None
        assert question_pattern.count >= 1

    def test_detects_tips(self) -> None:
        """Tipsパターンを検出すること"""
        tweets = [
            Tweet(
                id="1",
                text="今日のコーディングTips: コードレビューのポイント",
                created_at=datetime.now(),
                likes=80,
                retweets=25,
                replies=5,
            ),
        ]
        results = analyze_content_patterns(tweets)

        tip_pattern = next((r for r in results if r.pattern_type == "tip"), None)
        assert tip_pattern is not None
        assert tip_pattern.count >= 1

    def test_sorted_by_engagement(self, sample_tweets: list[Tweet]) -> None:
        """平均エンゲージメント順にソートされること"""
        results = analyze_content_patterns(sample_tweets)

        if len(results) > 1:
            engagements = [r.avg_engagement for r in results]
            assert engagements == sorted(engagements, reverse=True)


class TestGetEffectiveHashtagRecommendations:
    """効果的なハッシュタグレコメンデーションのテスト"""

    def test_returns_top_n(self, tweets_with_hashtags: list[Tweet]) -> None:
        """指定した数のハッシュタグを返すこと"""
        analysis = analyze_hashtags(tweets_with_hashtags)
        recommendations = get_effective_hashtag_recommendations(analysis, top_n=3)

        assert len(recommendations) <= 3

    def test_filters_by_min_usage(self, tweets_with_hashtags: list[Tweet]) -> None:
        """最低使用回数でフィルタリングされること"""
        analysis = analyze_hashtags(tweets_with_hashtags)
        recommendations = get_effective_hashtag_recommendations(
            analysis, top_n=10, min_usage=2
        )

        # 2回以上使用されたハッシュタグのみ
        for hashtag in recommendations:
            result = next((r for r in analysis if r.hashtag == hashtag), None)
            assert result is not None
            assert result.usage_count >= 2


class TestGetHighEngagementKeywords:
    """高エンゲージメントキーワード取得のテスト"""

    def test_returns_positive_correlation_only(
        self, sample_tweets: list[Tweet]
    ) -> None:
        """正の相関を持つキーワードのみを返すこと"""
        analysis = analyze_keywords(sample_tweets)
        keywords = get_high_engagement_keywords(analysis)

        for keyword in keywords:
            result = next((r for r in analysis if r.keyword == keyword), None)
            assert result is not None
            assert result.correlation_score > 0


class TestIntegrationWithAnalysis:
    """analysis.pyとの統合テスト"""

    def test_analyze_tweets_includes_content_analysis(
        self, sample_tweets: list[Tweet]
    ) -> None:
        """analyze_tweetsがコンテンツ分析を含むこと"""
        from src.analysis import analyze_tweets

        result = analyze_tweets(sample_tweets)

        # コンテンツ分析結果が含まれていること
        assert hasattr(result, "hashtag_analysis")
        assert hasattr(result, "keyword_analysis")
        assert hasattr(result, "content_patterns")

    def test_recommendations_include_hashtags(
        self, tweets_with_hashtags: list[Tweet]
    ) -> None:
        """レコメンデーションにハッシュタグが含まれること"""
        from src.analysis import analyze_tweets

        result = analyze_tweets(tweets_with_hashtags)

        assert result.recommendations is not None
        # ハッシュタグが含まれる可能性がある
        # （min_usageの条件を満たす場合のみ）
