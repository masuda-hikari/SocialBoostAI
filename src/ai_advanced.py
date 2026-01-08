"""
AI拡張機能モジュール - v0.3
トレンド分析、最適投稿時間AI分析、パーソナライズド提案、自動返信文案生成
"""

import logging
import os
import re
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv

from .content_analysis import (
    analyze_content_patterns,
    analyze_hashtags,
    analyze_keywords,
    get_effective_hashtag_recommendations,
    get_high_engagement_keywords,
)
from .models import (
    AnalysisResult,
    ContentPattern,
    HashtagAnalysis,
    HourlyEngagement,
    KeywordAnalysis,
    PostRecommendation,
    Tweet,
)

load_dotenv()

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """トレンド分析クラス"""

    def __init__(self) -> None:
        """初期化"""
        self._client = None

    def _get_client(self):
        """OpenAIクライアントを取得（遅延初期化）"""
        if self._client is None:
            try:
                from openai import OpenAI

                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY環境変数が設定されていません")

                self._client = OpenAI(api_key=api_key)
            except ImportError:
                raise ImportError("openaiパッケージがインストールされていません")
        return self._client

    def analyze_engagement_trends(
        self,
        tweets: list[Tweet],
        window_days: int = 7,
    ) -> dict:
        """エンゲージメントトレンドを分析

        Args:
            tweets: ツイートリスト
            window_days: 分析ウィンドウ（日数）

        Returns:
            dict: トレンド分析結果
        """
        if not tweets:
            return {"trend": "insufficient_data", "insights": []}

        # 日付でソート
        sorted_tweets = sorted(tweets, key=lambda t: t.created_at)

        # 日別エンゲージメント集計
        daily_engagement: dict[str, list[int]] = {}
        for tweet in sorted_tweets:
            date_key = tweet.created_at.strftime("%Y-%m-%d")
            engagement = tweet.likes + tweet.retweets + tweet.replies
            if date_key not in daily_engagement:
                daily_engagement[date_key] = []
            daily_engagement[date_key].append(engagement)

        # 日別平均エンゲージメント
        daily_avg = {
            date: sum(values) / len(values) for date, values in daily_engagement.items()
        }

        dates = sorted(daily_avg.keys())
        if len(dates) < 2:
            return {"trend": "insufficient_data", "insights": []}

        # トレンド判定（前半vs後半）
        mid = len(dates) // 2
        first_half_avg = sum(daily_avg[d] for d in dates[:mid]) / mid if mid > 0 else 0
        second_half_avg = (
            sum(daily_avg[d] for d in dates[mid:]) / (len(dates) - mid)
            if len(dates) - mid > 0
            else 0
        )

        if second_half_avg > first_half_avg * 1.1:
            trend = "increasing"
        elif second_half_avg < first_half_avg * 0.9:
            trend = "decreasing"
        else:
            trend = "stable"

        insights = []
        if trend == "increasing":
            insights.append(
                "エンゲージメントが上昇傾向にあります。現在の戦略を継続してください。"
            )
        elif trend == "decreasing":
            insights.append(
                "エンゲージメントが下降傾向にあります。コンテンツ戦略の見直しを検討してください。"
            )
        else:
            insights.append(
                "エンゲージメントは安定しています。新しい試みでブレイクスルーを狙いましょう。"
            )

        return {
            "trend": trend,
            "first_half_avg": round(first_half_avg, 2),
            "second_half_avg": round(second_half_avg, 2),
            "change_percent": round(
                (
                    (second_half_avg - first_half_avg) / first_half_avg * 100
                    if first_half_avg > 0
                    else 0
                ),
                2,
            ),
            "insights": insights,
        }

    def identify_viral_patterns(
        self,
        tweets: list[Tweet],
        threshold_percentile: float = 90,
    ) -> list[dict]:
        """バイラル投稿のパターンを特定

        Args:
            tweets: ツイートリスト
            threshold_percentile: バイラルと判定するパーセンタイル

        Returns:
            list[dict]: バイラルパターンリスト
        """
        if not tweets:
            return []

        # エンゲージメントスコア計算
        engagements = [t.likes + t.retweets + t.replies for t in tweets]
        if not engagements:
            return []

        sorted_eng = sorted(engagements)
        threshold_idx = int(len(sorted_eng) * threshold_percentile / 100)
        threshold = sorted_eng[min(threshold_idx, len(sorted_eng) - 1)]

        # バイラル投稿を抽出
        viral_tweets = [
            t
            for t in tweets
            if t.likes + t.retweets + t.replies >= threshold and threshold > 0
        ]

        if not viral_tweets:
            return []

        patterns = []

        # 時間帯パターン
        hours = [t.created_at.hour for t in viral_tweets]
        if hours:
            from collections import Counter

            hour_counts = Counter(hours)
            most_common_hour = hour_counts.most_common(1)[0][0]
            patterns.append(
                {
                    "type": "timing",
                    "pattern": f"{most_common_hour}時台",
                    "description": f"バイラル投稿の多くが{most_common_hour}時台に投稿されています",
                }
            )

        # 文字数パターン
        lengths = [len(t.text) for t in viral_tweets]
        avg_length = sum(lengths) / len(lengths) if lengths else 0
        patterns.append(
            {
                "type": "length",
                "pattern": f"約{int(avg_length)}文字",
                "description": f"バイラル投稿の平均文字数は{int(avg_length)}文字です",
            }
        )

        # ハッシュタグパターン
        hashtag_counts = [len(re.findall(r"#\S+", t.text)) for t in viral_tweets]
        avg_hashtags = (
            sum(hashtag_counts) / len(hashtag_counts) if hashtag_counts else 0
        )
        patterns.append(
            {
                "type": "hashtags",
                "pattern": f"約{round(avg_hashtags, 1)}個",
                "description": f"バイラル投稿の平均ハッシュタグ数は{round(avg_hashtags, 1)}個です",
            }
        )

        logger.info(
            f"{len(viral_tweets)}件のバイラル投稿から{len(patterns)}個のパターンを特定"
        )
        return patterns


class OptimalTimingAnalyzer:
    """最適投稿時間AI分析クラス"""

    def __init__(self) -> None:
        """初期化"""
        self._client = None

    def _get_client(self):
        """OpenAIクライアントを取得（遅延初期化）"""
        if self._client is None:
            try:
                from openai import OpenAI

                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY環境変数が設定されていません")

                self._client = OpenAI(api_key=api_key)
            except ImportError:
                raise ImportError("openaiパッケージがインストールされていません")
        return self._client

    def analyze_optimal_times(
        self,
        hourly_breakdown: list[HourlyEngagement],
        target_audience: Optional[str] = None,
    ) -> dict:
        """最適投稿時間を分析

        Args:
            hourly_breakdown: 時間帯別エンゲージメント
            target_audience: ターゲット層（例: "ビジネスパーソン", "学生"）

        Returns:
            dict: 最適時間分析結果
        """
        if not hourly_breakdown:
            return {
                "best_times": [],
                "worst_times": [],
                "recommendations": [],
            }

        # エンゲージメントでソート
        sorted_hours = sorted(
            hourly_breakdown,
            key=lambda h: h.total_engagement,
            reverse=True,
        )

        # 上位3時間帯と下位3時間帯
        best_hours = [h.hour for h in sorted_hours[:3]]
        worst_hours = [h.hour for h in sorted_hours[-3:] if h.post_count > 0]

        recommendations = []

        # 基本的な推奨
        if best_hours:
            time_ranges = self._hours_to_time_ranges(best_hours)
            recommendations.append(f"最も効果的な投稿時間: {', '.join(time_ranges)}")

        # 曜日×時間帯の組み合わせ推奨（簡易版）
        if 7 <= best_hours[0] <= 9:
            recommendations.append(
                "朝の通勤時間帯が効果的です。仕事前のユーザーにリーチしています。"
            )
        elif 12 <= best_hours[0] <= 13:
            recommendations.append(
                "昼休み時間帯が効果的です。休憩中のユーザーにリーチしています。"
            )
        elif 18 <= best_hours[0] <= 21:
            recommendations.append(
                "夜のゴールデンタイムが効果的です。リラックスタイムのユーザーにリーチしています。"
            )
        elif 22 <= best_hours[0] or best_hours[0] <= 1:
            recommendations.append(
                "深夜帯が効果的です。夜型ユーザーにリーチしています。"
            )

        # 避けるべき時間帯
        if worst_hours:
            worst_ranges = self._hours_to_time_ranges(worst_hours)
            recommendations.append(f"避けるべき時間帯: {', '.join(worst_ranges)}")

        return {
            "best_times": best_hours,
            "worst_times": worst_hours,
            "recommendations": recommendations,
            "hourly_stats": [
                {
                    "hour": h.hour,
                    "engagement": h.total_engagement,
                    "post_count": h.post_count,
                }
                for h in sorted_hours
            ],
        }

    def _hours_to_time_ranges(self, hours: list[int]) -> list[str]:
        """時間をわかりやすい時間帯表記に変換"""
        return [f"{h}:00-{(h+1)%24}:00" for h in hours]

    def get_ai_timing_insights(
        self,
        hourly_breakdown: list[HourlyEngagement],
        content_patterns: list[ContentPattern],
    ) -> str:
        """AIによる投稿タイミング洞察を生成

        Args:
            hourly_breakdown: 時間帯別エンゲージメント
            content_patterns: コンテンツパターン

        Returns:
            str: AI分析による洞察
        """
        client = self._get_client()

        # データをテキスト形式に変換
        hourly_data = "\n".join(
            [
                f"- {h.hour}時: 平均いいね{h.avg_likes:.1f}, 平均RT{h.avg_retweets:.1f}, 投稿数{h.post_count}"
                for h in sorted(hourly_breakdown, key=lambda x: x.hour)
            ]
        )

        pattern_data = "\n".join(
            [
                f"- {p.pattern_type}: 平均エンゲージメント{p.avg_engagement:.1f}, 件数{p.count}"
                for p in content_patterns
            ]
        )

        prompt = f"""以下のソーシャルメディアのパフォーマンスデータを分析し、投稿タイミングに関する具体的な提案を3つ提供してください。

時間帯別パフォーマンス:
{hourly_data}

コンテンツタイプ別パフォーマンス:
{pattern_data}

要件:
1. 具体的な時間帯を示すこと
2. なぜその時間帯が効果的かの理由を含めること
3. コンテンツタイプとの組み合わせ提案を含めること
4. 簡潔に（各提案2-3文程度）

形式:
1. [提案1]
2. [提案2]
3. [提案3]
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "あなたはソーシャルメディアマーケティングの専門家です。データに基づいた具体的なアドバイスを提供します。",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.7,
        )

        return response.choices[0].message.content or ""


class PersonalizedRecommender:
    """パーソナライズド提案クラス"""

    def __init__(self) -> None:
        """初期化"""
        self._client = None

    def _get_client(self):
        """OpenAIクライアントを取得（遅延初期化）"""
        if self._client is None:
            try:
                from openai import OpenAI

                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY環境変数が設定されていません")

                self._client = OpenAI(api_key=api_key)
            except ImportError:
                raise ImportError("openaiパッケージがインストールされていません")
        return self._client

    def generate_personalized_strategy(
        self,
        analysis_result: AnalysisResult,
        goals: Optional[list[str]] = None,
    ) -> dict:
        """パーソナライズされた戦略を生成

        Args:
            analysis_result: 分析結果
            goals: ユーザーの目標（例: ["フォロワー増加", "エンゲージメント向上"]）

        Returns:
            dict: パーソナライズされた戦略
        """
        client = self._get_client()

        # 分析データをまとめる
        metrics = analysis_result.metrics
        top_posts = analysis_result.top_performing_posts[:5]
        hashtag_analysis = analysis_result.hashtag_analysis[:5]
        keyword_analysis = analysis_result.keyword_analysis[:5]
        patterns = analysis_result.content_patterns

        # コンテキスト情報
        context = f"""
分析期間: {analysis_result.period_start.strftime('%Y-%m-%d')} - {analysis_result.period_end.strftime('%Y-%m-%d')}
総投稿数: {analysis_result.total_posts}

エンゲージメント指標:
- 総いいね数: {metrics.total_likes}
- 総リツイート数: {metrics.total_retweets}
- エンゲージメント率: {metrics.engagement_rate:.2%}
- 投稿あたり平均いいね: {metrics.avg_likes_per_post:.1f}

トップパフォーマンス投稿:
{chr(10).join([f'- {t.text[:80]}... (いいね: {t.likes}, RT: {t.retweets})' for t in top_posts])}

効果的なハッシュタグ:
{chr(10).join([f'- #{h.hashtag} (効果スコア: {h.effectiveness_score})' for h in hashtag_analysis])}

高エンゲージメントキーワード:
{chr(10).join([f'- {k.keyword} (相関: {k.correlation_score})' for k in keyword_analysis])}

コンテンツパターン:
{chr(10).join([f'- {p.pattern_type}: 平均エンゲージメント {p.avg_engagement}' for p in patterns])}
"""

        goals_text = f"ユーザーの目標: {', '.join(goals)}" if goals else ""

        prompt = f"""以下のソーシャルメディア分析データに基づいて、パーソナライズされた成長戦略を提案してください。

{context}

{goals_text}

以下の形式で回答してください:

## 強み
- [分析から特定された強み]

## 改善点
- [改善すべきポイント]

## 具体的なアクションプラン
1. [短期（1週間）で実行すべきこと]
2. [中期（1ヶ月）で達成すべき目標]
3. [継続的に行うべき習慣]

## コンテンツカレンダー提案
- [曜日/時間帯別の投稿計画]
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "あなたはソーシャルメディアグロースハッカーです。データに基づいた実践的な戦略を提案します。",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=1500,
            temperature=0.7,
        )

        strategy_text = response.choices[0].message.content or ""

        return {
            "strategy": strategy_text,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "based_on_posts": analysis_result.total_posts,
        }


class ReplyGenerator:
    """自動返信文案生成クラス"""

    def __init__(self) -> None:
        """初期化"""
        self._client = None

    def _get_client(self):
        """OpenAIクライアントを取得（遅延初期化）"""
        if self._client is None:
            try:
                from openai import OpenAI

                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY環境変数が設定されていません")

                self._client = OpenAI(api_key=api_key)
            except ImportError:
                raise ImportError("openaiパッケージがインストールされていません")
        return self._client

    def generate_reply_drafts(
        self,
        original_tweet: str,
        context: Optional[str] = None,
        tone: str = "friendly",
        count: int = 3,
    ) -> list[dict]:
        """返信文案を生成

        Args:
            original_tweet: 元のツイート
            context: 追加コンテキスト（自分のブランド情報など）
            tone: トーン（friendly, professional, casual, humorous）
            count: 生成する文案数

        Returns:
            list[dict]: 返信文案リスト
        """
        client = self._get_client()

        tone_descriptions = {
            "friendly": "フレンドリーで親しみやすい",
            "professional": "プロフェッショナルで丁寧な",
            "casual": "カジュアルでラフな",
            "humorous": "ユーモラスで面白い",
        }

        tone_desc = tone_descriptions.get(tone, tone_descriptions["friendly"])

        prompt = f"""以下のツイートに対する{tone_desc}トーンの返信を{count}パターン生成してください。

元のツイート:
{original_tweet}

{f'コンテキスト: {context}' if context else ''}

要件:
- 280文字以内
- 自然な会話調
- エンゲージメントを促す要素を含める
- スパム的な表現は避ける
- 必要に応じて絵文字を使用

形式:
1. [返信案1]
---
2. [返信案2]
---
3. [返信案3]
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "あなたはソーシャルメディアのコミュニケーション専門家です。自然で効果的な返信を作成します。",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=800,
            temperature=0.8,
        )

        content = response.choices[0].message.content or ""

        # 返信案をパース
        drafts = []
        parts = content.split("---")
        for part in parts:
            part = part.strip()
            if part:
                # 番号を除去
                lines = part.split("\n")
                for line in lines:
                    line = line.strip()
                    if line and not line[0].isdigit():
                        drafts.append({"text": line, "tone": tone})
                        break
                    elif line and line[0].isdigit() and "." in line:
                        text = line.split(".", 1)[1].strip()
                        if text:
                            drafts.append({"text": text, "tone": tone})
                            break

        logger.info(f"{len(drafts)}件の返信文案を生成しました")
        return drafts[:count]

    def generate_engagement_replies(
        self,
        mentions: list[Tweet],
        brand_voice: Optional[str] = None,
    ) -> list[dict]:
        """メンションに対する返信案を一括生成

        Args:
            mentions: メンション（返信対象）のツイートリスト
            brand_voice: ブランドボイスの説明

        Returns:
            list[dict]: 返信案リスト（元ツイートIDと返信文のペア）
        """
        results = []
        for mention in mentions[:10]:  # 最大10件まで
            try:
                drafts = self.generate_reply_drafts(
                    original_tweet=mention.text,
                    context=brand_voice,
                    count=1,
                )
                if drafts:
                    results.append(
                        {
                            "original_tweet_id": mention.id,
                            "original_text": mention.text[:100],
                            "suggested_reply": drafts[0]["text"],
                        }
                    )
            except Exception as e:
                logger.warning(f"返信生成に失敗: {e}")

        return results


class AdvancedAISuggester:
    """AI拡張提案統合クラス"""

    def __init__(self) -> None:
        """初期化"""
        self.trend_analyzer = TrendAnalyzer()
        self.timing_analyzer = OptimalTimingAnalyzer()
        self.recommender = PersonalizedRecommender()
        self.reply_generator = ReplyGenerator()

    def generate_comprehensive_recommendations(
        self,
        tweets: list[Tweet],
        analysis_result: AnalysisResult,
        goals: Optional[list[str]] = None,
    ) -> dict:
        """包括的なAI提案を生成

        Args:
            tweets: ツイートリスト
            analysis_result: 分析結果
            goals: ユーザーの目標

        Returns:
            dict: 包括的なAI提案
        """
        recommendations = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "trends": None,
            "viral_patterns": None,
            "optimal_timing": None,
            "personalized_strategy": None,
            "errors": [],
        }

        # トレンド分析
        try:
            recommendations["trends"] = self.trend_analyzer.analyze_engagement_trends(
                tweets
            )
        except Exception as e:
            logger.error(f"トレンド分析に失敗: {e}")
            recommendations["errors"].append(f"トレンド分析: {str(e)}")

        # バイラルパターン分析
        try:
            recommendations["viral_patterns"] = (
                self.trend_analyzer.identify_viral_patterns(tweets)
            )
        except Exception as e:
            logger.error(f"バイラルパターン分析に失敗: {e}")
            recommendations["errors"].append(f"バイラルパターン: {str(e)}")

        # 最適投稿時間分析
        try:
            recommendations["optimal_timing"] = (
                self.timing_analyzer.analyze_optimal_times(
                    analysis_result.hourly_breakdown
                )
            )
        except Exception as e:
            logger.error(f"最適時間分析に失敗: {e}")
            recommendations["errors"].append(f"最適時間: {str(e)}")

        # パーソナライズド戦略（API呼び出しあり）
        try:
            recommendations["personalized_strategy"] = (
                self.recommender.generate_personalized_strategy(analysis_result, goals)
            )
        except Exception as e:
            logger.error(f"パーソナライズド戦略生成に失敗: {e}")
            recommendations["errors"].append(f"戦略生成: {str(e)}")

        return recommendations
