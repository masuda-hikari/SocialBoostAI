"""
YouTube分析モジュール

YouTube動画を分析し、エンゲージメント指標・時間帯分析・
タグ分析・カテゴリ分析・コンテンツパターン分析を提供する。
"""

import logging
import re
from collections import defaultdict
from datetime import UTC, datetime
from typing import Optional

from .models import (
    ContentPattern,
    HourlyEngagement,
    PostRecommendation,
    YouTubeAnalysisResult,
    YouTubeCategoryAnalysis,
    YouTubeEngagementMetrics,
    YouTubeShort,
    YouTubeTagAnalysis,
    YouTubeVideo,
)

logger = logging.getLogger(__name__)

# YouTubeカテゴリ名マッピング
YOUTUBE_CATEGORIES = {
    "1": "映画とアニメ",
    "2": "自動車と乗り物",
    "10": "音楽",
    "15": "ペットと動物",
    "17": "スポーツ",
    "18": "ショートムービー",
    "19": "旅行とイベント",
    "20": "ゲーム",
    "21": "動画ブログ",
    "22": "ブログ",
    "23": "コメディ",
    "24": "エンターテイメント",
    "25": "ニュースと政治",
    "26": "ハウツーとスタイル",
    "27": "教育",
    "28": "科学と技術",
    "29": "非営利団体と社会活動",
}


def calculate_youtube_metrics(
    videos: list[YouTubeVideo],
) -> YouTubeEngagementMetrics:
    """動画リストからエンゲージメント指標を計算

    Args:
        videos: 動画リスト

    Returns:
        YouTubeEngagementMetrics: エンゲージメント指標
    """
    if not videos:
        return YouTubeEngagementMetrics()

    total_views = sum(v.views for v in videos)
    total_likes = sum(v.likes for v in videos)
    total_comments = sum(v.comments for v in videos)
    total_shares = sum(v.shares or 0 for v in videos)

    video_count = len(videos)
    total_engagement = total_likes + total_comments

    # エンゲージメント率（ビューベース）
    engagement_rate = 0.0
    if total_views > 0:
        engagement_rate = (total_engagement / total_views) * 100

    # いいね率
    view_to_like_ratio = 0.0
    if total_views > 0:
        view_to_like_ratio = (total_likes / total_views) * 100

    # 視聴時間関連
    total_watch_time = sum(v.watch_time_minutes or 0 for v in videos)
    avg_duration = sum(v.avg_view_duration or 0 for v in videos) / video_count if video_count else 0
    avg_percentage = sum(v.avg_view_percentage or 0 for v in videos) / video_count if video_count else 0

    # Shorts視聴比率
    shorts_views = sum(v.views for v in videos if v.video_type == "short")
    shorts_rate = (shorts_views / total_views * 100) if total_views > 0 else 0

    return YouTubeEngagementMetrics(
        total_views=total_views,
        total_likes=total_likes,
        total_comments=total_comments,
        total_shares=total_shares,
        engagement_rate=round(engagement_rate, 4),
        avg_views_per_video=round(total_views / video_count, 2),
        avg_likes_per_video=round(total_likes / video_count, 2),
        avg_comments_per_video=round(total_comments / video_count, 2),
        view_to_like_ratio=round(view_to_like_ratio, 4),
        total_watch_time_hours=round(total_watch_time / 60, 2),
        avg_view_duration_seconds=round(avg_duration, 2),
        avg_view_percentage=round(avg_percentage, 2),
        shorts_view_rate=round(shorts_rate, 2),
    )


def analyze_youtube_hourly(
    videos: list[YouTubeVideo],
) -> list[HourlyEngagement]:
    """時間帯別エンゲージメントを分析

    Args:
        videos: 動画リスト

    Returns:
        list[HourlyEngagement]: 時間帯別エンゲージメントリスト（0-23時）
    """
    hourly_data: dict[int, dict[str, list[int]]] = defaultdict(
        lambda: {"views": [], "likes": [], "comments": []}
    )

    for video in videos:
        hour = video.published_at.hour
        hourly_data[hour]["views"].append(video.views)
        hourly_data[hour]["likes"].append(video.likes)
        hourly_data[hour]["comments"].append(video.comments)

    results: list[HourlyEngagement] = []
    for hour in range(24):
        data = hourly_data[hour]
        likes = data["likes"]
        views = data["views"]

        if likes:
            avg_likes = sum(likes) / len(likes)
            avg_views = sum(views) / len(views)
            # YouTubeではviewsも重要な指標
            total_engagement = avg_likes + avg_views / 100  # viewsをスケール調整
        else:
            avg_likes = 0.0
            avg_views = 0.0
            total_engagement = 0.0

        results.append(
            HourlyEngagement(
                hour=hour,
                avg_likes=round(avg_likes, 2),
                avg_retweets=round(avg_views, 2),  # YouTubeではviewsを表示
                post_count=len(likes),
                total_engagement=round(total_engagement, 2),
            )
        )

    return results


def find_youtube_best_hours(
    hourly_engagement: list[HourlyEngagement],
    top_n: int = 3,
    min_posts: int = 2,
) -> list[int]:
    """最適な投稿時間を特定

    Args:
        hourly_engagement: 時間帯別エンゲージメントリスト
        top_n: 上位何件を返すか
        min_posts: 最低投稿数（信頼性のため）

    Returns:
        list[int]: 最適な投稿時間（時）のリスト
    """
    valid_hours = [h for h in hourly_engagement if h.post_count >= min_posts]

    if not valid_hours:
        valid_hours = hourly_engagement

    sorted_hours = sorted(valid_hours, key=lambda h: h.total_engagement, reverse=True)
    return [h.hour for h in sorted_hours[:top_n]]


def get_top_youtube_videos(
    videos: list[YouTubeVideo],
    top_n: int = 5,
) -> list[YouTubeVideo]:
    """最もエンゲージメントの高い動画を取得

    Args:
        videos: 動画リスト
        top_n: 上位何件を返すか

    Returns:
        list[YouTubeVideo]: 上位動画リスト
    """
    sorted_videos = sorted(
        videos,
        key=lambda v: v.views + v.likes * 10 + v.comments * 50,
        reverse=True,
    )
    return sorted_videos[:top_n]


def get_top_youtube_shorts(
    videos: list[YouTubeVideo],
    top_n: int = 5,
) -> list[YouTubeShort]:
    """最もパフォーマンスの高いShortsを取得

    Args:
        videos: 動画リスト
        top_n: 上位何件を返すか

    Returns:
        list[YouTubeShort]: 上位Shortsリスト
    """
    shorts = [v for v in videos if v.video_type == "short"]
    sorted_shorts = sorted(
        shorts,
        key=lambda v: v.views + v.likes * 10 + v.comments * 50,
        reverse=True,
    )

    return [
        YouTubeShort(
            id=v.id,
            title=v.title,
            description=v.description,
            published_at=v.published_at,
            thumbnail_url=v.thumbnail_url,
            duration=v.duration,
            views=v.views,
            likes=v.likes,
            comments=v.comments,
            shares=v.shares,
            channel_id=v.channel_id,
        )
        for v in sorted_shorts[:top_n]
    ]


def analyze_youtube_tags(
    videos: list[YouTubeVideo],
) -> list[YouTubeTagAnalysis]:
    """タグの効果を分析

    Args:
        videos: 動画リスト

    Returns:
        list[YouTubeTagAnalysis]: タグ分析結果リスト
    """
    if not videos:
        return []

    tag_data: dict[str, dict] = defaultdict(
        lambda: {"count": 0, "views": 0, "likes": 0, "comments": 0}
    )

    # 全体の平均エンゲージメントを計算
    total_engagement = sum(v.likes + v.comments for v in videos)
    avg_engagement = total_engagement / len(videos) if videos else 0

    # タグごとのデータを集計
    for video in videos:
        for tag in video.tags:
            tag_lower = tag.lower()
            tag_data[tag_lower]["count"] += 1
            tag_data[tag_lower]["views"] += video.views
            tag_data[tag_lower]["likes"] += video.likes
            tag_data[tag_lower]["comments"] += video.comments

    # 分析結果を作成
    results: list[YouTubeTagAnalysis] = []
    for tag, data in tag_data.items():
        count = data["count"]
        total_views = data["views"]
        total_likes = data["likes"]
        tag_engagement = total_likes + data["comments"]
        tag_avg_engagement = tag_engagement / count if count > 0 else 0

        # 効果スコア = (タグ付き平均エンゲージメント / 全体平均) * 使用頻度補正
        frequency_factor = min(1.0, count / 3)
        effectiveness = (
            (tag_avg_engagement / avg_engagement * frequency_factor)
            if avg_engagement > 0
            else 0
        )

        results.append(
            YouTubeTagAnalysis(
                tag=tag,
                usage_count=count,
                total_views=total_views,
                total_likes=total_likes,
                avg_engagement=round(tag_avg_engagement, 2),
                effectiveness_score=round(effectiveness, 2),
            )
        )

    results.sort(key=lambda x: x.effectiveness_score, reverse=True)
    logger.info(f"{len(results)}個のYouTubeタグを分析しました")

    return results


def analyze_youtube_categories(
    videos: list[YouTubeVideo],
) -> list[YouTubeCategoryAnalysis]:
    """カテゴリ別パフォーマンスを分析

    Args:
        videos: 動画リスト

    Returns:
        list[YouTubeCategoryAnalysis]: カテゴリ分析結果リスト
    """
    if not videos:
        return []

    category_data: dict[str, dict] = defaultdict(
        lambda: {"count": 0, "views": 0, "likes": 0, "comments": 0}
    )

    for video in videos:
        if not video.category_id:
            continue

        cat_id = video.category_id
        category_data[cat_id]["count"] += 1
        category_data[cat_id]["views"] += video.views
        category_data[cat_id]["likes"] += video.likes
        category_data[cat_id]["comments"] += video.comments

    results: list[YouTubeCategoryAnalysis] = []
    for cat_id, data in category_data.items():
        count = data["count"]
        total_views = data["views"]
        total_likes = data["likes"]
        cat_engagement = total_likes + data["comments"]
        avg_engagement = cat_engagement / count if count > 0 else 0

        cat_name = YOUTUBE_CATEGORIES.get(cat_id, f"カテゴリ{cat_id}")

        results.append(
            YouTubeCategoryAnalysis(
                category_id=cat_id,
                category_name=cat_name,
                video_count=count,
                total_views=total_views,
                avg_engagement=round(avg_engagement, 2),
            )
        )

    results.sort(key=lambda x: x.avg_engagement, reverse=True)
    logger.info(f"{len(results)}個のYouTubeカテゴリを分析しました")

    return results


# YouTubeコンテンツパターン検出用
YOUTUBE_PATTERNS = {
    "tutorial": [
        r"how to",
        r"やり方",
        r"方法",
        r"tutorial",
        r"解説",
        r"講座",
        r"入門",
        r"beginner",
        r"初心者",
        r"learn",
        r"教え",
    ],
    "vlog": [
        r"vlog",
        r"ブログ",
        r"日常",
        r"day in",
        r"一日",
        r"ルーティン",
        r"routine",
    ],
    "review": [
        r"review",
        r"レビュー",
        r"開封",
        r"unboxing",
        r"使ってみた",
        r"買ってみた",
        r"紹介",
    ],
    "challenge": [
        r"challenge",
        r"チャレンジ",
        r"やってみた",
        r"試してみた",
        r"検証",
    ],
    "ranking": [
        r"top \d+",
        r"best \d+",
        r"ランキング",
        r"おすすめ\d+選",
        r"〇選",
    ],
    "live": [
        r"live",
        r"ライブ",
        r"生配信",
        r"生放送",
        r"stream",
    ],
    "shorts": [
        r"#shorts",
        r"short",
        r"ショート",
    ],
    "engagement_bait": [
        r"いいね",
        r"チャンネル登録",
        r"subscribe",
        r"コメント",
        r"通知",
        r"bell",
        r"part \d",
        r"パート\d",
        r"続き",
    ],
}


def analyze_youtube_patterns(
    videos: list[YouTubeVideo],
) -> list[ContentPattern]:
    """YouTubeコンテンツパターンを分析

    Args:
        videos: 動画リスト

    Returns:
        list[ContentPattern]: コンテンツパターン分析結果リスト
    """
    if not videos:
        return []

    pattern_data: dict[str, dict] = {
        pattern_type: {"count": 0, "total_engagement": 0, "total_views": 0, "examples": []}
        for pattern_type in YOUTUBE_PATTERNS.keys()
    }

    for video in videos:
        # タイトルと説明を結合して検索
        text = f"{video.title or ''} {video.description or ''}"
        if not text.strip():
            continue

        engagement = video.likes + video.comments

        for pattern_type, patterns in YOUTUBE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    data = pattern_data[pattern_type]
                    data["count"] += 1
                    data["total_engagement"] += engagement
                    data["total_views"] += video.views
                    if len(data["examples"]) < 3:
                        data["examples"].append(video.title[:100])
                    break

    results: list[ContentPattern] = []
    for pattern_type, data in pattern_data.items():
        count = data["count"]
        if count == 0:
            continue

        avg_engagement = data["total_engagement"] / count

        results.append(
            ContentPattern(
                pattern_type=pattern_type,
                count=count,
                avg_engagement=round(avg_engagement, 2),
                example_posts=data["examples"],
            )
        )

    results.sort(key=lambda x: x.avg_engagement, reverse=True)
    logger.info(f"{len(results)}個のYouTubeコンテンツパターンを分析しました")

    return results


def analyze_video_duration(
    videos: list[YouTubeVideo],
) -> tuple[float, Optional[str], dict[str, float]]:
    """動画の長さを分析

    Args:
        videos: 動画リスト

    Returns:
        tuple[float, Optional[str], dict[str, float]]:
            - 平均動画長（秒）
            - 最適な長さの範囲
            - 長さ別エンゲージメント
    """
    if not videos:
        return 0.0, None, {}

    # 長さ区分（YouTubeは長い動画が多いので区分を調整）
    duration_bins = {
        "0-5min": {"count": 0, "engagement": 0, "views": 0},
        "5-10min": {"count": 0, "engagement": 0, "views": 0},
        "10-20min": {"count": 0, "engagement": 0, "views": 0},
        "20min+": {"count": 0, "engagement": 0, "views": 0},
    }

    total_duration = 0
    for video in videos:
        # Shortsは除外
        if video.video_type == "short":
            continue

        total_duration += video.duration
        engagement = video.likes + video.comments

        if video.duration <= 300:  # 5分
            bin_key = "0-5min"
        elif video.duration <= 600:  # 10分
            bin_key = "5-10min"
        elif video.duration <= 1200:  # 20分
            bin_key = "10-20min"
        else:
            bin_key = "20min+"

        duration_bins[bin_key]["count"] += 1
        duration_bins[bin_key]["engagement"] += engagement
        duration_bins[bin_key]["views"] += video.views

    # 通常動画のみでカウント
    regular_videos = [v for v in videos if v.video_type != "short"]
    avg_duration = total_duration / len(regular_videos) if regular_videos else 0

    # 各区分の平均エンゲージメントを計算
    duration_engagement = {}
    for bin_key, data in duration_bins.items():
        if data["count"] > 0:
            duration_engagement[bin_key] = data["engagement"] / data["count"]
        else:
            duration_engagement[bin_key] = 0.0

    # 最適な長さを判定
    best_duration = max(
        duration_engagement.items(),
        key=lambda x: x[1] if duration_bins[x[0]]["count"] >= 2 else 0,
        default=("10-20min", 0),
    )[0]

    return avg_duration, best_duration, duration_engagement


def analyze_shorts_vs_videos(
    videos: list[YouTubeVideo],
) -> Optional[dict]:
    """Shorts vs 通常動画のパフォーマンス比較

    Args:
        videos: 動画リスト

    Returns:
        Optional[dict]: 比較結果
    """
    shorts = [v for v in videos if v.video_type == "short"]
    regular = [v for v in videos if v.video_type != "short"]

    if not shorts or not regular:
        return None

    shorts_avg_views = sum(v.views for v in shorts) / len(shorts)
    shorts_avg_engagement = sum(v.likes + v.comments for v in shorts) / len(shorts)
    regular_avg_views = sum(v.views for v in regular) / len(regular)
    regular_avg_engagement = sum(v.likes + v.comments for v in regular) / len(regular)

    return {
        "shorts_count": len(shorts),
        "shorts_avg_views": round(shorts_avg_views, 2),
        "shorts_avg_engagement": round(shorts_avg_engagement, 2),
        "regular_count": len(regular),
        "regular_avg_views": round(regular_avg_views, 2),
        "regular_avg_engagement": round(regular_avg_engagement, 2),
        "views_ratio": round(shorts_avg_views / regular_avg_views, 2) if regular_avg_views > 0 else 0,
        "engagement_ratio": round(shorts_avg_engagement / regular_avg_engagement, 2) if regular_avg_engagement > 0 else 0,
    }


def _generate_youtube_recommendations(
    metrics: YouTubeEngagementMetrics,
    best_hours: list[int],
    tag_analysis: list[YouTubeTagAnalysis],
    category_analysis: list[YouTubeCategoryAnalysis],
    content_patterns: list[ContentPattern],
    best_duration: Optional[str],
    shorts_comparison: Optional[dict],
) -> PostRecommendation:
    """YouTubeレコメンデーションを生成

    Args:
        metrics: エンゲージメント指標
        best_hours: 最適な投稿時間
        tag_analysis: タグ分析結果
        category_analysis: カテゴリ分析結果
        content_patterns: コンテンツパターン分析結果
        best_duration: 最適な動画長
        shorts_comparison: Shorts vs 動画比較結果

    Returns:
        PostRecommendation: 投稿レコメンデーション
    """
    # 効果的なタグを取得
    effective_tags = [t.tag for t in tag_analysis[:5] if t.usage_count >= 2]

    # 理由の説明を生成
    hour_strs = [f"{h}時" for h in best_hours]
    hours_text = "、".join(hour_strs)

    reasoning_parts = [
        f"YouTube分析の結果、{hours_text}の投稿が最もエンゲージメントが高い傾向にあります。",
        f"平均視聴数は{metrics.avg_views_per_video}、",
        f"平均いいね数は{metrics.avg_likes_per_video}、",
        f"いいね率（いいね/視聴）は{metrics.view_to_like_ratio}%です。",
    ]

    if best_duration:
        reasoning_parts.append(f"最も効果的な動画の長さは「{best_duration}」です。")

    if effective_tags:
        reasoning_parts.append(
            f"効果的なタグ: {', '.join(effective_tags[:3])}。"
        )

    if category_analysis:
        top_category = category_analysis[0]
        reasoning_parts.append(
            f"最も効果的なカテゴリ: 「{top_category.category_name}」"
            f"（平均エンゲージメント: {top_category.avg_engagement}）。"
        )

    if content_patterns:
        best_pattern = content_patterns[0]
        pattern_names = {
            "tutorial": "チュートリアル/解説",
            "vlog": "Vlog/日常",
            "review": "レビュー/開封",
            "challenge": "チャレンジ",
            "ranking": "ランキング/まとめ",
            "live": "ライブ配信",
            "shorts": "Shorts",
            "engagement_bait": "エンゲージメント促進",
        }
        pattern_name = pattern_names.get(
            best_pattern.pattern_type, best_pattern.pattern_type
        )
        reasoning_parts.append(
            f"最も効果的なコンテンツ形式は「{pattern_name}」"
            f"（平均エンゲージメント: {best_pattern.avg_engagement}）です。"
        )

    if shorts_comparison:
        if shorts_comparison["engagement_ratio"] > 1.2:
            reasoning_parts.append(
                f"Shortsは通常動画より{shorts_comparison['engagement_ratio']}倍のエンゲージメントがあります。"
            )
        elif shorts_comparison["engagement_ratio"] < 0.8:
            reasoning_parts.append(
                "通常動画の方がエンゲージメントが高い傾向です。"
            )

    # コンテンツアイデア生成
    content_ideas = []
    if content_patterns:
        for pattern in content_patterns[:3]:
            pattern_names = {
                "tutorial": "チュートリアル/解説動画を投稿する",
                "vlog": "Vlog形式の動画を試す",
                "review": "レビュー/開封動画を作成する",
                "challenge": "チャレンジ動画に挑戦する",
                "ranking": "ランキング/まとめ動画を作成する",
                "live": "ライブ配信を行う",
                "shorts": "Shortsを積極的に活用する",
                "engagement_bait": "シリーズ物の動画を作成する",
            }
            idea = pattern_names.get(pattern.pattern_type)
            if idea and idea not in content_ideas:
                content_ideas.append(idea)

    return PostRecommendation(
        best_hours=best_hours,
        suggested_hashtags=effective_tags,
        content_ideas=content_ideas,
        reasoning="".join(reasoning_parts),
    )


def analyze_youtube_videos(
    videos: list[YouTubeVideo],
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
) -> YouTubeAnalysisResult:
    """YouTube動画を総合分析

    Args:
        videos: 動画リスト
        period_start: 分析期間開始
        period_end: 分析期間終了

    Returns:
        YouTubeAnalysisResult: 分析結果
    """
    if not videos:
        now = datetime.now(UTC)
        return YouTubeAnalysisResult(
            period_start=period_start or now,
            period_end=period_end or now,
            total_videos=0,
            metrics=YouTubeEngagementMetrics(),
        )

    # 期間を決定
    all_dates = [v.published_at for v in videos]
    actual_start = period_start or min(all_dates)
    actual_end = period_end or max(all_dates)

    # 各分析を実行
    metrics = calculate_youtube_metrics(videos)
    hourly_breakdown = analyze_youtube_hourly(videos)
    top_videos = get_top_youtube_videos(videos)
    top_shorts = get_top_youtube_shorts(videos)
    best_hours = find_youtube_best_hours(hourly_breakdown)

    # コンテンツ分析
    tag_results = analyze_youtube_tags(videos)
    category_results = analyze_youtube_categories(videos)
    pattern_results = analyze_youtube_patterns(videos)

    # 動画長分析
    avg_duration, best_duration, _ = analyze_video_duration(videos)
    shorts_comparison = analyze_shorts_vs_videos(videos)

    # Shorts/通常動画カウント
    shorts_count = len([v for v in videos if v.video_type == "short"])
    regular_count = len(videos) - shorts_count

    # レコメンデーション生成
    recommendations = _generate_youtube_recommendations(
        metrics, best_hours, tag_results, category_results, pattern_results, best_duration, shorts_comparison
    )

    logger.info(f"{len(videos)}件のYouTube動画を分析しました")

    return YouTubeAnalysisResult(
        period_start=actual_start,
        period_end=actual_end,
        total_videos=regular_count,
        total_shorts=shorts_count,
        metrics=metrics,
        hourly_breakdown=hourly_breakdown,
        top_performing_videos=top_videos,
        top_performing_shorts=top_shorts,
        recommendations=recommendations,
        tag_analysis=tag_results,
        category_analysis=category_results,
        content_patterns=pattern_results,
        avg_video_duration=round(avg_duration, 2),
        best_duration_range=best_duration,
        shorts_vs_video_performance=shorts_comparison,
    )
