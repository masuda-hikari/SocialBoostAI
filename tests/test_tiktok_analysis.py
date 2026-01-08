# -*- coding: utf-8 -*-
"""
TikTok分析モジュールのテスト
"""

from datetime import datetime, timezone

import pytest

from src.models import (
    TikTokVideo,
    TikTokEngagementMetrics,
    TikTokSoundAnalysis,
    TikTokAnalysisResult,
)
from src.tiktok_analysis import (
    calculate_tiktok_metrics,
    analyze_tiktok_hourly,
    find_tiktok_best_hours,
    get_top_tiktok_videos,
    extract_tiktok_hashtags,
    analyze_tiktok_hashtags,
    analyze_tiktok_sounds,
    analyze_tiktok_patterns,
    analyze_video_duration,
    analyze_video_types,
    analyze_tiktok_videos,
)


@pytest.fixture
def sample_videos():
    """テスト用TikTok動画データ"""
    return [
        TikTokVideo(
            id="video_1",
            description="これはテスト動画です #fyp #viral #テスト",
            create_time=datetime(2026, 1, 1, 19, 0, tzinfo=timezone.utc),
            duration=25,
            likes=1500,
            comments=50,
            shares=30,
            views=25000,
            sound_id="sound_001",
            sound_name="Original Sound",
            is_original_sound=True,
            hashtags=["fyp", "viral", "テスト"],
        ),
        TikTokVideo(
            id="video_2",
            description="チャレンジに参加！ #challenge #tiktok",
            create_time=datetime(2026, 1, 2, 20, 0, tzinfo=timezone.utc),
            duration=15,
            likes=3000,
            comments=120,
            shares=80,
            views=50000,
            sound_id="sound_002",
            sound_name="Trending Beat",
            is_original_sound=False,
            hashtags=["challenge", "tiktok"],
        ),
        TikTokVideo(
            id="video_3",
            description="How to tutorial やり方解説 #tutorial #howto",
            create_time=datetime(2026, 1, 3, 21, 0, tzinfo=timezone.utc),
            duration=45,
            likes=800,
            comments=30,
            shares=20,
            views=15000,
            sound_id="sound_001",
            sound_name="Original Sound",
            is_original_sound=True,
            hashtags=["tutorial", "howto"],
        ),
        TikTokVideo(
            id="video_4",
            description="POV: あなたが主人公になったら #pov: #storytime",
            create_time=datetime(2026, 1, 4, 12, 0, tzinfo=timezone.utc),
            duration=60,
            likes=2200,
            comments=90,
            shares=50,
            views=35000,
            sound_id="sound_003",
            sound_name="Dramatic Music",
            is_original_sound=False,
            hashtags=["pov", "storytime"],
            video_type="video",
        ),
        TikTokVideo(
            id="video_5",
            description="デュエット動画 #duet with @creator",
            create_time=datetime(2026, 1, 5, 18, 0, tzinfo=timezone.utc),
            duration=30,
            likes=1200,
            comments=40,
            shares=25,
            views=20000,
            sound_id="sound_002",
            sound_name="Trending Beat",
            is_original_sound=False,
            hashtags=["duet"],
            video_type="duet",
        ),
    ]


class TestCalculateTikTokMetrics:
    """calculate_tiktok_metricsのテスト"""

    def test_calculate_metrics(self, sample_videos):
        """基本的な指標計算"""
        metrics = calculate_tiktok_metrics(sample_videos)

        assert isinstance(metrics, TikTokEngagementMetrics)
        assert metrics.total_views == 145000
        assert metrics.total_likes == 8700
        assert metrics.total_comments == 330
        assert metrics.total_shares == 205
        # エンゲージメント率 = (likes + comments + shares) / views * 100
        expected_rate = (8700 + 330 + 205) / 145000 * 100
        assert abs(metrics.engagement_rate - expected_rate) < 0.01

    def test_empty_videos(self):
        """空の動画リスト"""
        metrics = calculate_tiktok_metrics([])

        assert metrics.total_views == 0
        assert metrics.total_likes == 0
        assert metrics.engagement_rate == 0.0


class TestAnalyzeTikTokHourly:
    """analyze_tiktok_hourlyのテスト"""

    def test_hourly_analysis(self, sample_videos):
        """時間帯別分析"""
        hourly = analyze_tiktok_hourly(sample_videos)

        assert len(hourly) == 24
        # 19時の投稿を確認
        hour_19 = next(h for h in hourly if h.hour == 19)
        assert hour_19.post_count == 1
        assert hour_19.avg_likes == 1500

    def test_empty_videos(self):
        """空の動画リスト"""
        hourly = analyze_tiktok_hourly([])

        assert len(hourly) == 24
        for h in hourly:
            assert h.post_count == 0
            assert h.avg_likes == 0


class TestFindTikTokBestHours:
    """find_tiktok_best_hoursのテスト"""

    def test_find_best_hours(self, sample_videos):
        """最適時間帯の特定"""
        hourly = analyze_tiktok_hourly(sample_videos)
        best_hours = find_tiktok_best_hours(hourly, top_n=3, min_posts=1)

        assert len(best_hours) <= 3
        # 20時（challenge動画）がトップになるはず
        assert 20 in best_hours


class TestGetTopTikTokVideos:
    """get_top_tiktok_videosのテスト"""

    def test_get_top_videos(self, sample_videos):
        """上位動画の取得"""
        top = get_top_tiktok_videos(sample_videos, top_n=3)

        assert len(top) == 3
        # video_2（views=50000, likes=3000）がトップ
        assert top[0].id == "video_2"

    def test_top_n_exceeds_list(self, sample_videos):
        """top_nが動画数を超える場合"""
        top = get_top_tiktok_videos(sample_videos, top_n=10)

        assert len(top) == 5


class TestExtractTikTokHashtags:
    """extract_tiktok_hashtagsのテスト"""

    def test_extract_hashtags(self):
        """ハッシュタグ抽出"""
        text = "テスト投稿 #fyp #viral #tiktok"
        hashtags = extract_tiktok_hashtags(text)

        assert len(hashtags) == 3
        assert "fyp" in hashtags
        assert "viral" in hashtags
        assert "tiktok" in hashtags

    def test_empty_text(self):
        """空のテキスト"""
        hashtags = extract_tiktok_hashtags("")
        assert hashtags == []

    def test_none_text(self):
        """Noneのテキスト"""
        hashtags = extract_tiktok_hashtags(None)
        assert hashtags == []


class TestAnalyzeTikTokHashtags:
    """analyze_tiktok_hashtagsのテスト"""

    def test_analyze_hashtags(self, sample_videos):
        """ハッシュタグ分析"""
        analysis = analyze_tiktok_hashtags(sample_videos)

        assert len(analysis) > 0
        # fyp と viral は1回使用
        fyp_analysis = next((h for h in analysis if h.hashtag == "fyp"), None)
        assert fyp_analysis is not None
        assert fyp_analysis.usage_count == 1

    def test_empty_videos(self):
        """空の動画リスト"""
        analysis = analyze_tiktok_hashtags([])
        assert analysis == []


class TestAnalyzeTikTokSounds:
    """analyze_tiktok_soundsのテスト"""

    def test_analyze_sounds(self, sample_videos):
        """サウンド分析"""
        analysis = analyze_tiktok_sounds(sample_videos)

        assert len(analysis) > 0
        # sound_001 は2回使用
        sound_001 = next((s for s in analysis if s.sound_id == "sound_001"), None)
        assert sound_001 is not None
        assert sound_001.usage_count == 2
        assert sound_001.sound_name == "Original Sound"

    def test_empty_videos(self):
        """空の動画リスト"""
        analysis = analyze_tiktok_sounds([])
        assert analysis == []


class TestAnalyzeTikTokPatterns:
    """analyze_tiktok_patternsのテスト"""

    def test_analyze_patterns(self, sample_videos):
        """コンテンツパターン分析"""
        patterns = analyze_tiktok_patterns(sample_videos)

        assert len(patterns) > 0
        # tutorial パターンを検出
        tutorial = next((p for p in patterns if p.pattern_type == "tutorial"), None)
        assert tutorial is not None
        assert tutorial.count >= 1

    def test_empty_videos(self):
        """空の動画リスト"""
        patterns = analyze_tiktok_patterns([])
        assert patterns == []


class TestAnalyzeVideoDuration:
    """analyze_video_durationのテスト"""

    def test_analyze_duration(self, sample_videos):
        """動画長分析"""
        avg_duration, best_range, duration_engagement = analyze_video_duration(sample_videos)

        assert avg_duration > 0
        # 平均は (25 + 15 + 45 + 60 + 30) / 5 = 35秒
        assert abs(avg_duration - 35) < 0.1
        assert best_range in ["0-15s", "15-30s", "30-60s", "60s+"]
        assert len(duration_engagement) == 4

    def test_empty_videos(self):
        """空の動画リスト"""
        avg_duration, best_range, duration_engagement = analyze_video_duration([])

        assert avg_duration == 0.0
        assert best_range is None
        assert duration_engagement == {}


class TestAnalyzeVideoTypes:
    """analyze_video_typesのテスト"""

    def test_analyze_types(self, sample_videos):
        """動画タイプ分析"""
        duet_perf, stitch_perf = analyze_video_types(sample_videos)

        # video_5はduet
        assert duet_perf is not None
        assert duet_perf > 0
        # stitchはなし
        assert stitch_perf is None

    def test_empty_videos(self):
        """空の動画リスト"""
        duet_perf, stitch_perf = analyze_video_types([])

        assert duet_perf is None
        assert stitch_perf is None


class TestAnalyzeTikTokVideos:
    """analyze_tiktok_videosのテスト"""

    def test_full_analysis(self, sample_videos):
        """総合分析"""
        result = analyze_tiktok_videos(sample_videos)

        assert isinstance(result, TikTokAnalysisResult)
        assert result.total_videos == 5
        assert result.metrics.total_views == 145000
        assert len(result.hourly_breakdown) == 24
        assert len(result.top_performing_videos) <= 5
        assert result.recommendations is not None
        assert len(result.hashtag_analysis) > 0
        assert len(result.sound_analysis) > 0
        assert result.avg_video_duration > 0

    def test_empty_videos(self):
        """空の動画リスト"""
        result = analyze_tiktok_videos([])

        assert result.total_videos == 0
        assert result.metrics.total_views == 0

    def test_with_period(self, sample_videos):
        """期間指定の分析"""
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 1, 31, tzinfo=timezone.utc)
        result = analyze_tiktok_videos(sample_videos, period_start=start, period_end=end)

        assert result.period_start == start
        assert result.period_end == end
