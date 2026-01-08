"""
TikTok分析モジュール

TikTok動画を分析し、エンゲージメント指標・時間帯分析・
ハッシュタグ分析・サウンド分析・コンテンツパターン分析を提供する。
"""

import logging
import re
from collections import defaultdict
from datetime import UTC, datetime
from typing import Optional

from .models import (
    ContentPattern,
    HashtagAnalysis,
    HourlyEngagement,
    PostRecommendation,
    TikTokAnalysisResult,
    TikTokEngagementMetrics,
    TikTokSoundAnalysis,
    TikTokVideo,
)

logger = logging.getLogger(__name__)


def calculate_tiktok_metrics(
    videos: list[TikTokVideo],
) -> TikTokEngagementMetrics:
    """動画リストからエンゲージメント指標を計算

    Args:
        videos: 動画リスト

    Returns:
        TikTokEngagementMetrics: エンゲージメント指標
    """
    if not videos:
        return TikTokEngagementMetrics()

    total_views = sum(v.views for v in videos)
    total_likes = sum(v.likes for v in videos)
    total_comments = sum(v.comments for v in videos)
    total_shares = sum(v.shares for v in videos)
    total_saves = sum(v.saves or 0 for v in videos)

    video_count = len(videos)
    total_engagement = total_likes + total_comments + total_shares

    # エンゲージメント率（ビューベース）
    engagement_rate = 0.0
    if total_views > 0:
        engagement_rate = (total_engagement / total_views) * 100

    # いいね率
    view_to_like_ratio = 0.0
    if total_views > 0:
        view_to_like_ratio = (total_likes / total_views) * 100

    return TikTokEngagementMetrics(
        total_views=total_views,
        total_likes=total_likes,
        total_comments=total_comments,
        total_shares=total_shares,
        total_saves=total_saves,
        engagement_rate=round(engagement_rate, 4),
        avg_views_per_video=round(total_views / video_count, 2),
        avg_likes_per_video=round(total_likes / video_count, 2),
        avg_comments_per_video=round(total_comments / video_count, 2),
        avg_shares_per_video=round(total_shares / video_count, 2),
        view_to_like_ratio=round(view_to_like_ratio, 4),
    )


def analyze_tiktok_hourly(
    videos: list[TikTokVideo],
) -> list[HourlyEngagement]:
    """時間帯別エンゲージメントを分析

    Args:
        videos: 動画リスト

    Returns:
        list[HourlyEngagement]: 時間帯別エンゲージメントリスト（0-23時）
    """
    hourly_data: dict[int, dict[str, list[int]]] = defaultdict(
        lambda: {"views": [], "likes": [], "comments": [], "shares": []}
    )

    for video in videos:
        hour = video.create_time.hour
        hourly_data[hour]["views"].append(video.views)
        hourly_data[hour]["likes"].append(video.likes)
        hourly_data[hour]["comments"].append(video.comments)
        hourly_data[hour]["shares"].append(video.shares)

    results: list[HourlyEngagement] = []
    for hour in range(24):
        data = hourly_data[hour]
        likes = data["likes"]
        views = data["views"]

        if likes:
            avg_likes = sum(likes) / len(likes)
            avg_views = sum(views) / len(views)
            # TikTokではviewsも重要な指標
            total_engagement = avg_likes + avg_views / 100  # viewsをスケール調整
        else:
            avg_likes = 0.0
            avg_views = 0.0
            total_engagement = 0.0

        results.append(
            HourlyEngagement(
                hour=hour,
                avg_likes=round(avg_likes, 2),
                avg_retweets=round(avg_views, 2),  # TikTokではviewsを表示
                post_count=len(likes),
                total_engagement=round(total_engagement, 2),
            )
        )

    return results


def find_tiktok_best_hours(
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


def get_top_tiktok_videos(
    videos: list[TikTokVideo],
    top_n: int = 5,
) -> list[TikTokVideo]:
    """最もエンゲージメントの高い動画を取得

    Args:
        videos: 動画リスト
        top_n: 上位何件を返すか

    Returns:
        list[TikTokVideo]: 上位動画リスト
    """
    sorted_videos = sorted(
        videos,
        key=lambda v: v.views + v.likes * 10 + v.comments * 50 + v.shares * 100,
        reverse=True,
    )
    return sorted_videos[:top_n]


def extract_tiktok_hashtags(description: Optional[str]) -> list[str]:
    """説明からハッシュタグを抽出

    Args:
        description: 動画説明テキスト

    Returns:
        list[str]: ハッシュタグリスト（#なし）
    """
    if not description:
        return []

    pattern = r"#([^\s#]+)"
    matches = re.findall(pattern, description)
    return [m.lower() for m in matches]


def analyze_tiktok_hashtags(
    videos: list[TikTokVideo],
) -> list[HashtagAnalysis]:
    """ハッシュタグの効果を分析

    Args:
        videos: 動画リスト

    Returns:
        list[HashtagAnalysis]: ハッシュタグ分析結果リスト
    """
    if not videos:
        return []

    hashtag_data: dict[str, dict] = defaultdict(
        lambda: {"count": 0, "views": 0, "likes": 0, "comments": 0, "shares": 0}
    )

    # 全体の平均エンゲージメントを計算
    total_engagement = sum(
        v.likes + v.comments + v.shares for v in videos
    )
    avg_engagement = total_engagement / len(videos) if videos else 0

    # ハッシュタグごとのデータを集計
    for video in videos:
        # 動画のハッシュタグを使用（既に抽出済みの場合）または説明から抽出
        hashtags = video.hashtags or extract_tiktok_hashtags(video.description)
        for tag in hashtags:
            hashtag_data[tag]["count"] += 1
            hashtag_data[tag]["views"] += video.views
            hashtag_data[tag]["likes"] += video.likes
            hashtag_data[tag]["comments"] += video.comments
            hashtag_data[tag]["shares"] += video.shares

    # 分析結果を作成
    results: list[HashtagAnalysis] = []
    for hashtag, data in hashtag_data.items():
        count = data["count"]
        total_views = data["views"]
        total_likes = data["likes"]
        total_comments = data["comments"]
        tag_engagement = total_likes + total_comments + data["shares"]
        tag_avg_engagement = tag_engagement / count if count > 0 else 0

        # 効果スコア = (タグ付き平均エンゲージメント / 全体平均) * 使用頻度補正
        frequency_factor = min(1.0, count / 3)
        effectiveness = (
            (tag_avg_engagement / avg_engagement * frequency_factor)
            if avg_engagement > 0
            else 0
        )

        results.append(
            HashtagAnalysis(
                hashtag=hashtag,
                usage_count=count,
                total_likes=total_likes,
                total_retweets=total_comments,  # TikTok: commentsをretweets枠に
                avg_engagement=round(tag_avg_engagement, 2),
                effectiveness_score=round(effectiveness, 2),
            )
        )

    results.sort(key=lambda x: x.effectiveness_score, reverse=True)
    logger.info(f"{len(results)}個のTikTokハッシュタグを分析しました")

    return results


def analyze_tiktok_sounds(
    videos: list[TikTokVideo],
) -> list[TikTokSoundAnalysis]:
    """使用サウンドの効果を分析

    Args:
        videos: 動画リスト

    Returns:
        list[TikTokSoundAnalysis]: サウンド分析結果リスト
    """
    if not videos:
        return []

    sound_data: dict[str, dict] = defaultdict(
        lambda: {
            "name": "",
            "count": 0,
            "views": 0,
            "likes": 0,
            "comments": 0,
            "shares": 0,
        }
    )

    # 全体の平均エンゲージメントを計算
    total_engagement = sum(v.likes + v.comments + v.shares for v in videos)
    avg_engagement = total_engagement / len(videos) if videos else 0

    # サウンドごとのデータを集計
    for video in videos:
        if not video.sound_id:
            continue

        sound_id = video.sound_id
        sound_data[sound_id]["name"] = video.sound_name or "Unknown"
        sound_data[sound_id]["count"] += 1
        sound_data[sound_id]["views"] += video.views
        sound_data[sound_id]["likes"] += video.likes
        sound_data[sound_id]["comments"] += video.comments
        sound_data[sound_id]["shares"] += video.shares

    # 分析結果を作成
    results: list[TikTokSoundAnalysis] = []
    for sound_id, data in sound_data.items():
        count = data["count"]
        total_views = data["views"]
        total_likes = data["likes"]
        sound_engagement = total_likes + data["comments"] + data["shares"]
        sound_avg_engagement = sound_engagement / count if count > 0 else 0

        # 効果スコア
        frequency_factor = min(1.0, count / 3)
        effectiveness = (
            (sound_avg_engagement / avg_engagement * frequency_factor)
            if avg_engagement > 0
            else 0
        )

        results.append(
            TikTokSoundAnalysis(
                sound_id=sound_id,
                sound_name=data["name"],
                usage_count=count,
                total_views=total_views,
                total_likes=total_likes,
                avg_engagement=round(sound_avg_engagement, 2),
                is_trending=total_views > 100000,  # 10万再生以上をトレンド判定
                effectiveness_score=round(effectiveness, 2),
            )
        )

    results.sort(key=lambda x: x.effectiveness_score, reverse=True)
    logger.info(f"{len(results)}個のTikTokサウンドを分析しました")

    return results


# TikTokコンテンツパターン検出用
TIKTOK_PATTERNS = {
    "tutorial": [
        r"how to",
        r"やり方",
        r"方法",
        r"tutorial",
        r"step by step",
        r"ステップ",
        r"learn",
        r"教え",
        r"tips",
        r"hack",
        r"ライフハック",
    ],
    "challenge": [
        r"challenge",
        r"チャレンジ",
        r"やってみた",
        r"試してみた",
        r"trend",
        r"トレンド",
    ],
    "transformation": [
        r"before.*after",
        r"ビフォーアフター",
        r"変身",
        r"makeover",
        r"glow up",
    ],
    "pov": [
        r"pov:",
        r"pov：",
        r"視点",
    ],
    "storytime": [
        r"storytime",
        r"ストーリータイム",
        r"体験談",
        r"実話",
    ],
    "duet_stitch": [
        r"#duet",
        r"#stitch",
        r"duet with",
        r"stitch with",
    ],
    "engagement_bait": [
        r"いいね",
        r"フォロー",
        r"コメント",
        r"シェア",
        r"follow for",
        r"like if",
        r"comment",
        r"share this",
        r"part \d",
        r"パート\d",
    ],
}


def analyze_tiktok_patterns(
    videos: list[TikTokVideo],
) -> list[ContentPattern]:
    """TikTokコンテンツパターンを分析

    Args:
        videos: 動画リスト

    Returns:
        list[ContentPattern]: コンテンツパターン分析結果リスト
    """
    if not videos:
        return []

    pattern_data: dict[str, dict] = {
        pattern_type: {"count": 0, "total_engagement": 0, "total_views": 0, "examples": []}
        for pattern_type in TIKTOK_PATTERNS.keys()
    }

    for video in videos:
        if not video.description:
            continue

        engagement = video.likes + video.comments + video.shares

        for pattern_type, patterns in TIKTOK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, video.description, re.IGNORECASE):
                    data = pattern_data[pattern_type]
                    data["count"] += 1
                    data["total_engagement"] += engagement
                    data["total_views"] += video.views
                    if len(data["examples"]) < 3:
                        data["examples"].append(video.description[:100])
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
    logger.info(f"{len(results)}個のTikTokコンテンツパターンを分析しました")

    return results


def analyze_video_duration(
    videos: list[TikTokVideo],
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

    # 長さ区分
    duration_bins = {
        "0-15s": {"count": 0, "engagement": 0, "views": 0},
        "15-30s": {"count": 0, "engagement": 0, "views": 0},
        "30-60s": {"count": 0, "engagement": 0, "views": 0},
        "60s+": {"count": 0, "engagement": 0, "views": 0},
    }

    total_duration = 0
    for video in videos:
        total_duration += video.duration
        engagement = video.likes + video.comments + video.shares

        if video.duration <= 15:
            bin_key = "0-15s"
        elif video.duration <= 30:
            bin_key = "15-30s"
        elif video.duration <= 60:
            bin_key = "30-60s"
        else:
            bin_key = "60s+"

        duration_bins[bin_key]["count"] += 1
        duration_bins[bin_key]["engagement"] += engagement
        duration_bins[bin_key]["views"] += video.views

    avg_duration = total_duration / len(videos)

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
        default=("30-60s", 0),
    )[0]

    return avg_duration, best_duration, duration_engagement


def analyze_video_types(
    videos: list[TikTokVideo],
) -> tuple[Optional[float], Optional[float]]:
    """動画タイプ別パフォーマンスを分析

    Args:
        videos: 動画リスト

    Returns:
        tuple[Optional[float], Optional[float]]:
            - デュエット動画の平均エンゲージメント
            - スティッチ動画の平均エンゲージメント
    """
    duet_engagement: list[int] = []
    stitch_engagement: list[int] = []

    for video in videos:
        engagement = video.likes + video.comments + video.shares

        if video.video_type == "duet":
            duet_engagement.append(engagement)
        elif video.video_type == "stitch":
            stitch_engagement.append(engagement)

    duet_avg = sum(duet_engagement) / len(duet_engagement) if duet_engagement else None
    stitch_avg = sum(stitch_engagement) / len(stitch_engagement) if stitch_engagement else None

    return duet_avg, stitch_avg


def _generate_tiktok_recommendations(
    metrics: TikTokEngagementMetrics,
    best_hours: list[int],
    hashtag_analysis: list[HashtagAnalysis],
    sound_analysis: list[TikTokSoundAnalysis],
    content_patterns: list[ContentPattern],
    best_duration: Optional[str],
) -> PostRecommendation:
    """TikTokレコメンデーションを生成

    Args:
        metrics: エンゲージメント指標
        best_hours: 最適な投稿時間
        hashtag_analysis: ハッシュタグ分析結果
        sound_analysis: サウンド分析結果
        content_patterns: コンテンツパターン分析結果
        best_duration: 最適な動画長

    Returns:
        PostRecommendation: 投稿レコメンデーション
    """
    # 効果的なハッシュタグを取得
    effective_hashtags = [h.hashtag for h in hashtag_analysis[:5] if h.usage_count >= 2]

    # 理由の説明を生成
    hour_strs = [f"{h}時" for h in best_hours]
    hours_text = "、".join(hour_strs)

    reasoning_parts = [
        f"TikTok分析の結果、{hours_text}の投稿が最もエンゲージメントが高い傾向にあります。",
        f"平均再生数は{metrics.avg_views_per_video}、",
        f"平均いいね数は{metrics.avg_likes_per_video}、",
        f"いいね率（いいね/再生）は{metrics.view_to_like_ratio}%です。",
    ]

    if best_duration:
        reasoning_parts.append(f"最も効果的な動画の長さは「{best_duration}」です。")

    if effective_hashtags:
        reasoning_parts.append(
            f"効果的なハッシュタグ: #{', #'.join(effective_hashtags[:3])}。"
        )

    if sound_analysis:
        top_sound = sound_analysis[0]
        if top_sound.usage_count >= 2:
            reasoning_parts.append(
                f"効果的なサウンド: 「{top_sound.sound_name}」"
                f"（平均エンゲージメント: {top_sound.avg_engagement}）。"
            )

    if content_patterns:
        best_pattern = content_patterns[0]
        pattern_names = {
            "tutorial": "チュートリアル/How-to",
            "challenge": "チャレンジ",
            "transformation": "ビフォーアフター",
            "pov": "POV（視点）",
            "storytime": "ストーリータイム",
            "duet_stitch": "デュエット/スティッチ",
            "engagement_bait": "エンゲージメント促進",
        }
        pattern_name = pattern_names.get(
            best_pattern.pattern_type, best_pattern.pattern_type
        )
        reasoning_parts.append(
            f"最も効果的なコンテンツ形式は「{pattern_name}」"
            f"（平均エンゲージメント: {best_pattern.avg_engagement}）です。"
        )

    # コンテンツアイデア生成
    content_ideas = []
    if content_patterns:
        for pattern in content_patterns[:3]:
            pattern_names = {
                "tutorial": "チュートリアル動画を投稿する",
                "challenge": "トレンドチャレンジに参加する",
                "transformation": "ビフォーアフター動画を作成する",
                "pov": "POV形式の動画を試す",
                "storytime": "ストーリータイム動画を作成する",
                "duet_stitch": "人気動画にデュエット/スティッチで反応する",
                "engagement_bait": "シリーズ物の動画を作成する",
            }
            idea = pattern_names.get(pattern.pattern_type)
            if idea and idea not in content_ideas:
                content_ideas.append(idea)

    return PostRecommendation(
        best_hours=best_hours,
        suggested_hashtags=effective_hashtags,
        content_ideas=content_ideas,
        reasoning="".join(reasoning_parts),
    )


def analyze_tiktok_videos(
    videos: list[TikTokVideo],
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
) -> TikTokAnalysisResult:
    """TikTok動画を総合分析

    Args:
        videos: 動画リスト
        period_start: 分析期間開始
        period_end: 分析期間終了

    Returns:
        TikTokAnalysisResult: 分析結果
    """
    if not videos:
        now = datetime.now(UTC)
        return TikTokAnalysisResult(
            period_start=period_start or now,
            period_end=period_end or now,
            total_videos=0,
            metrics=TikTokEngagementMetrics(),
        )

    # 期間を決定
    all_dates = [v.create_time for v in videos]
    actual_start = period_start or min(all_dates)
    actual_end = period_end or max(all_dates)

    # 各分析を実行
    metrics = calculate_tiktok_metrics(videos)
    hourly_breakdown = analyze_tiktok_hourly(videos)
    top_videos = get_top_tiktok_videos(videos)
    best_hours = find_tiktok_best_hours(hourly_breakdown)

    # コンテンツ分析
    hashtag_results = analyze_tiktok_hashtags(videos)
    sound_results = analyze_tiktok_sounds(videos)
    pattern_results = analyze_tiktok_patterns(videos)

    # 動画長分析
    avg_duration, best_duration, _ = analyze_video_duration(videos)
    duet_performance, stitch_performance = analyze_video_types(videos)

    # レコメンデーション生成
    recommendations = _generate_tiktok_recommendations(
        metrics, best_hours, hashtag_results, sound_results, pattern_results, best_duration
    )

    logger.info(f"{len(videos)}件のTikTok動画を分析しました")

    return TikTokAnalysisResult(
        period_start=actual_start,
        period_end=actual_end,
        total_videos=len(videos),
        metrics=metrics,
        hourly_breakdown=hourly_breakdown,
        top_performing_videos=top_videos,
        recommendations=recommendations,
        hashtag_analysis=hashtag_results,
        sound_analysis=sound_results,
        content_patterns=pattern_results,
        avg_video_duration=round(avg_duration, 2),
        best_duration_range=best_duration,
        duet_performance=duet_performance,
        stitch_performance=stitch_performance,
    )
