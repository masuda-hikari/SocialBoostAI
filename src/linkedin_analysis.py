"""
LinkedIn分析モジュール

LinkedIn投稿を分析し、エンゲージメント指標・時間帯分析・
曜日分析・ハッシュタグ分析・コンテンツパターン分析を提供する。

LinkedInはB2B特化のため、曜日分析が特に重要。
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
    LinkedInAnalysisResult,
    LinkedInArticle,
    LinkedInDemographics,
    LinkedInEngagementMetrics,
    LinkedInPost,
    PostRecommendation,
)

logger = logging.getLogger(__name__)

# 曜日名（日本語）
WEEKDAY_NAMES = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]


def calculate_linkedin_metrics(
    posts: list[LinkedInPost],
) -> LinkedInEngagementMetrics:
    """投稿リストからエンゲージメント指標を計算

    Args:
        posts: 投稿リスト

    Returns:
        LinkedInEngagementMetrics: エンゲージメント指標
    """
    if not posts:
        return LinkedInEngagementMetrics()

    total_impressions = sum(p.impressions or 0 for p in posts)
    total_unique_impressions = sum(p.unique_impressions or 0 for p in posts)
    total_likes = sum(p.likes for p in posts)
    total_comments = sum(p.comments for p in posts)
    total_shares = sum(p.shares for p in posts)
    total_clicks = sum(p.clicks or 0 for p in posts)

    post_count = len(posts)
    total_engagement = total_likes + total_comments + total_shares + total_clicks

    # エンゲージメント率（インプレッションベース）
    engagement_rate = 0.0
    if total_impressions > 0:
        engagement_rate = (total_engagement / total_impressions) * 100

    # CTR
    ctr = 0.0
    if total_impressions > 0:
        ctr = (total_clicks / total_impressions) * 100

    # バイラリティ率
    virality_rate = 0.0
    if total_impressions > 0:
        virality_rate = (total_shares / total_impressions) * 100

    return LinkedInEngagementMetrics(
        total_impressions=total_impressions,
        total_unique_impressions=total_unique_impressions,
        total_likes=total_likes,
        total_comments=total_comments,
        total_shares=total_shares,
        total_clicks=total_clicks,
        engagement_rate=round(engagement_rate, 4),
        avg_likes_per_post=round(total_likes / post_count, 2),
        avg_comments_per_post=round(total_comments / post_count, 2),
        avg_shares_per_post=round(total_shares / post_count, 2),
        avg_clicks_per_post=round(total_clicks / post_count, 2),
        click_through_rate=round(ctr, 4),
        virality_rate=round(virality_rate, 4),
    )


def analyze_linkedin_hourly(
    posts: list[LinkedInPost],
) -> list[HourlyEngagement]:
    """時間帯別エンゲージメントを分析

    Args:
        posts: 投稿リスト

    Returns:
        list[HourlyEngagement]: 時間帯別エンゲージメントリスト（0-23時）
    """
    hourly_data: dict[int, dict[str, list[int]]] = defaultdict(
        lambda: {"likes": [], "shares": [], "comments": [], "clicks": []}
    )

    for post in posts:
        hour = post.created_at.hour
        hourly_data[hour]["likes"].append(post.likes)
        hourly_data[hour]["shares"].append(post.shares)
        hourly_data[hour]["comments"].append(post.comments)
        hourly_data[hour]["clicks"].append(post.clicks or 0)

    results: list[HourlyEngagement] = []
    for hour in range(24):
        data = hourly_data[hour]
        likes = data["likes"]
        shares = data["shares"]
        comments = data["comments"]
        clicks = data["clicks"]

        if likes:
            avg_likes = sum(likes) / len(likes)
            avg_shares = sum(shares) / len(shares)
            avg_comments = sum(comments) / len(comments)
            avg_clicks = sum(clicks) / len(clicks)
            total_engagement = avg_likes + avg_shares + avg_comments + avg_clicks
        else:
            avg_likes = 0.0
            avg_shares = 0.0
            total_engagement = 0.0

        results.append(
            HourlyEngagement(
                hour=hour,
                avg_likes=round(avg_likes, 2),
                avg_retweets=round(avg_shares, 2),  # LinkedInではsharesを表示
                post_count=len(likes),
                total_engagement=round(total_engagement, 2),
            )
        )

    return results


def analyze_linkedin_daily(
    posts: list[LinkedInPost],
) -> list[dict]:
    """曜日別エンゲージメントを分析（B2Bでは曜日が重要）

    Args:
        posts: 投稿リスト

    Returns:
        list[dict]: 曜日別エンゲージメントリスト
    """
    daily_data: dict[int, dict[str, list[int]]] = defaultdict(
        lambda: {"likes": [], "shares": [], "comments": [], "clicks": [], "impressions": []}
    )

    for post in posts:
        weekday = post.created_at.weekday()  # 0=月曜, 6=日曜
        daily_data[weekday]["likes"].append(post.likes)
        daily_data[weekday]["shares"].append(post.shares)
        daily_data[weekday]["comments"].append(post.comments)
        daily_data[weekday]["clicks"].append(post.clicks or 0)
        daily_data[weekday]["impressions"].append(post.impressions or 0)

    results: list[dict] = []
    for weekday in range(7):
        data = daily_data[weekday]
        likes = data["likes"]
        shares = data["shares"]
        comments = data["comments"]
        clicks = data["clicks"]
        impressions = data["impressions"]

        if likes:
            avg_likes = sum(likes) / len(likes)
            avg_shares = sum(shares) / len(shares)
            avg_comments = sum(comments) / len(comments)
            avg_clicks = sum(clicks) / len(clicks)
            avg_impressions = sum(impressions) / len(impressions)
            total_engagement = avg_likes + avg_shares + avg_comments + avg_clicks
        else:
            avg_likes = 0.0
            avg_shares = 0.0
            avg_comments = 0.0
            avg_clicks = 0.0
            avg_impressions = 0.0
            total_engagement = 0.0

        results.append({
            "weekday": weekday,
            "weekday_name": WEEKDAY_NAMES[weekday],
            "avg_likes": round(avg_likes, 2),
            "avg_shares": round(avg_shares, 2),
            "avg_comments": round(avg_comments, 2),
            "avg_clicks": round(avg_clicks, 2),
            "avg_impressions": round(avg_impressions, 2),
            "post_count": len(likes),
            "total_engagement": round(total_engagement, 2),
        })

    return results


def find_linkedin_best_hours(
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


def find_linkedin_best_days(
    daily_engagement: list[dict],
    top_n: int = 3,
    min_posts: int = 2,
) -> list[str]:
    """最適な投稿曜日を特定（B2B特化）

    Args:
        daily_engagement: 曜日別エンゲージメントリスト
        top_n: 上位何件を返すか
        min_posts: 最低投稿数（信頼性のため）

    Returns:
        list[str]: 最適な投稿曜日のリスト
    """
    valid_days = [d for d in daily_engagement if d["post_count"] >= min_posts]

    if not valid_days:
        valid_days = daily_engagement

    sorted_days = sorted(valid_days, key=lambda d: d["total_engagement"], reverse=True)
    return [d["weekday_name"] for d in sorted_days[:top_n]]


def get_top_linkedin_posts(
    posts: list[LinkedInPost],
    top_n: int = 5,
) -> list[LinkedInPost]:
    """最もエンゲージメントの高い投稿を取得

    Args:
        posts: 投稿リスト
        top_n: 上位何件を返すか

    Returns:
        list[LinkedInPost]: 上位投稿リスト
    """
    sorted_posts = sorted(
        posts,
        key=lambda p: p.likes + p.comments * 5 + p.shares * 10 + (p.clicks or 0),
        reverse=True,
    )
    return sorted_posts[:top_n]


def analyze_linkedin_hashtags(
    posts: list[LinkedInPost],
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
        lambda: {"count": 0, "likes": 0, "shares": 0, "comments": 0, "clicks": 0}
    )

    # 全体の平均エンゲージメントを計算
    total_engagement = sum(
        p.likes + p.comments + p.shares + (p.clicks or 0) for p in posts
    )
    avg_engagement = total_engagement / len(posts) if posts else 0

    # ハッシュタグごとのデータを集計
    for post in posts:
        for hashtag in post.hashtags:
            hashtag_lower = hashtag.lower()
            hashtag_data[hashtag_lower]["count"] += 1
            hashtag_data[hashtag_lower]["likes"] += post.likes
            hashtag_data[hashtag_lower]["shares"] += post.shares
            hashtag_data[hashtag_lower]["comments"] += post.comments
            hashtag_data[hashtag_lower]["clicks"] += post.clicks or 0

    # 分析結果を作成
    results: list[HashtagAnalysis] = []
    for hashtag, data in hashtag_data.items():
        count = data["count"]
        total_likes = data["likes"]
        total_retweets = data["shares"]  # LinkedInではshares
        tag_engagement = total_likes + data["comments"] + total_retweets + data["clicks"]
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
                total_retweets=total_retweets,
                avg_engagement=round(tag_avg_engagement, 2),
                effectiveness_score=round(effectiveness, 2),
            )
        )

    results.sort(key=lambda x: x.effectiveness_score, reverse=True)
    logger.info(f"{len(results)}個のLinkedInハッシュタグを分析しました")

    return results


# LinkedInコンテンツパターン検出用（B2B特化）
LINKEDIN_PATTERNS = {
    "thought_leadership": [
        r"insight",
        r"perspective",
        r"lesson",
        r"learned",
        r"experience",
        r"reflection",
        r"考察",
        r"気づき",
        r"学び",
        r"教訓",
    ],
    "career": [
        r"career",
        r"job",
        r"hired",
        r"hiring",
        r"recruitment",
        r"転職",
        r"採用",
        r"キャリア",
        r"就職",
    ],
    "industry_news": [
        r"breaking",
        r"news",
        r"update",
        r"announced",
        r"ニュース",
        r"発表",
        r"アップデート",
    ],
    "tips": [
        r"tip",
        r"advice",
        r"how to",
        r"guide",
        r"コツ",
        r"方法",
        r"アドバイス",
        r"ポイント",
    ],
    "achievement": [
        r"excited",
        r"thrilled",
        r"proud",
        r"milestone",
        r"achieved",
        r"嬉しい",
        r"達成",
        r"成功",
        r"マイルストーン",
    ],
    "networking": [
        r"connect",
        r"connection",
        r"network",
        r"meet",
        r"event",
        r"conference",
        r"カンファレンス",
        r"イベント",
        r"交流",
    ],
    "question": [
        r"\?$",
        r"what do you think",
        r"how do you",
        r"thoughts\?",
        r"どう思いますか",
        r"どう考えますか",
        r"教えてください",
    ],
    "listicle": [
        r"\d+\s*(tips|ways|things|reasons)",
        r"\d+\s*(選|個|つ)",
        r"ランキング",
        r"まとめ",
    ],
    "personal_story": [
        r"story",
        r"journey",
        r"my experience",
        r"when i",
        r"私の経験",
        r"ストーリー",
        r"エピソード",
    ],
    "engagement_bait": [
        r"agree\?",
        r"like if",
        r"share if",
        r"comment",
        r"いいね",
        r"シェア",
        r"コメント",
        r"どう思う",
    ],
}


def analyze_linkedin_patterns(
    posts: list[LinkedInPost],
) -> list[ContentPattern]:
    """LinkedInコンテンツパターンを分析

    Args:
        posts: 投稿リスト

    Returns:
        list[ContentPattern]: コンテンツパターン分析結果リスト
    """
    if not posts:
        return []

    pattern_data: dict[str, dict] = {
        pattern_type: {"count": 0, "total_engagement": 0, "total_impressions": 0, "examples": []}
        for pattern_type in LINKEDIN_PATTERNS.keys()
    }

    for post in posts:
        text = post.text or ""
        if not text.strip():
            continue

        engagement = post.likes + post.comments + post.shares + (post.clicks or 0)

        for pattern_type, patterns in LINKEDIN_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    data = pattern_data[pattern_type]
                    data["count"] += 1
                    data["total_engagement"] += engagement
                    data["total_impressions"] += post.impressions or 0
                    if len(data["examples"]) < 3:
                        data["examples"].append(text[:100])
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
    logger.info(f"{len(results)}個のLinkedInコンテンツパターンを分析しました")

    return results


def analyze_media_type_performance(
    posts: list[LinkedInPost],
) -> dict[str, float]:
    """メディアタイプ別パフォーマンスを分析

    Args:
        posts: 投稿リスト

    Returns:
        dict[str, float]: メディアタイプ別平均エンゲージメント
    """
    if not posts:
        return {}

    media_data: dict[str, dict] = defaultdict(
        lambda: {"count": 0, "engagement": 0}
    )

    for post in posts:
        media_type = post.media_type or "NONE"
        engagement = post.likes + post.comments + post.shares + (post.clicks or 0)
        media_data[media_type]["count"] += 1
        media_data[media_type]["engagement"] += engagement

    result = {}
    for media_type, data in media_data.items():
        if data["count"] > 0:
            result[media_type] = round(data["engagement"] / data["count"], 2)

    return result


def analyze_post_length(
    posts: list[LinkedInPost],
) -> tuple[float, dict[str, float]]:
    """投稿文字数を分析

    Args:
        posts: 投稿リスト

    Returns:
        tuple[float, dict[str, float]]:
            - 平均文字数
            - 文字数帯別エンゲージメント
    """
    if not posts:
        return 0.0, {}

    length_bins = {
        "short": {"count": 0, "engagement": 0},  # 0-150文字
        "medium": {"count": 0, "engagement": 0},  # 150-500文字
        "long": {"count": 0, "engagement": 0},  # 500-1500文字
        "very_long": {"count": 0, "engagement": 0},  # 1500文字以上
    }

    total_length = 0
    posts_with_text = 0

    for post in posts:
        text = post.text or ""
        length = len(text)
        if length == 0:
            continue

        total_length += length
        posts_with_text += 1
        engagement = post.likes + post.comments + post.shares + (post.clicks or 0)

        if length <= 150:
            bin_key = "short"
        elif length <= 500:
            bin_key = "medium"
        elif length <= 1500:
            bin_key = "long"
        else:
            bin_key = "very_long"

        length_bins[bin_key]["count"] += 1
        length_bins[bin_key]["engagement"] += engagement

    avg_length = total_length / posts_with_text if posts_with_text > 0 else 0

    length_engagement = {}
    for bin_key, data in length_bins.items():
        if data["count"] > 0:
            length_engagement[bin_key] = round(data["engagement"] / data["count"], 2)

    return avg_length, length_engagement


def _generate_linkedin_recommendations(
    metrics: LinkedInEngagementMetrics,
    best_hours: list[int],
    best_days: list[str],
    hashtag_analysis: list[HashtagAnalysis],
    content_patterns: list[ContentPattern],
    media_performance: dict[str, float],
    post_length_performance: dict[str, float],
) -> PostRecommendation:
    """LinkedInレコメンデーションを生成

    Args:
        metrics: エンゲージメント指標
        best_hours: 最適な投稿時間
        best_days: 最適な投稿曜日
        hashtag_analysis: ハッシュタグ分析結果
        content_patterns: コンテンツパターン分析結果
        media_performance: メディアタイプ別パフォーマンス
        post_length_performance: 投稿長別パフォーマンス

    Returns:
        PostRecommendation: 投稿レコメンデーション
    """
    # 効果的なハッシュタグを取得
    effective_hashtags = [t.hashtag for t in hashtag_analysis[:5] if t.usage_count >= 2]

    # 理由の説明を生成
    hour_strs = [f"{h}時" for h in best_hours]
    hours_text = "、".join(hour_strs)
    days_text = "、".join(best_days)

    reasoning_parts = [
        f"LinkedIn分析の結果、{hours_text}の投稿が最もエンゲージメントが高い傾向にあります。",
        f"B2Bプラットフォームとして、最も効果的な曜日は{days_text}です。",
        f"平均いいね数は{metrics.avg_likes_per_post}、",
        f"平均コメント数は{metrics.avg_comments_per_post}、",
        f"CTRは{metrics.click_through_rate}%です。",
    ]

    if effective_hashtags:
        reasoning_parts.append(
            f"効果的なハッシュタグ: #{', #'.join(effective_hashtags[:3])}。"
        )

    if media_performance:
        best_media = max(media_performance.items(), key=lambda x: x[1])
        media_type_names = {
            "NONE": "テキストのみ",
            "IMAGE": "画像",
            "VIDEO": "動画",
            "DOCUMENT": "ドキュメント",
            "ARTICLE": "記事リンク",
        }
        media_name = media_type_names.get(best_media[0], best_media[0])
        reasoning_parts.append(
            f"最も効果的なメディアタイプは「{media_name}」"
            f"（平均エンゲージメント: {best_media[1]}）です。"
        )

    if content_patterns:
        best_pattern = content_patterns[0]
        pattern_names = {
            "thought_leadership": "ソートリーダーシップ",
            "career": "キャリア/採用",
            "industry_news": "業界ニュース",
            "tips": "ノウハウ/Tips",
            "achievement": "実績報告",
            "networking": "ネットワーキング",
            "question": "質問形式",
            "listicle": "リスト形式",
            "personal_story": "個人ストーリー",
            "engagement_bait": "エンゲージメント促進",
        }
        pattern_name = pattern_names.get(
            best_pattern.pattern_type, best_pattern.pattern_type
        )
        reasoning_parts.append(
            f"最も効果的なコンテンツ形式は「{pattern_name}」"
            f"（平均エンゲージメント: {best_pattern.avg_engagement}）です。"
        )

    if post_length_performance:
        best_length = max(post_length_performance.items(), key=lambda x: x[1])
        length_names = {
            "short": "短文（〜150文字）",
            "medium": "中程度（150〜500文字）",
            "long": "長文（500〜1500文字）",
            "very_long": "超長文（1500文字以上）",
        }
        length_name = length_names.get(best_length[0], best_length[0])
        reasoning_parts.append(
            f"最も効果的な投稿長は「{length_name}」です。"
        )

    # コンテンツアイデア生成
    content_ideas = []
    if content_patterns:
        for pattern in content_patterns[:3]:
            pattern_ideas = {
                "thought_leadership": "業界の知見やリーダーシップを示す投稿をする",
                "career": "キャリアに関する投稿や採用情報を共有する",
                "industry_news": "業界ニュースや最新動向を共有する",
                "tips": "実用的なノウハウやTipsを投稿する",
                "achievement": "成果やマイルストーンを報告する",
                "networking": "イベントやカンファレンス参加を共有する",
                "question": "質問形式でフォロワーの意見を求める",
                "listicle": "リスト形式でわかりやすくまとめる",
                "personal_story": "自分の経験や学びをストーリーで伝える",
                "engagement_bait": "コメントやシェアを促す投稿をする",
            }
            idea = pattern_ideas.get(pattern.pattern_type)
            if idea and idea not in content_ideas:
                content_ideas.append(idea)

    # B2B固有の推奨事項を追加
    content_ideas.append("平日の業務時間内に投稿する（特に火〜木曜日）")

    return PostRecommendation(
        best_hours=best_hours,
        suggested_hashtags=effective_hashtags,
        content_ideas=content_ideas,
        reasoning="".join(reasoning_parts),
    )


def analyze_linkedin_posts(
    posts: list[LinkedInPost],
    articles: Optional[list[LinkedInArticle]] = None,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
) -> LinkedInAnalysisResult:
    """LinkedIn投稿を総合分析

    Args:
        posts: 投稿リスト
        articles: 記事リスト（オプション）
        period_start: 分析期間開始
        period_end: 分析期間終了

    Returns:
        LinkedInAnalysisResult: 分析結果
    """
    if not posts:
        now = datetime.now(UTC)
        return LinkedInAnalysisResult(
            period_start=period_start or now,
            period_end=period_end or now,
            total_posts=0,
            metrics=LinkedInEngagementMetrics(),
        )

    # 期間を決定
    all_dates = [p.created_at for p in posts]
    actual_start = period_start or min(all_dates)
    actual_end = period_end or max(all_dates)

    # 各分析を実行
    metrics = calculate_linkedin_metrics(posts)
    hourly_breakdown = analyze_linkedin_hourly(posts)
    daily_breakdown = analyze_linkedin_daily(posts)
    top_posts = get_top_linkedin_posts(posts)
    best_hours = find_linkedin_best_hours(hourly_breakdown)
    best_days = find_linkedin_best_days(daily_breakdown)

    # コンテンツ分析
    hashtag_results = analyze_linkedin_hashtags(posts)
    pattern_results = analyze_linkedin_patterns(posts)
    media_performance = analyze_media_type_performance(posts)
    avg_post_length, length_performance = analyze_post_length(posts)

    # レコメンデーション生成
    recommendations = _generate_linkedin_recommendations(
        metrics,
        best_hours,
        best_days,
        hashtag_results,
        pattern_results,
        media_performance,
        length_performance,
    )

    # 記事処理
    top_articles = []
    article_count = 0
    if articles:
        article_count = len(articles)
        # 記事のソート
        sorted_articles = sorted(
            articles,
            key=lambda a: a.likes + a.comments * 5 + a.shares * 10,
            reverse=True,
        )
        top_articles = sorted_articles[:5]

    logger.info(f"{len(posts)}件のLinkedIn投稿を分析しました")

    return LinkedInAnalysisResult(
        period_start=actual_start,
        period_end=actual_end,
        total_posts=len(posts),
        total_articles=article_count,
        metrics=metrics,
        hourly_breakdown=hourly_breakdown,
        daily_breakdown=daily_breakdown,
        top_performing_posts=top_posts,
        top_performing_articles=top_articles,
        recommendations=recommendations,
        hashtag_analysis=hashtag_results,
        content_patterns=pattern_results,
        best_posting_days=best_days,
        avg_post_length=round(avg_post_length, 2),
        media_type_performance=media_performance,
    )
