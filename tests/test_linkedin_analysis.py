# -*- coding: utf-8 -*-
"""
LinkedIn分析モジュールのテスト
"""

from datetime import datetime, timezone

import pytest

from src.models import (
    LinkedInPost,
    LinkedInArticle,
    LinkedInEngagementMetrics,
    LinkedInAnalysisResult,
)
from src.linkedin_analysis import (
    calculate_linkedin_metrics,
    analyze_linkedin_hourly,
    analyze_linkedin_daily,
    find_linkedin_best_hours,
    find_linkedin_best_days,
    get_top_linkedin_posts,
    analyze_linkedin_hashtags,
    analyze_linkedin_patterns,
    analyze_media_type_performance,
    analyze_post_length,
    analyze_linkedin_posts,
)


@pytest.fixture
def sample_posts():
    """テスト用LinkedIn投稿データ"""
    return [
        LinkedInPost(
            id="post_1",
            text="This is my insight about leadership. 気づきを共有します。#leadership #management",
            created_at=datetime(2026, 1, 6, 9, 0, tzinfo=timezone.utc),  # 月曜日 9時
            visibility="PUBLIC",
            media_type="IMAGE",
            likes=150,
            comments=25,
            shares=30,
            clicks=80,
            impressions=5000,
            unique_impressions=4500,
            hashtags=["leadership", "management"],
        ),
        LinkedInPost(
            id="post_2",
            text="We're hiring! 採用情報です。#hiring #career",
            created_at=datetime(2026, 1, 7, 10, 0, tzinfo=timezone.utc),  # 火曜日 10時
            visibility="PUBLIC",
            media_type="NONE",
            likes=200,
            comments=45,
            shares=50,
            clicks=150,
            impressions=8000,
            unique_impressions=7000,
            hashtags=["hiring", "career"],
        ),
        LinkedInPost(
            id="post_3",
            text="5 tips for productivity. 生産性向上のコツ。#productivity #tips",
            created_at=datetime(2026, 1, 8, 11, 0, tzinfo=timezone.utc),  # 水曜日 11時
            visibility="PUBLIC",
            media_type="DOCUMENT",
            likes=180,
            comments=35,
            shares=40,
            clicks=120,
            impressions=6500,
            unique_impressions=6000,
            hashtags=["productivity", "tips"],
        ),
        LinkedInPost(
            id="post_4",
            text="What do you think about AI? どう思いますか？",
            created_at=datetime(2026, 1, 9, 14, 0, tzinfo=timezone.utc),  # 木曜日 14時
            visibility="PUBLIC",
            media_type="VIDEO",
            likes=300,
            comments=80,
            shares=60,
            clicks=100,
            impressions=10000,
            unique_impressions=9000,
            hashtags=["ai", "technology"],
        ),
        LinkedInPost(
            id="post_5",
            text="My career journey story. 私の経験をシェアします。",
            created_at=datetime(2026, 1, 10, 16, 0, tzinfo=timezone.utc),  # 金曜日 16時
            visibility="PUBLIC",
            media_type="IMAGE",
            likes=120,
            comments=20,
            shares=15,
            clicks=50,
            impressions=4000,
            unique_impressions=3500,
            hashtags=["career", "story"],
        ),
    ]


class TestCalculateLinkedInMetrics:
    """LinkedInエンゲージメント指標計算のテスト"""

    def test_basic_calculation(self, sample_posts):
        """基本的な計算が正しいか"""
        metrics = calculate_linkedin_metrics(sample_posts)

        assert isinstance(metrics, LinkedInEngagementMetrics)
        assert metrics.total_impressions == 33500  # 5000+8000+6500+10000+4000
        assert metrics.total_likes == 950  # 150+200+180+300+120
        assert metrics.total_comments == 205  # 25+45+35+80+20
        assert metrics.total_shares == 195  # 30+50+40+60+15
        assert metrics.total_clicks == 500  # 80+150+120+100+50

    def test_engagement_rate(self, sample_posts):
        """エンゲージメント率が正しく計算されるか"""
        metrics = calculate_linkedin_metrics(sample_posts)

        # (likes + comments + shares + clicks) / impressions * 100
        total_engagement = 950 + 205 + 195 + 500
        expected_rate = (total_engagement / 33500) * 100
        assert abs(metrics.engagement_rate - expected_rate) < 0.01

    def test_ctr(self, sample_posts):
        """CTRが正しく計算されるか"""
        metrics = calculate_linkedin_metrics(sample_posts)

        expected_ctr = (500 / 33500) * 100
        assert abs(metrics.click_through_rate - expected_ctr) < 0.01

    def test_virality_rate(self, sample_posts):
        """バイラリティ率が正しく計算されるか"""
        metrics = calculate_linkedin_metrics(sample_posts)

        expected_virality = (195 / 33500) * 100
        assert abs(metrics.virality_rate - expected_virality) < 0.01

    def test_empty_posts(self):
        """空リストで正しく処理されるか"""
        metrics = calculate_linkedin_metrics([])

        assert metrics.total_impressions == 0
        assert metrics.total_likes == 0
        assert metrics.engagement_rate == 0.0
        assert metrics.click_through_rate == 0.0


class TestAnalyzeLinkedInHourly:
    """時間帯別分析のテスト"""

    def test_hourly_analysis(self, sample_posts):
        """時間帯別分析が正しく行われるか"""
        hourly = analyze_linkedin_hourly(sample_posts)

        assert len(hourly) == 24
        # 9時に投稿がある
        hour_9 = next(h for h in hourly if h.hour == 9)
        assert hour_9.post_count >= 1

    def test_empty_posts(self):
        """空リストで正しく処理されるか"""
        hourly = analyze_linkedin_hourly([])

        assert len(hourly) == 24
        for h in hourly:
            assert h.post_count == 0


class TestAnalyzeLinkedInDaily:
    """曜日別分析のテスト（B2B特化）"""

    def test_daily_analysis(self, sample_posts):
        """曜日別分析が正しく行われるか"""
        daily = analyze_linkedin_daily(sample_posts)

        assert len(daily) == 7
        # 火曜日（weekday=1）に投稿がある
        tuesday = next(d for d in daily if d["weekday"] == 1)
        assert tuesday["post_count"] >= 1
        assert tuesday["weekday_name"] == "火曜日"

    def test_weekday_names(self, sample_posts):
        """曜日名が正しいか"""
        daily = analyze_linkedin_daily(sample_posts)

        expected_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
        for i, d in enumerate(daily):
            assert d["weekday_name"] == expected_names[i]

    def test_empty_posts(self):
        """空リストで正しく処理されるか"""
        daily = analyze_linkedin_daily([])

        assert len(daily) == 7
        for d in daily:
            assert d["post_count"] == 0


class TestFindLinkedInBestHours:
    """最適投稿時間のテスト"""

    def test_find_best_hours(self, sample_posts):
        """最適時間が正しく特定されるか"""
        hourly = analyze_linkedin_hourly(sample_posts)
        best_hours = find_linkedin_best_hours(hourly, top_n=3)

        assert len(best_hours) <= 3
        assert all(0 <= h <= 23 for h in best_hours)


class TestFindLinkedInBestDays:
    """最適投稿曜日のテスト（B2B特化）"""

    def test_find_best_days(self, sample_posts):
        """最適曜日が正しく特定されるか"""
        daily = analyze_linkedin_daily(sample_posts)
        best_days = find_linkedin_best_days(daily, top_n=3)

        assert len(best_days) <= 3
        # 日本語の曜日名が返される
        valid_days = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
        for day in best_days:
            assert day in valid_days


class TestGetTopLinkedInPosts:
    """トップ投稿取得のテスト"""

    def test_get_top_posts(self, sample_posts):
        """トップ投稿が正しく取得されるか"""
        top = get_top_linkedin_posts(sample_posts, top_n=3)

        assert len(top) == 3
        # ソート順が正しいか（エンゲージメントが高い順）
        for i in range(len(top) - 1):
            score_i = top[i].likes + top[i].comments * 5 + top[i].shares * 10 + (top[i].clicks or 0)
            score_next = top[i+1].likes + top[i+1].comments * 5 + top[i+1].shares * 10 + (top[i+1].clicks or 0)
            assert score_i >= score_next


class TestAnalyzeLinkedInHashtags:
    """ハッシュタグ分析のテスト"""

    def test_hashtag_analysis(self, sample_posts):
        """ハッシュタグ分析が正しく行われるか"""
        hashtags = analyze_linkedin_hashtags(sample_posts)

        assert len(hashtags) > 0
        # ハッシュタグが小文字化されているか
        for tag in hashtags:
            assert tag.hashtag == tag.hashtag.lower()

    def test_career_hashtag_count(self, sample_posts):
        """特定のハッシュタグが正しくカウントされるか"""
        hashtags = analyze_linkedin_hashtags(sample_posts)

        # "career"は2回使用されている
        career_tag = next((t for t in hashtags if t.hashtag == "career"), None)
        assert career_tag is not None
        assert career_tag.usage_count == 2

    def test_empty_posts(self):
        """空リストで正しく処理されるか"""
        hashtags = analyze_linkedin_hashtags([])
        assert len(hashtags) == 0


class TestAnalyzeLinkedInPatterns:
    """コンテンツパターン分析のテスト（B2B特化）"""

    def test_pattern_detection(self, sample_posts):
        """パターンが正しく検出されるか"""
        patterns = analyze_linkedin_patterns(sample_posts)

        # 少なくとも1つは検出される
        assert len(patterns) > 0
        pattern_types = [p.pattern_type for p in patterns]

        # 期待されるパターンが検出されるか
        # thought_leadership, career, tips, question, personal_storyなど
        assert len(pattern_types) > 0

    def test_question_pattern(self, sample_posts):
        """質問パターンが検出されるか"""
        patterns = analyze_linkedin_patterns(sample_posts)

        # "What do you think"を含む投稿があるので質問パターンが検出されるはず
        pattern_types = [p.pattern_type for p in patterns]
        assert "question" in pattern_types

    def test_tips_pattern(self, sample_posts):
        """Tipsパターンが検出されるか"""
        patterns = analyze_linkedin_patterns(sample_posts)

        # "5 tips"を含む投稿があるのでtipsパターンが検出されるはず
        pattern_types = [p.pattern_type for p in patterns]
        assert "tips" in pattern_types

    def test_empty_posts(self):
        """空リストで正しく処理されるか"""
        patterns = analyze_linkedin_patterns([])
        assert len(patterns) == 0


class TestAnalyzeMediaTypePerformance:
    """メディアタイプ別パフォーマンス分析のテスト"""

    def test_media_type_analysis(self, sample_posts):
        """メディアタイプ分析が正しく行われるか"""
        performance = analyze_media_type_performance(sample_posts)

        assert len(performance) > 0
        # 各メディアタイプがある
        assert "IMAGE" in performance
        assert "VIDEO" in performance
        assert "DOCUMENT" in performance
        assert "NONE" in performance

    def test_empty_posts(self):
        """空リストで正しく処理されるか"""
        performance = analyze_media_type_performance([])
        assert performance == {}


class TestAnalyzePostLength:
    """投稿文字数分析のテスト"""

    def test_post_length_analysis(self, sample_posts):
        """投稿文字数分析が正しく行われるか"""
        avg_length, length_performance = analyze_post_length(sample_posts)

        assert avg_length > 0
        assert len(length_performance) > 0

    def test_empty_posts(self):
        """空リストで正しく処理されるか"""
        avg_length, length_performance = analyze_post_length([])

        assert avg_length == 0.0
        assert length_performance == {}


class TestAnalyzeLinkedInPosts:
    """総合分析のテスト"""

    def test_full_analysis(self, sample_posts):
        """総合分析が正しく行われるか"""
        result = analyze_linkedin_posts(sample_posts)

        assert isinstance(result, LinkedInAnalysisResult)
        assert result.total_posts == 5
        assert result.metrics.total_impressions == 33500
        assert len(result.hourly_breakdown) == 24
        assert len(result.daily_breakdown) == 7
        assert len(result.top_performing_posts) <= 5
        assert result.recommendations is not None
        assert len(result.best_posting_days) > 0

    def test_empty_posts(self):
        """空リストで正しく処理されるか"""
        result = analyze_linkedin_posts([])

        assert result.total_posts == 0
        assert result.metrics.total_impressions == 0

    def test_with_period(self, sample_posts):
        """期間指定で正しく処理されるか"""
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 1, 31, tzinfo=timezone.utc)

        result = analyze_linkedin_posts(sample_posts, period_start=start, period_end=end)

        assert result.period_start == start
        assert result.period_end == end

    def test_with_articles(self, sample_posts):
        """記事付きで正しく処理されるか"""
        articles = [
            LinkedInArticle(
                id="article_1",
                title="テスト記事",
                published_at=datetime(2026, 1, 7, 10, 0, tzinfo=timezone.utc),
                views=5000,
                likes=100,
                comments=30,
                shares=20,
            ),
        ]

        result = analyze_linkedin_posts(sample_posts, articles=articles)

        assert result.total_articles == 1
        assert len(result.top_performing_articles) == 1
