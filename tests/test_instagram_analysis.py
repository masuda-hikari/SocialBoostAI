# -*- coding: utf-8 -*-
"""
Instagram分析機能のテスト
"""

from datetime import UTC, datetime, timedelta

import pytest

from src.instagram_analysis import (
    INSTAGRAM_PATTERNS,
    analyze_instagram_hashtags,
    analyze_instagram_hourly,
    analyze_instagram_patterns,
    analyze_instagram_posts,
    calculate_instagram_metrics,
    extract_instagram_hashtags,
    find_instagram_best_hours,
    get_top_instagram_posts,
    get_top_instagram_reels,
)
from src.models import (
    InstagramEngagementMetrics,
    InstagramPost,
    InstagramReel,
)


# フィクスチャ: サンプル投稿データ
@pytest.fixture
def sample_posts() -> list[InstagramPost]:
    """サンプルInstagram投稿を生成"""
    base_time = datetime.now(UTC)
    return [
        InstagramPost(
            id="post_1",
            caption="素敵なカフェを発見！ #cafe #tokyo #lifestyle",
            media_type="IMAGE",
            created_at=base_time - timedelta(hours=2),
            likes=150,
            comments=25,
            saves=30,
            shares=10,
            impressions=2000,
            reach=1500,
        ),
        InstagramPost(
            id="post_2",
            caption="新商品のご紹介です！ #fashion #newitem",
            media_type="CAROUSEL_ALBUM",
            created_at=base_time - timedelta(hours=5),
            likes=280,
            comments=45,
            saves=65,
            shares=20,
            impressions=3500,
            reach=2800,
        ),
        InstagramPost(
            id="post_3",
            caption="皆さんはどう思いますか？ #question",
            media_type="IMAGE",
            created_at=base_time - timedelta(hours=8),
            likes=95,
            comments=78,  # 質問形式でコメント多い
            saves=12,
            shares=5,
            impressions=1800,
            reach=1400,
        ),
        InstagramPost(
            id="post_4",
            caption="How to make perfect coffee ☕ #tutorial #coffee",
            media_type="VIDEO",
            created_at=base_time - timedelta(hours=12),
            likes=420,
            comments=55,
            saves=180,  # チュートリアルは保存多い
            shares=35,
            impressions=5500,
            reach=4200,
        ),
        InstagramPost(
            id="post_5",
            caption="Behind the scenes 🎬 #bts #photography",
            media_type="IMAGE",
            created_at=base_time - timedelta(hours=18),
            likes=200,
            comments=30,
            saves=25,
            shares=15,
            impressions=2500,
            reach=2000,
        ),
    ]


@pytest.fixture
def sample_reels() -> list[InstagramReel]:
    """サンプルリールを生成"""
    base_time = datetime.now(UTC)
    return [
        InstagramReel(
            id="reel_1",
            caption="30秒でわかる！コーヒーの淹れ方 #shorts #coffee",
            created_at=base_time - timedelta(days=1),
            likes=850,
            comments=95,
            saves=220,
            shares=150,
            plays=12000,
            reach=8000,
        ),
        InstagramReel(
            id="reel_2",
            caption="ダンスチャレンジ！ #dance #viral",
            created_at=base_time - timedelta(days=2),
            likes=1200,
            comments=180,
            saves=90,
            shares=350,
            plays=25000,
            reach=18000,
        ),
    ]


class TestCalculateInstagramMetrics:
    """Instagram指標計算のテスト"""

    def test_empty_posts(self):
        """空のリストで空の指標を返す"""
        result = calculate_instagram_metrics([])
        assert result.total_likes == 0
        assert result.total_comments == 0
        assert result.engagement_rate == 0.0

    def test_metrics_calculation(self, sample_posts):
        """指標が正しく計算される"""
        result = calculate_instagram_metrics(sample_posts, follower_count=10000)

        assert result.total_likes == 1145  # 150+280+95+420+200
        assert result.total_comments == 233  # 25+45+78+55+30
        assert result.total_saves == 312  # 30+65+12+180+25
        assert result.avg_likes_per_post == 229.0
        assert result.avg_comments_per_post == 46.6
        assert result.engagement_rate > 0

    def test_zero_followers(self, sample_posts):
        """フォロワー0でもエラーにならない"""
        result = calculate_instagram_metrics(sample_posts, follower_count=0)
        assert result.engagement_rate == 0.0


class TestAnalyzeInstagramHourly:
    """時間帯別分析のテスト"""

    def test_hourly_breakdown(self, sample_posts):
        """24時間分のデータが生成される"""
        result = analyze_instagram_hourly(sample_posts)
        assert len(result) == 24

    def test_post_count_per_hour(self, sample_posts):
        """投稿数が正しくカウントされる"""
        result = analyze_instagram_hourly(sample_posts)
        total_posts = sum(h.post_count for h in result)
        assert total_posts == len(sample_posts)


class TestFindInstagramBestHours:
    """最適投稿時間特定のテスト"""

    def test_returns_top_n(self, sample_posts):
        """指定した数の時間帯を返す"""
        hourly = analyze_instagram_hourly(sample_posts)
        result = find_instagram_best_hours(hourly, top_n=3)
        assert len(result) <= 3

    def test_all_hours_considered_with_low_min_posts(self, sample_posts):
        """min_posts=1で全時間帯を考慮"""
        hourly = analyze_instagram_hourly(sample_posts)
        result = find_instagram_best_hours(hourly, top_n=5, min_posts=1)
        assert len(result) == len(sample_posts)


class TestGetTopInstagramPosts:
    """トップ投稿取得のテスト"""

    def test_returns_top_n(self, sample_posts):
        """指定数の投稿を返す"""
        result = get_top_instagram_posts(sample_posts, top_n=3)
        assert len(result) == 3

    def test_sorted_by_engagement(self, sample_posts):
        """エンゲージメント順にソートされる"""
        result = get_top_instagram_posts(sample_posts, top_n=5)
        # 最初の投稿が最もエンゲージメントが高いはず
        assert result[0].id == "post_4"  # 420+55+180=655


class TestGetTopInstagramReels:
    """トップリール取得のテスト"""

    def test_returns_top_n(self, sample_reels):
        """指定数のリールを返す"""
        result = get_top_instagram_reels(sample_reels, top_n=2)
        assert len(result) == 2

    def test_sorted_by_engagement(self, sample_reels):
        """再生数込みでソートされる"""
        result = get_top_instagram_reels(sample_reels, top_n=2)
        # reel_2が最もエンゲージメントが高い（plays考慮）
        assert result[0].id == "reel_2"


class TestExtractInstagramHashtags:
    """ハッシュタグ抽出のテスト"""

    def test_extract_hashtags(self):
        """ハッシュタグが正しく抽出される"""
        caption = "素敵な一日 #happy #life #tokyo"
        result = extract_instagram_hashtags(caption)
        assert len(result) == 3
        assert "happy" in result
        assert "life" in result
        assert "tokyo" in result

    def test_empty_caption(self):
        """空のキャプションで空リストを返す"""
        result = extract_instagram_hashtags(None)
        assert result == []

    def test_no_hashtags(self):
        """ハッシュタグなしで空リストを返す"""
        result = extract_instagram_hashtags("素敵な一日でした")
        assert result == []


class TestAnalyzeInstagramHashtags:
    """ハッシュタグ分析のテスト"""

    def test_empty_posts(self):
        """空のリストで空の結果を返す"""
        result = analyze_instagram_hashtags([])
        assert result == []

    def test_hashtag_analysis(self, sample_posts):
        """ハッシュタグが正しく分析される"""
        result = analyze_instagram_hashtags(sample_posts)
        assert len(result) > 0
        # ソートされているか確認
        scores = [h.effectiveness_score for h in result]
        assert scores == sorted(scores, reverse=True)


class TestAnalyzeInstagramPatterns:
    """コンテンツパターン分析のテスト"""

    def test_empty_posts(self):
        """空のリストで空の結果を返す"""
        result = analyze_instagram_patterns([])
        assert result == []

    def test_pattern_detection(self, sample_posts):
        """パターンが検出される"""
        result = analyze_instagram_patterns(sample_posts)
        pattern_types = [p.pattern_type for p in result]

        # 質問形式が検出されるはず（post_3）
        assert "question" in pattern_types
        # チュートリアルが検出されるはず（post_4）
        assert "tutorial" in pattern_types
        # behind_scenesが検出されるはず（post_5）
        assert "behind_scenes" in pattern_types

    def test_sorted_by_engagement(self, sample_posts):
        """エンゲージメント順にソートされる"""
        result = analyze_instagram_patterns(sample_posts)
        engagements = [p.avg_engagement for p in result]
        assert engagements == sorted(engagements, reverse=True)


class TestAnalyzeInstagramPosts:
    """総合分析のテスト"""

    def test_empty_posts(self):
        """空のリストで空の結果を返す"""
        result = analyze_instagram_posts([])
        assert result.total_posts == 0
        assert result.total_reels == 0

    def test_full_analysis(self, sample_posts, sample_reels):
        """総合分析が実行される"""
        result = analyze_instagram_posts(
            posts=sample_posts,
            reels=sample_reels,
            follower_count=10000,
        )

        assert result.total_posts == 5
        assert result.total_reels == 2
        assert result.metrics.total_likes > 0
        assert len(result.hourly_breakdown) == 24
        assert len(result.top_performing_posts) <= 5
        assert len(result.top_performing_reels) <= 5
        assert result.recommendations is not None

    def test_period_auto_detection(self, sample_posts):
        """期間が自動検出される"""
        result = analyze_instagram_posts(sample_posts)
        assert result.period_start <= result.period_end

    def test_custom_period(self, sample_posts):
        """カスタム期間が設定される"""
        now = datetime.now(UTC)
        start = now - timedelta(days=7)
        result = analyze_instagram_posts(
            sample_posts,
            period_start=start,
            period_end=now,
        )
        assert result.period_start == start
        assert result.period_end == now


class TestInstagramPatterns:
    """パターン定義のテスト"""

    def test_patterns_defined(self):
        """必要なパターンが定義されている"""
        assert "question" in INSTAGRAM_PATTERNS
        assert "tutorial" in INSTAGRAM_PATTERNS
        assert "behind_scenes" in INSTAGRAM_PATTERNS
        assert "engagement_bait" in INSTAGRAM_PATTERNS
        assert "product" in INSTAGRAM_PATTERNS
