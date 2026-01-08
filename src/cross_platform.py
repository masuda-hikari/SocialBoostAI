"""
クロスプラットフォーム比較分析モジュール

Twitter/Instagramの分析結果を比較し、
プラットフォーム間のパフォーマンス差異と戦略的インサイトを提供する。
"""

import logging
from datetime import UTC, datetime
from typing import Optional

from .models import (
    AnalysisResult,
    CrossPlatformComparison,
    InstagramAnalysisResult,
    PlatformComparisonItem,
    PlatformPerformance,
    PlatformType,
)

logger = logging.getLogger(__name__)


def extract_twitter_performance(
    analysis: AnalysisResult,
) -> PlatformPerformance:
    """Twitter分析結果からパフォーマンス指標を抽出

    Args:
        analysis: Twitter分析結果

    Returns:
        PlatformPerformance: プラットフォームパフォーマンス
    """
    metrics = analysis.metrics
    total_engagement = (
        metrics.total_likes + metrics.total_retweets + metrics.total_replies
    )

    # 最適投稿時間を取得
    best_hour = None
    if analysis.hourly_breakdown:
        sorted_hours = sorted(
            analysis.hourly_breakdown, key=lambda h: h.total_engagement, reverse=True
        )
        if sorted_hours and sorted_hours[0].post_count > 0:
            best_hour = sorted_hours[0].hour

    # トップハッシュタグを取得
    top_hashtags = [h.hashtag for h in analysis.hashtag_analysis[:5]]

    # コンテンツインサイトを生成
    content_insights = []
    if analysis.content_patterns:
        top_pattern = analysis.content_patterns[0]
        pattern_names = {
            "question": "質問形式",
            "tip": "Tips/ノウハウ",
            "announcement": "お知らせ",
            "engagement_bait": "エンゲージメント促進",
        }
        pattern_name = pattern_names.get(
            top_pattern.pattern_type, top_pattern.pattern_type
        )
        content_insights.append(
            f"最も効果的なコンテンツ: {pattern_name}（平均エンゲージメント: {top_pattern.avg_engagement}）"
        )

    return PlatformPerformance(
        platform=PlatformType.TWITTER,
        total_posts=analysis.total_posts,
        total_engagement=total_engagement,
        avg_engagement_rate=metrics.engagement_rate,
        avg_likes_per_post=metrics.avg_likes_per_post,
        avg_comments_per_post=round(
            metrics.total_replies / max(1, analysis.total_posts), 2
        ),
        avg_shares_per_post=metrics.avg_retweets_per_post,
        best_hour=best_hour,
        top_hashtags=top_hashtags,
        content_insights=content_insights,
    )


def extract_instagram_performance(
    analysis: InstagramAnalysisResult,
) -> PlatformPerformance:
    """Instagram分析結果からパフォーマンス指標を抽出

    Args:
        analysis: Instagram分析結果

    Returns:
        PlatformPerformance: プラットフォームパフォーマンス
    """
    metrics = analysis.metrics
    total_engagement = (
        metrics.total_likes + metrics.total_comments + metrics.total_saves
    )

    # 最適投稿時間を取得
    best_hour = None
    if analysis.hourly_breakdown:
        sorted_hours = sorted(
            analysis.hourly_breakdown, key=lambda h: h.total_engagement, reverse=True
        )
        if sorted_hours and sorted_hours[0].post_count > 0:
            best_hour = sorted_hours[0].hour

    # トップハッシュタグを取得
    top_hashtags = [h.hashtag for h in analysis.hashtag_analysis[:5]]

    # コンテンツインサイトを生成
    content_insights = []
    if analysis.content_patterns:
        top_pattern = analysis.content_patterns[0]
        pattern_names = {
            "question": "質問形式",
            "tutorial": "チュートリアル/How-to",
            "behind_scenes": "舞台裏/メイキング",
            "engagement_bait": "エンゲージメント促進",
            "product": "商品紹介",
        }
        pattern_name = pattern_names.get(
            top_pattern.pattern_type, top_pattern.pattern_type
        )
        content_insights.append(
            f"最も効果的なコンテンツ: {pattern_name}（平均エンゲージメント: {top_pattern.avg_engagement}）"
        )

    return PlatformPerformance(
        platform=PlatformType.INSTAGRAM,
        total_posts=analysis.total_posts + analysis.total_reels,
        total_engagement=total_engagement,
        avg_engagement_rate=metrics.engagement_rate,
        avg_likes_per_post=metrics.avg_likes_per_post,
        avg_comments_per_post=metrics.avg_comments_per_post,
        avg_shares_per_post=round(
            metrics.total_shares / max(1, analysis.total_posts), 2
        ),
        best_hour=best_hour,
        top_hashtags=top_hashtags,
        content_insights=content_insights,
    )


def compare_metrics(
    twitter_perf: Optional[PlatformPerformance],
    instagram_perf: Optional[PlatformPerformance],
) -> list[PlatformComparisonItem]:
    """プラットフォーム間の指標を比較

    Args:
        twitter_perf: Twitterパフォーマンス
        instagram_perf: Instagramパフォーマンス

    Returns:
        list[PlatformComparisonItem]: 比較項目リスト
    """
    items: list[PlatformComparisonItem] = []

    def create_comparison(
        metric_name: str,
        twitter_val: Optional[float],
        instagram_val: Optional[float],
        insight_template: str,
    ) -> PlatformComparisonItem:
        """比較項目を作成"""
        winner = None
        diff_percent = None

        if twitter_val is not None and instagram_val is not None:
            if twitter_val > 0:
                diff_percent = round(
                    ((instagram_val - twitter_val) / twitter_val) * 100, 1
                )

            if abs((twitter_val or 0) - (instagram_val or 0)) < 0.01 * max(
                twitter_val or 1, instagram_val or 1
            ):
                winner = "tie"
                insight = f"{metric_name}: 両プラットフォームで同等のパフォーマンス"
            elif (twitter_val or 0) > (instagram_val or 0):
                winner = "twitter"
                insight = insight_template.format(
                    platform="Twitter", value=twitter_val, diff=abs(diff_percent or 0)
                )
            else:
                winner = "instagram"
                insight = insight_template.format(
                    platform="Instagram",
                    value=instagram_val,
                    diff=abs(diff_percent or 0),
                )
        elif twitter_val is not None:
            winner = "twitter"
            insight = f"{metric_name}: Twitterのみデータあり（{twitter_val}）"
        elif instagram_val is not None:
            winner = "instagram"
            insight = f"{metric_name}: Instagramのみデータあり（{instagram_val}）"
        else:
            insight = f"{metric_name}: データなし"

        return PlatformComparisonItem(
            metric_name=metric_name,
            twitter_value=twitter_val,
            instagram_value=instagram_val,
            difference_percent=diff_percent,
            winner=winner,
            insight=insight,
        )

    # 投稿数比較
    items.append(
        create_comparison(
            "投稿数",
            float(twitter_perf.total_posts) if twitter_perf else None,
            float(instagram_perf.total_posts) if instagram_perf else None,
            "{platform}の方が{diff:.0f}%多く投稿",
        )
    )

    # 総エンゲージメント比較
    items.append(
        create_comparison(
            "総エンゲージメント",
            float(twitter_perf.total_engagement) if twitter_perf else None,
            float(instagram_perf.total_engagement) if instagram_perf else None,
            "{platform}が{diff:.0f}%多いエンゲージメントを獲得",
        )
    )

    # エンゲージメント率比較
    items.append(
        create_comparison(
            "エンゲージメント率",
            twitter_perf.avg_engagement_rate if twitter_perf else None,
            instagram_perf.avg_engagement_rate if instagram_perf else None,
            "{platform}のエンゲージメント率が{diff:.1f}%高い",
        )
    )

    # 平均いいね数比較
    items.append(
        create_comparison(
            "平均いいね数",
            twitter_perf.avg_likes_per_post if twitter_perf else None,
            instagram_perf.avg_likes_per_post if instagram_perf else None,
            "{platform}の平均いいね数が{diff:.0f}%多い",
        )
    )

    # 平均コメント/リプライ数比較
    items.append(
        create_comparison(
            "平均コメント数",
            twitter_perf.avg_comments_per_post if twitter_perf else None,
            instagram_perf.avg_comments_per_post if instagram_perf else None,
            "{platform}のコメント/リプライが{diff:.0f}%多い",
        )
    )

    # 平均シェア/リツイート数比較
    items.append(
        create_comparison(
            "平均シェア数",
            twitter_perf.avg_shares_per_post if twitter_perf else None,
            instagram_perf.avg_shares_per_post if instagram_perf else None,
            "{platform}のシェア/RTが{diff:.0f}%多い",
        )
    )

    return items


def determine_overall_winner(
    comparison_items: list[PlatformComparisonItem],
) -> Optional[str]:
    """総合的な勝者を決定

    Args:
        comparison_items: 比較項目リスト

    Returns:
        Optional[str]: 勝者プラットフォーム（"twitter", "instagram", "tie"）
    """
    twitter_wins = 0
    instagram_wins = 0

    # 重要度に基づく重み付け
    weights = {
        "エンゲージメント率": 3,  # 最重要
        "総エンゲージメント": 2,
        "平均いいね数": 1,
        "平均コメント数": 1,
        "平均シェア数": 1,
        "投稿数": 0.5,  # 量より質を重視
    }

    for item in comparison_items:
        weight = weights.get(item.metric_name, 1)
        if item.winner == "twitter":
            twitter_wins += weight
        elif item.winner == "instagram":
            instagram_wins += weight

    if abs(twitter_wins - instagram_wins) < 0.5:
        return "tie"
    elif twitter_wins > instagram_wins:
        return "twitter"
    else:
        return "instagram"


def generate_cross_platform_insights(
    twitter_perf: Optional[PlatformPerformance],
    instagram_perf: Optional[PlatformPerformance],
    comparison_items: list[PlatformComparisonItem],
    overall_winner: Optional[str],
) -> list[str]:
    """クロスプラットフォームインサイトを生成

    Args:
        twitter_perf: Twitterパフォーマンス
        instagram_perf: Instagramパフォーマンス
        comparison_items: 比較項目リスト
        overall_winner: 総合勝者

    Returns:
        list[str]: インサイトリスト
    """
    insights: list[str] = []

    # 総合評価
    if overall_winner == "twitter":
        insights.append("📊 総合評価: Twitterがより高いパフォーマンスを示しています")
    elif overall_winner == "instagram":
        insights.append("📊 総合評価: Instagramがより高いパフォーマンスを示しています")
    else:
        insights.append("📊 総合評価: 両プラットフォームで同等のパフォーマンスです")

    # 投稿時間の比較
    if twitter_perf and instagram_perf:
        if twitter_perf.best_hour is not None and instagram_perf.best_hour is not None:
            if twitter_perf.best_hour == instagram_perf.best_hour:
                insights.append(
                    f"⏰ 最適投稿時間: 両プラットフォームとも{twitter_perf.best_hour}時が最適"
                )
            else:
                insights.append(
                    f"⏰ 最適投稿時間: Twitter={twitter_perf.best_hour}時、"
                    f"Instagram={instagram_perf.best_hour}時"
                )

    # ハッシュタグ戦略
    if twitter_perf and instagram_perf:
        common_hashtags = set(twitter_perf.top_hashtags) & set(
            instagram_perf.top_hashtags
        )
        if common_hashtags:
            insights.append(
                f"#️⃣ 共通の効果的ハッシュタグ: {', '.join(list(common_hashtags)[:3])}"
            )

    # エンゲージメント率の差異分析
    er_item = next(
        (i for i in comparison_items if i.metric_name == "エンゲージメント率"), None
    )
    if er_item and er_item.difference_percent:
        if abs(er_item.difference_percent) > 50:
            insights.append(
                f"⚠️ エンゲージメント率に大きな差異（{er_item.difference_percent:+.1f}%）があります"
            )

    return insights


def generate_strategic_recommendations(
    twitter_perf: Optional[PlatformPerformance],
    instagram_perf: Optional[PlatformPerformance],
    comparison_items: list[PlatformComparisonItem],
    overall_winner: Optional[str],
) -> list[str]:
    """戦略的レコメンデーションを生成

    Args:
        twitter_perf: Twitterパフォーマンス
        instagram_perf: Instagramパフォーマンス
        comparison_items: 比較項目リスト
        overall_winner: 総合勝者

    Returns:
        list[str]: レコメンデーションリスト
    """
    recommendations: list[str] = []

    # 主力プラットフォームの提案
    if overall_winner == "twitter":
        recommendations.append(
            "💡 Twitterを主力プラットフォームとして、コンテンツ投資を集中することを推奨"
        )
        if instagram_perf and instagram_perf.total_posts > 0:
            recommendations.append(
                "💡 Instagramは補助的に活用し、ビジュアルコンテンツの実験場として利用"
            )
    elif overall_winner == "instagram":
        recommendations.append(
            "💡 Instagramを主力プラットフォームとして、コンテンツ投資を集中することを推奨"
        )
        if twitter_perf and twitter_perf.total_posts > 0:
            recommendations.append(
                "💡 Twitterはリアルタイム発信・コミュニケーション用途に特化"
            )
    else:
        recommendations.append(
            "💡 両プラットフォームをバランス良く活用し、オーディエンス拡大を狙う"
        )

    # 投稿頻度の最適化
    if twitter_perf and instagram_perf:
        if twitter_perf.total_posts > instagram_perf.total_posts * 2:
            recommendations.append(
                "📈 Instagram投稿頻度の増加を検討（Twitterの半分以下です）"
            )
        elif instagram_perf.total_posts > twitter_perf.total_posts * 2:
            recommendations.append(
                "📈 Twitter投稿頻度の増加を検討（Instagramの半分以下です）"
            )

    # コンテンツ転用の提案
    recommendations.append(
        "🔄 高パフォーマンスコンテンツは形式を変えて他プラットフォームでも展開"
    )

    return recommendations


def generate_synergy_opportunities(
    twitter_perf: Optional[PlatformPerformance],
    instagram_perf: Optional[PlatformPerformance],
) -> list[str]:
    """プラットフォーム間連携の機会を提案

    Args:
        twitter_perf: Twitterパフォーマンス
        instagram_perf: Instagramパフォーマンス

    Returns:
        list[str]: 連携機会リスト
    """
    opportunities: list[str] = []

    opportunities.append(
        "🔗 Instagram投稿をTwitterでティーザー告知し、クロスフォローを促進"
    )
    opportunities.append(
        "🔗 Twitter限定情報をInstagramストーリーで共有し、フォロワー循環を構築"
    )

    if twitter_perf and instagram_perf:
        # 共通ハッシュタグ戦略
        common_tags = set(twitter_perf.top_hashtags) & set(instagram_perf.top_hashtags)
        if common_tags:
            opportunities.append(
                f"🔗 共通ハッシュタグ（{', '.join(list(common_tags)[:2])}）で"
                "ブランド統一感を強化"
            )

        # 投稿時間の統合
        if (
            twitter_perf.best_hour == instagram_perf.best_hour
            and twitter_perf.best_hour
        ):
            opportunities.append(
                f"🔗 {twitter_perf.best_hour}時に両プラットフォーム同時投稿で"
                "インパクト最大化"
            )

    return opportunities


def compare_platforms(
    twitter_analysis: Optional[AnalysisResult] = None,
    instagram_analysis: Optional[InstagramAnalysisResult] = None,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
) -> CrossPlatformComparison:
    """Twitter/Instagramの分析結果を比較

    Args:
        twitter_analysis: Twitter分析結果
        instagram_analysis: Instagram分析結果
        period_start: 比較期間開始
        period_end: 比較期間終了

    Returns:
        CrossPlatformComparison: クロスプラットフォーム比較結果
    """
    now = datetime.now(UTC)
    platforms_analyzed: list[str] = []

    # パフォーマンス抽出
    twitter_perf = None
    instagram_perf = None

    if twitter_analysis and twitter_analysis.total_posts > 0:
        twitter_perf = extract_twitter_performance(twitter_analysis)
        platforms_analyzed.append(PlatformType.TWITTER)
        period_start = period_start or twitter_analysis.period_start
        period_end = period_end or twitter_analysis.period_end

    if instagram_analysis and (
        instagram_analysis.total_posts > 0 or instagram_analysis.total_reels > 0
    ):
        instagram_perf = extract_instagram_performance(instagram_analysis)
        platforms_analyzed.append(PlatformType.INSTAGRAM)
        if not period_start:
            period_start = instagram_analysis.period_start
        if not period_end:
            period_end = instagram_analysis.period_end

    # 比較項目を生成
    comparison_items = compare_metrics(twitter_perf, instagram_perf)

    # 総合勝者を決定
    overall_winner = determine_overall_winner(comparison_items)

    # インサイトを生成
    cross_platform_insights = generate_cross_platform_insights(
        twitter_perf, instagram_perf, comparison_items, overall_winner
    )

    # 戦略的レコメンデーションを生成
    strategic_recommendations = generate_strategic_recommendations(
        twitter_perf, instagram_perf, comparison_items, overall_winner
    )

    # 連携機会を生成
    synergy_opportunities = generate_synergy_opportunities(twitter_perf, instagram_perf)

    logger.info(f"クロスプラットフォーム比較完了: {platforms_analyzed}")

    return CrossPlatformComparison(
        period_start=period_start or now,
        period_end=period_end or now,
        platforms_analyzed=platforms_analyzed,
        twitter_performance=twitter_perf,
        instagram_performance=instagram_perf,
        comparison_items=comparison_items,
        overall_winner=overall_winner,
        cross_platform_insights=cross_platform_insights,
        strategic_recommendations=strategic_recommendations,
        synergy_opportunities=synergy_opportunities,
    )
