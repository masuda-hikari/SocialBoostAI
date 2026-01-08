"""
Instagram分析モジュール

InstagramのPost/Reel/Storyを分析し、エンゲージメント指標・時間帯分析・
コンテンツパターン分析を提供する。
"""

import logging
import re
from collections import defaultdict
from datetime import UTC, datetime
from typing import Optional, Union

from .content_analysis import STOP_WORDS_EN, STOP_WORDS_JA
from .models import (
    ContentPattern,
    HashtagAnalysis,
    HourlyEngagement,
    InstagramAnalysisResult,
    InstagramEngagementMetrics,
    InstagramPost,
    InstagramReel,
    PostRecommendation,
)

logger = logging.getLogger(__name__)


def calculate_instagram_metrics(
    posts: list[InstagramPost],
    follower_count: int = 0,
) -> InstagramEngagementMetrics:
    """投稿リストからエンゲージメント指標を計算

    Args:
        posts: 投稿リスト
        follower_count: フォロワー数（エンゲージメント率計算用）

    Returns:
        InstagramEngagementMetrics: エンゲージメント指標
    """
    if not posts:
        return InstagramEngagementMetrics()

    total_likes = sum(p.likes for p in posts)
    total_comments = sum(p.comments for p in posts)
    total_saves = sum(p.saves or 0 for p in posts)
    total_shares = sum(p.shares or 0 for p in posts)
    total_impressions = sum(p.impressions or 0 for p in posts)
    total_reach = sum(p.reach or 0 for p in posts)

    post_count = len(posts)
    total_engagement = total_likes + total_comments + total_saves

    # エンゲージメント率（フォロワーベース）
    engagement_rate = 0.0
    if follower_count > 0:
        engagement_rate = (total_engagement / post_count / follower_count) * 100

    return InstagramEngagementMetrics(
        total_likes=total_likes,
        total_comments=total_comments,
        total_saves=total_saves,
        total_shares=total_shares,
        total_impressions=total_impressions,
        total_reach=total_reach,
        engagement_rate=round(engagement_rate, 4),
        avg_likes_per_post=round(total_likes / post_count, 2),
        avg_comments_per_post=round(total_comments / post_count, 2),
        avg_saves_per_post=round(total_saves / post_count, 2),
    )


def analyze_instagram_hourly(
    posts: list[InstagramPost],
) -> list[HourlyEngagement]:
    """時間帯別エンゲージメントを分析

    Args:
        posts: 投稿リスト

    Returns:
        list[HourlyEngagement]: 時間帯別エンゲージメントリスト（0-23時）
    """
    hourly_data: dict[int, dict[str, list[int]]] = defaultdict(
        lambda: {"likes": [], "comments": []}
    )

    for post in posts:
        hour = post.created_at.hour
        hourly_data[hour]["likes"].append(post.likes)
        hourly_data[hour]["comments"].append(post.comments)

    results: list[HourlyEngagement] = []
    for hour in range(24):
        data = hourly_data[hour]
        likes = data["likes"]
        comments = data["comments"]

        if likes:
            avg_likes = sum(likes) / len(likes)
            avg_comments = sum(comments) / len(comments)
            # Instagramではretweets相当としてcommentsを使用
            total_engagement = avg_likes + avg_comments
        else:
            avg_likes = 0.0
            avg_comments = 0.0
            total_engagement = 0.0

        results.append(
            HourlyEngagement(
                hour=hour,
                avg_likes=round(avg_likes, 2),
                avg_retweets=round(avg_comments, 2),  # commentsをretweets枠に
                post_count=len(likes),
                total_engagement=round(total_engagement, 2),
            )
        )

    return results


def find_instagram_best_hours(
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


def get_top_instagram_posts(
    posts: list[InstagramPost],
    top_n: int = 5,
) -> list[InstagramPost]:
    """最もエンゲージメントの高い投稿を取得

    Args:
        posts: 投稿リスト
        top_n: 上位何件を返すか

    Returns:
        list[InstagramPost]: 上位投稿リスト
    """
    sorted_posts = sorted(
        posts,
        key=lambda p: p.likes + p.comments + (p.saves or 0),
        reverse=True,
    )
    return sorted_posts[:top_n]


def get_top_instagram_reels(
    reels: list[InstagramReel],
    top_n: int = 5,
) -> list[InstagramReel]:
    """最もエンゲージメントの高いリールを取得

    Args:
        reels: リールリスト
        top_n: 上位何件を返すか

    Returns:
        list[InstagramReel]: 上位リールリスト
    """
    sorted_reels = sorted(
        reels,
        key=lambda r: r.likes + r.comments + (r.saves or 0) + (r.plays or 0),
        reverse=True,
    )
    return sorted_reels[:top_n]


def extract_instagram_hashtags(caption: Optional[str]) -> list[str]:
    """キャプションからハッシュタグを抽出

    Args:
        caption: キャプションテキスト

    Returns:
        list[str]: ハッシュタグリスト（#なし）
    """
    if not caption:
        return []

    pattern = r"#([^\s#]+)"
    matches = re.findall(pattern, caption)
    return [m.lower() for m in matches]


def analyze_instagram_hashtags(
    posts: list[InstagramPost],
) -> list[HashtagAnalysis]:
    """ハッシュタグの効果を分析

    Args:
        posts: 投稿リスト

    Returns:
        list[HashtagAnalysis]: ハッシュタグ分析結果リスト
    """
    if not posts:
        return []

    hashtag_data: dict[str, dict] = defaultdict(
        lambda: {"count": 0, "likes": 0, "comments": 0, "saves": 0}
    )

    # 全体の平均エンゲージメントを計算
    total_engagement = sum(p.likes + p.comments + (p.saves or 0) for p in posts)
    avg_engagement = total_engagement / len(posts) if posts else 0

    # ハッシュタグごとのデータを集計
    for post in posts:
        hashtags = extract_instagram_hashtags(post.caption)
        for tag in hashtags:
            hashtag_data[tag]["count"] += 1
            hashtag_data[tag]["likes"] += post.likes
            hashtag_data[tag]["comments"] += post.comments
            hashtag_data[tag]["saves"] += post.saves or 0

    # 分析結果を作成
    results: list[HashtagAnalysis] = []
    for hashtag, data in hashtag_data.items():
        count = data["count"]
        total_likes = data["likes"]
        total_comments = data["comments"]
        total_saves = data["saves"]
        tag_engagement = total_likes + total_comments + total_saves
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
                total_retweets=total_comments,  # Instagram: commentsをretweets枠に
                avg_engagement=round(tag_avg_engagement, 2),
                effectiveness_score=round(effectiveness, 2),
            )
        )

    results.sort(key=lambda x: x.effectiveness_score, reverse=True)
    logger.info(f"{len(results)}個のInstagramハッシュタグを分析しました")

    return results


# Instagramコンテンツパターン検出用
INSTAGRAM_PATTERNS = {
    "question": [
        r"[？?]$",
        r"[？?]\s",
        r"どう思う",
        r"皆さん",
        r"教えて",
        r"what do you think",
        r"thoughts\?",
    ],
    "tutorial": [
        r"how to",
        r"やり方",
        r"方法",
        r"tutorial",
        r"step by step",
        r"ステップ",
        r"\d+選",
    ],
    "behind_scenes": [
        r"舞台裏",
        r"behind the scenes",
        r"bts",
        r"メイキング",
        r"裏側",
    ],
    "engagement_bait": [
        r"いいね",
        r"保存",
        r"シェア",
        r"コメント",
        r"double tap",
        r"save this",
        r"share with",
        r"tag a friend",
    ],
    "product": [
        r"新商品",
        r"new arrival",
        r"発売",
        r"launch",
        r"available now",
        r"販売",
        r"購入",
        r"link in bio",
    ],
}


def analyze_instagram_patterns(
    posts: list[InstagramPost],
) -> list[ContentPattern]:
    """Instagramコンテンツパターンを分析

    Args:
        posts: 投稿リスト

    Returns:
        list[ContentPattern]: コンテンツパターン分析結果リスト
    """
    if not posts:
        return []

    pattern_data: dict[str, dict] = {
        pattern_type: {"count": 0, "total_engagement": 0, "examples": []}
        for pattern_type in INSTAGRAM_PATTERNS.keys()
    }

    for post in posts:
        if not post.caption:
            continue

        engagement = post.likes + post.comments + (post.saves or 0)

        for pattern_type, patterns in INSTAGRAM_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, post.caption, re.IGNORECASE):
                    data = pattern_data[pattern_type]
                    data["count"] += 1
                    data["total_engagement"] += engagement
                    if len(data["examples"]) < 3:
                        data["examples"].append(post.caption[:100])
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
    logger.info(f"{len(results)}個のInstagramコンテンツパターンを分析しました")

    return results


def _generate_instagram_recommendations(
    metrics: InstagramEngagementMetrics,
    best_hours: list[int],
    hashtag_analysis: list[HashtagAnalysis],
    content_patterns: list[ContentPattern],
) -> PostRecommendation:
    """Instagramレコメンデーションを生成

    Args:
        metrics: エンゲージメント指標
        best_hours: 最適な投稿時間
        hashtag_analysis: ハッシュタグ分析結果
        content_patterns: コンテンツパターン分析結果

    Returns:
        PostRecommendation: 投稿レコメンデーション
    """
    # 効果的なハッシュタグを取得
    effective_hashtags = [h.hashtag for h in hashtag_analysis[:5] if h.usage_count >= 2]

    # 理由の説明を生成
    hour_strs = [f"{h}時" for h in best_hours]
    hours_text = "、".join(hour_strs)

    reasoning_parts = [
        f"Instagram分析の結果、{hours_text}の投稿が最もエンゲージメントが高い傾向にあります。",
        f"平均いいね数は{metrics.avg_likes_per_post}、",
        f"平均コメント数は{metrics.avg_comments_per_post}、",
        f"平均保存数は{metrics.avg_saves_per_post}です。",
    ]

    if effective_hashtags:
        reasoning_parts.append(
            f"効果的なハッシュタグ: #{', #'.join(effective_hashtags[:3])}。"
        )

    if content_patterns:
        best_pattern = content_patterns[0]
        pattern_names = {
            "question": "質問形式",
            "tutorial": "チュートリアル/How-to",
            "behind_scenes": "舞台裏/メイキング",
            "engagement_bait": "エンゲージメント促進",
            "product": "商品紹介",
        }
        pattern_name = pattern_names.get(
            best_pattern.pattern_type, best_pattern.pattern_type
        )
        reasoning_parts.append(
            f"最も効果的なコンテンツ形式は「{pattern_name}」"
            f"（平均エンゲージメント: {best_pattern.avg_engagement}）です。"
        )

    return PostRecommendation(
        best_hours=best_hours,
        suggested_hashtags=effective_hashtags,
        content_ideas=[],  # AI機能で実装
        reasoning="".join(reasoning_parts),
    )


def analyze_instagram_posts(
    posts: list[InstagramPost],
    reels: list[InstagramReel] = [],
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
    follower_count: int = 0,
) -> InstagramAnalysisResult:
    """Instagram投稿を総合分析

    Args:
        posts: 投稿リスト
        reels: リールリスト
        period_start: 分析期間開始
        period_end: 分析期間終了
        follower_count: フォロワー数（エンゲージメント率計算用）

    Returns:
        InstagramAnalysisResult: 分析結果
    """
    if not posts and not reels:
        now = datetime.now(UTC)
        return InstagramAnalysisResult(
            period_start=period_start or now,
            period_end=period_end or now,
            total_posts=0,
            total_reels=0,
            metrics=InstagramEngagementMetrics(),
        )

    # 期間を決定
    all_dates = [p.created_at for p in posts] + [r.created_at for r in reels]
    actual_start = period_start or min(all_dates)
    actual_end = period_end or max(all_dates)

    # 各分析を実行
    metrics = calculate_instagram_metrics(posts, follower_count)
    hourly_breakdown = analyze_instagram_hourly(posts)
    top_posts = get_top_instagram_posts(posts)
    top_reels = get_top_instagram_reels(reels)
    best_hours = find_instagram_best_hours(hourly_breakdown)

    # コンテンツ分析
    hashtag_results = analyze_instagram_hashtags(posts)
    pattern_results = analyze_instagram_patterns(posts)

    # レコメンデーション生成
    recommendations = _generate_instagram_recommendations(
        metrics, best_hours, hashtag_results, pattern_results
    )

    logger.info(f"{len(posts)}件のInstagram投稿、{len(reels)}件のリールを分析しました")

    return InstagramAnalysisResult(
        period_start=actual_start,
        period_end=actual_end,
        total_posts=len(posts),
        total_reels=len(reels),
        metrics=metrics,
        hourly_breakdown=hourly_breakdown,
        top_performing_posts=top_posts,
        top_performing_reels=top_reels,
        recommendations=recommendations,
        hashtag_analysis=hashtag_results,
        content_patterns=pattern_results,
    )
