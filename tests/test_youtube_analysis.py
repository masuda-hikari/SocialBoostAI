# -*- coding: utf-8 -*-
"""
YouTube分析モジュールのテスト
"""

from datetime import datetime, timezone

import pytest

from src.models import (
    YouTubeVideo,
    YouTubeShort,
    YouTubeEngagementMetrics,
    YouTubeTagAnalysis,
    YouTubeCategoryAnalysis,
    YouTubeAnalysisResult,
)
from src.youtube_analysis import (
    calculate_youtube_metrics,
    analyze_youtube_hourly,
    find_youtube_best_hours,
    get_top_youtube_videos,
    get_top_youtube_shorts,
    analyze_youtube_tags,
    analyze_youtube_categories,
    analyze_youtube_patterns,
    analyze_video_duration,
    analyze_shorts_vs_videos,
    analyze_youtube_videos,
)


@pytest.fixture
def sample_videos():
    """テスト用YouTube動画データ"""
    return [
        YouTubeVideo(
            id="video_1",
            title="チュートリアル動画：初心者向け解説",
            description="これはテスト動画です。初心者向けの解説動画。",
            published_at=datetime(2026, 1, 1, 18, 0, tzinfo=timezone.utc),
            duration=720,  # 12分
            views=25000,
            likes=1500,
            comments=50,
            video_type="video",
            category_id="26",  # ハウツーとスタイル
            tags=["tutorial", "beginner", "解説"],
            channel_id="UC_test_channel",
        ),
        YouTubeVideo(
            id="video_2",
            title="Vlog：一日の過ごし方",
            description="Day in my life ルーティン",
            published_at=datetime(2026, 1, 2, 17, 0, tzinfo=timezone.utc),
            duration=900,  # 15分
            views=50000,
            likes=3000,
            comments=120,
            video_type="video",
            category_id="22",  # ブログ
            tags=["vlog", "routine", "日常"],
            channel_id="UC_test_channel",
        ),
        YouTubeVideo(
            id="video_3",
            title="レビュー：新製品開封",
            description="Unboxing and review 開封レビュー",
            published_at=datetime(2026, 1, 3, 19, 0, tzinfo=timezone.utc),
            duration=600,  # 10分
            views=15000,
            likes=800,
            comments=30,
            video_type="video",
            category_id="28",  # 科学と技術
            tags=["review", "unboxing", "レビュー"],
            channel_id="UC_test_channel",
        ),
        YouTubeVideo(
            id="short_1",
            title="Short動画 #shorts",
            description="ショート動画テスト #shorts",
            published_at=datetime(2026, 1, 4, 12, 0, tzinfo=timezone.utc),
            duration=45,  # 45秒 = Short
            views=80000,
            likes=5000,
            comments=200,
            video_type="short",
            category_id="24",  # エンターテイメント
            tags=["shorts", "short"],
            channel_id="UC_test_channel",
        ),
        YouTubeVideo(
            id="short_2",
            title="Short チャレンジ #shorts",
            description="Challenge #shorts チャレンジ",
            published_at=datetime(2026, 1, 5, 20, 0, tzinfo=timezone.utc),
            duration=30,  # 30秒 = Short
            views=60000,
            likes=4000,
            comments=150,
            video_type="short",
            category_id="24",  # エンターテイメント
            tags=["shorts", "challenge"],
            channel_id="UC_test_channel",
        ),
    ]


class TestCalculateYouTubeMetrics:
    """YouTubeエンゲージメント指標計算のテスト"""

    def test_basic_calculation(self, sample_videos):
        """基本的な計算が正しいか"""
        metrics = calculate_youtube_metrics(sample_videos)

        assert isinstance(metrics, YouTubeEngagementMetrics)
        assert metrics.total_views == 230000  # 25000 + 50000 + 15000 + 80000 + 60000
        assert metrics.total_likes == 14300  # 1500 + 3000 + 800 + 5000 + 4000
        assert metrics.total_comments == 550  # 50 + 120 + 30 + 200 + 150

    def test_engagement_rate(self, sample_videos):
        """エンゲージメント率が正しく計算されるか"""
        metrics = calculate_youtube_metrics(sample_videos)

        # (likes + comments) / views * 100
        expected_rate = (14300 + 550) / 230000 * 100
        assert abs(metrics.engagement_rate - expected_rate) < 0.01

    def test_view_to_like_ratio(self, sample_videos):
        """いいね率が正しく計算されるか"""
        metrics = calculate_youtube_metrics(sample_videos)

        expected_ratio = 14300 / 230000 * 100
        assert abs(metrics.view_to_like_ratio - expected_ratio) < 0.01

    def test_empty_videos(self):
        """空リストで正しく処理されるか"""
        metrics = calculate_youtube_metrics([])

        assert metrics.total_views == 0
        assert metrics.total_likes == 0
        assert metrics.engagement_rate == 0.0


class TestAnalyzeYouTubeHourly:
    """時間帯別分析のテスト"""

    def test_hourly_analysis(self, sample_videos):
        """時間帯別分析が正しく行われるか"""
        hourly = analyze_youtube_hourly(sample_videos)

        assert len(hourly) == 24
        # 18時に投稿がある
        hour_18 = next(h for h in hourly if h.hour == 18)
        assert hour_18.post_count >= 1

    def test_empty_videos(self):
        """空リストで正しく処理されるか"""
        hourly = analyze_youtube_hourly([])

        assert len(hourly) == 24
        for h in hourly:
            assert h.post_count == 0


class TestFindYouTubeBestHours:
    """最適投稿時間のテスト"""

    def test_find_best_hours(self, sample_videos):
        """最適時間が正しく特定されるか"""
        hourly = analyze_youtube_hourly(sample_videos)
        best_hours = find_youtube_best_hours(hourly, top_n=3)

        assert len(best_hours) <= 3
        assert all(0 <= h <= 23 for h in best_hours)


class TestGetTopYouTubeVideos:
    """トップ動画取得のテスト"""

    def test_get_top_videos(self, sample_videos):
        """トップ動画が正しく取得されるか"""
        top = get_top_youtube_videos(sample_videos, top_n=3)

        assert len(top) == 3
        # ソート順が正しいか（エンゲージメントが高い順）
        for i in range(len(top) - 1):
            score_i = top[i].views + top[i].likes * 10 + top[i].comments * 50
            score_next = top[i+1].views + top[i+1].likes * 10 + top[i+1].comments * 50
            assert score_i >= score_next


class TestGetTopYouTubeShorts:
    """トップShorts取得のテスト"""

    def test_get_top_shorts(self, sample_videos):
        """トップShortsが正しく取得されるか"""
        top = get_top_youtube_shorts(sample_videos, top_n=2)

        assert len(top) == 2
        # 全てShortであること
        for short in top:
            assert isinstance(short, YouTubeShort)


class TestAnalyzeYouTubeTags:
    """タグ分析のテスト"""

    def test_tag_analysis(self, sample_videos):
        """タグ分析が正しく行われるか"""
        tags = analyze_youtube_tags(sample_videos)

        assert len(tags) > 0
        assert all(isinstance(t, YouTubeTagAnalysis) for t in tags)

        # タグが小文字化されているか
        for tag in tags:
            assert tag.tag == tag.tag.lower()

    def test_empty_videos(self):
        """空リストで正しく処理されるか"""
        tags = analyze_youtube_tags([])
        assert len(tags) == 0


class TestAnalyzeYouTubeCategories:
    """カテゴリ分析のテスト"""

    def test_category_analysis(self, sample_videos):
        """カテゴリ分析が正しく行われるか"""
        categories = analyze_youtube_categories(sample_videos)

        assert len(categories) > 0
        assert all(isinstance(c, YouTubeCategoryAnalysis) for c in categories)

    def test_empty_videos(self):
        """空リストで正しく処理されるか"""
        categories = analyze_youtube_categories([])
        assert len(categories) == 0


class TestAnalyzeYouTubePatterns:
    """コンテンツパターン分析のテスト"""

    def test_pattern_detection(self, sample_videos):
        """パターンが正しく検出されるか"""
        patterns = analyze_youtube_patterns(sample_videos)

        # チュートリアル、vlog、reviewなどが検出されるはず
        pattern_types = [p.pattern_type for p in patterns]
        # 少なくとも1つは検出される
        assert len(patterns) > 0

    def test_empty_videos(self):
        """空リストで正しく処理されるか"""
        patterns = analyze_youtube_patterns([])
        assert len(patterns) == 0


class TestAnalyzeVideoDuration:
    """動画長分析のテスト"""

    def test_duration_analysis(self, sample_videos):
        """動画長分析が正しく行われるか"""
        avg_duration, best_range, engagement = analyze_video_duration(sample_videos)

        assert avg_duration > 0
        assert best_range in ["0-5min", "5-10min", "10-20min", "20min+", None]
        assert isinstance(engagement, dict)

    def test_empty_videos(self):
        """空リストで正しく処理されるか"""
        avg_duration, best_range, engagement = analyze_video_duration([])

        assert avg_duration == 0.0
        assert best_range is None
        assert engagement == {}


class TestAnalyzeShortsVsVideos:
    """Shorts vs 通常動画比較のテスト"""

    def test_comparison(self, sample_videos):
        """比較が正しく行われるか"""
        comparison = analyze_shorts_vs_videos(sample_videos)

        assert comparison is not None
        assert "shorts_count" in comparison
        assert "regular_count" in comparison
        assert comparison["shorts_count"] == 2
        assert comparison["regular_count"] == 3

    def test_no_shorts(self):
        """Shortsがない場合"""
        videos = [
            YouTubeVideo(
                id="v1",
                title="Video",
                published_at=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
                duration=600,
                views=1000,
                likes=100,
                comments=10,
                video_type="video",
            )
        ]
        comparison = analyze_shorts_vs_videos(videos)
        assert comparison is None


class TestAnalyzeYouTubeVideos:
    """総合分析のテスト"""

    def test_full_analysis(self, sample_videos):
        """総合分析が正しく行われるか"""
        result = analyze_youtube_videos(sample_videos)

        assert isinstance(result, YouTubeAnalysisResult)
        assert result.total_videos == 3  # 通常動画
        assert result.total_shorts == 2  # Shorts
        assert result.metrics.total_views == 230000
        assert len(result.hourly_breakdown) == 24
        assert len(result.top_performing_videos) <= 5
        assert result.recommendations is not None

    def test_empty_videos(self):
        """空リストで正しく処理されるか"""
        result = analyze_youtube_videos([])

        assert result.total_videos == 0
        assert result.total_shorts == 0
        assert result.metrics.total_views == 0

    def test_with_period(self, sample_videos):
        """期間指定で正しく処理されるか"""
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 1, 31, tzinfo=timezone.utc)

        result = analyze_youtube_videos(sample_videos, period_start=start, period_end=end)

        assert result.period_start == start
        assert result.period_end == end
