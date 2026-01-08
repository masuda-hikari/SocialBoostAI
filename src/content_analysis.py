"""
コンテンツ分析モジュール - キーワード/ハッシュタグ効果分析
"""

import logging
import re
from collections import Counter, defaultdict
from typing import Optional

from .models import (
    ContentPattern,
    HashtagAnalysis,
    KeywordAnalysis,
    Tweet,
)

logger = logging.getLogger(__name__)

# 日本語ストップワード（分析から除外）
STOP_WORDS_JA = {
    "の",
    "に",
    "は",
    "を",
    "た",
    "が",
    "で",
    "て",
    "と",
    "し",
    "れ",
    "さ",
    "ある",
    "いる",
    "も",
    "する",
    "から",
    "な",
    "こと",
    "として",
    "い",
    "や",
    "れる",
    "など",
    "なっ",
    "ない",
    "この",
    "ため",
    "その",
    "あっ",
    "よう",
    "また",
    "もの",
    "という",
    "あり",
    "まで",
    "られ",
    "なる",
    "へ",
    "か",
    "だ",
    "これ",
    "によって",
    "により",
    "おり",
    "より",
    "による",
    "ず",
    "なり",
    "られる",
    "において",
    "ば",
    "なかっ",
    "なく",
    "しかし",
    "について",
    "せ",
    "だっ",
    "その後",
    "できる",
    "それ",
    "う",
    "ので",
    "なお",
    "のみ",
    "でき",
    "き",
    "つ",
    "における",
    "および",
    "いう",
    "さらに",
    "でも",
    "ら",
    "たり",
    "その他",
    "に関する",
    "たち",
    "ます",
    "ん",
    "なら",
    "に対して",
    "特に",
    "せる",
    "及び",
    "これら",
    "とき",
    "では",
    "にて",
    "ほか",
    "ながら",
    "うち",
    "そして",
    "とともに",
    "ただし",
    "かつて",
    "それぞれ",
    "または",
    "お",
    "ほど",
    "ものの",
    "に対する",
    "ほとんど",
    "と共に",
    "といった",
    "です",
    "とも",
    "ところ",
    "ここ",
    "あなた",
    "私",
    "僕",
    "俺",
    "彼",
    "彼女",
}

# 英語ストップワード
STOP_WORDS_EN = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "up",
    "about",
    "into",
    "through",
    "during",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "must",
    "shall",
    "can",
    "need",
    "dare",
    "ought",
    "used",
    "it",
    "its",
    "this",
    "that",
    "these",
    "those",
    "i",
    "you",
    "he",
    "she",
    "we",
    "they",
    "what",
    "which",
    "who",
    "when",
    "where",
    "why",
    "how",
    "all",
    "each",
    "every",
    "both",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "no",
    "nor",
    "not",
    "only",
    "own",
    "same",
    "so",
    "than",
    "too",
    "very",
    "just",
    "also",
    "now",
    "here",
    "there",
    "then",
    "once",
    "if",
    "my",
    "your",
    "our",
}

# コンテンツパターン検出用の正規表現
PATTERNS = {
    "question": [
        r"[？?]$",
        r"[？?]\s",
        r"どう思う",
        r"どうですか",
        r"皆さん",
        r"みなさん",
        r"教えて",
        r"質問",
    ],
    "tip": [
        r"Tips?[:：]",
        r"ポイント[:：]",
        r"コツ",
        r"方法",
        r"やり方",
        r"おすすめ",
        r"便利",
        r"裏技",
        r"\d+選",
        r"\d+つの",
    ],
    "announcement": [
        r"お知らせ",
        r"発表",
        r"リリース",
        r"新機能",
        r"アップデート",
        r"開始",
        r"公開",
        r"launch",
        r"release",
    ],
    "engagement_bait": [
        r"いいね",
        r"RT",
        r"リツイート",
        r"フォロー",
        r"シェア",
        r"拡散",
        r"保存",
    ],
}


def extract_hashtags(text: str) -> list[str]:
    """テキストからハッシュタグを抽出

    Args:
        text: ツイートテキスト

    Returns:
        list[str]: ハッシュタグリスト（#なし）
    """
    pattern = r"#([^\s#]+)"
    matches = re.findall(pattern, text)
    return [m.lower() for m in matches]


def extract_keywords(text: str, min_length: int = 2) -> list[str]:
    """テキストからキーワードを抽出

    Args:
        text: ツイートテキスト
        min_length: 最小文字数

    Returns:
        list[str]: キーワードリスト
    """
    # ハッシュタグ、メンション、URLを除去
    text = re.sub(r"#\S+", "", text)
    text = re.sub(r"@\S+", "", text)
    text = re.sub(r"https?://\S+", "", text)

    # 単語を抽出（日本語と英語両方対応）
    # 日本語: 連続する漢字・ひらがな・カタカナ
    # 英語: 連続するアルファベット
    words = re.findall(r"[一-龥ぁ-んァ-ン]+|[a-zA-Z]+", text)

    # フィルタリング
    keywords = []
    for word in words:
        word_lower = word.lower()
        if len(word) >= min_length:
            if word_lower not in STOP_WORDS_JA and word_lower not in STOP_WORDS_EN:
                keywords.append(word_lower)

    return keywords


def analyze_hashtags(tweets: list[Tweet]) -> list[HashtagAnalysis]:
    """ハッシュタグの効果を分析

    Args:
        tweets: ツイートリスト

    Returns:
        list[HashtagAnalysis]: ハッシュタグ分析結果リスト
    """
    if not tweets:
        return []

    hashtag_data: dict[str, dict] = defaultdict(
        lambda: {"count": 0, "likes": 0, "retweets": 0, "replies": 0}
    )

    # 全体の平均エンゲージメントを計算
    total_engagement = sum(t.likes + t.retweets + t.replies for t in tweets)
    avg_engagement = total_engagement / len(tweets) if tweets else 0

    # ハッシュタグごとのデータを集計
    for tweet in tweets:
        hashtags = extract_hashtags(tweet.text)
        engagement = tweet.likes + tweet.retweets + tweet.replies

        for tag in hashtags:
            hashtag_data[tag]["count"] += 1
            hashtag_data[tag]["likes"] += tweet.likes
            hashtag_data[tag]["retweets"] += tweet.retweets
            hashtag_data[tag]["replies"] += tweet.replies

    # 分析結果を作成
    results: list[HashtagAnalysis] = []
    for hashtag, data in hashtag_data.items():
        count = data["count"]
        total_likes = data["likes"]
        total_retweets = data["retweets"]
        total_replies = data["replies"]
        tag_engagement = total_likes + total_retweets + total_replies
        tag_avg_engagement = tag_engagement / count if count > 0 else 0

        # 効果スコア = (タグ付き平均エンゲージメント / 全体平均) * 使用頻度補正
        # 使用頻度が低いタグは信頼性が低いためペナルティ
        frequency_factor = min(1.0, count / 3)  # 3回以上で100%
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

    # 効果スコアでソート
    results.sort(key=lambda x: x.effectiveness_score, reverse=True)
    logger.info(f"{len(results)}個のハッシュタグを分析しました")

    return results


def analyze_keywords(
    tweets: list[Tweet],
    top_n: int = 20,
) -> list[KeywordAnalysis]:
    """キーワードの効果を分析

    Args:
        tweets: ツイートリスト
        top_n: 上位何件を返すか

    Returns:
        list[KeywordAnalysis]: キーワード分析結果リスト
    """
    if not tweets:
        return []

    keyword_data: dict[str, dict] = defaultdict(
        lambda: {"count": 0, "total_engagement": 0}
    )

    # 全体の平均エンゲージメントを計算
    total_engagement = sum(t.likes + t.retweets + t.replies for t in tweets)
    avg_engagement = total_engagement / len(tweets) if tweets else 0

    # キーワードごとのデータを集計
    for tweet in tweets:
        keywords = extract_keywords(tweet.text)
        engagement = tweet.likes + tweet.retweets + tweet.replies

        for keyword in set(keywords):  # 同一ツイート内の重複を除去
            keyword_data[keyword]["count"] += 1
            keyword_data[keyword]["total_engagement"] += engagement

    # 分析結果を作成
    results: list[KeywordAnalysis] = []
    for keyword, data in keyword_data.items():
        count = data["count"]
        if count < 2:  # 2回未満のキーワードは除外
            continue

        keyword_avg_engagement = data["total_engagement"] / count

        # 相関スコア（-1から1の範囲）
        # 平均より高ければ正、低ければ負
        if avg_engagement > 0:
            correlation = (keyword_avg_engagement - avg_engagement) / avg_engagement
            correlation = max(-1.0, min(1.0, correlation))  # クリップ
        else:
            correlation = 0.0

        results.append(
            KeywordAnalysis(
                keyword=keyword,
                frequency=count,
                avg_engagement=round(keyword_avg_engagement, 2),
                correlation_score=round(correlation, 2),
            )
        )

    # 相関スコアでソート
    results.sort(key=lambda x: x.correlation_score, reverse=True)
    logger.info(f"{len(results)}個のキーワードを分析しました")

    return results[:top_n]


def analyze_content_patterns(tweets: list[Tweet]) -> list[ContentPattern]:
    """コンテンツパターンを分析

    Args:
        tweets: ツイートリスト

    Returns:
        list[ContentPattern]: コンテンツパターン分析結果リスト
    """
    if not tweets:
        return []

    pattern_data: dict[str, dict] = {
        pattern_type: {"count": 0, "total_engagement": 0, "examples": []}
        for pattern_type in PATTERNS.keys()
    }

    for tweet in tweets:
        engagement = tweet.likes + tweet.retweets + tweet.replies

        for pattern_type, patterns in PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, tweet.text, re.IGNORECASE):
                    data = pattern_data[pattern_type]
                    data["count"] += 1
                    data["total_engagement"] += engagement
                    if len(data["examples"]) < 3:
                        data["examples"].append(tweet.text[:100])
                    break  # 1つのパターンにマッチしたら次のツイートへ

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

    # 平均エンゲージメントでソート
    results.sort(key=lambda x: x.avg_engagement, reverse=True)
    logger.info(f"{len(results)}個のコンテンツパターンを分析しました")

    return results


def get_effective_hashtag_recommendations(
    hashtag_analysis: list[HashtagAnalysis],
    top_n: int = 5,
    min_usage: int = 2,
) -> list[str]:
    """効果的なハッシュタグをレコメンド

    Args:
        hashtag_analysis: ハッシュタグ分析結果
        top_n: 上位何件を返すか
        min_usage: 最低使用回数

    Returns:
        list[str]: レコメンドハッシュタグリスト
    """
    filtered = [h for h in hashtag_analysis if h.usage_count >= min_usage]
    filtered.sort(key=lambda x: x.effectiveness_score, reverse=True)
    return [h.hashtag for h in filtered[:top_n]]


def get_high_engagement_keywords(
    keyword_analysis: list[KeywordAnalysis],
    top_n: int = 10,
) -> list[str]:
    """高エンゲージメントキーワードを取得

    Args:
        keyword_analysis: キーワード分析結果
        top_n: 上位何件を返すか

    Returns:
        list[str]: 高エンゲージメントキーワードリスト
    """
    positive = [k for k in keyword_analysis if k.correlation_score > 0]
    return [k.keyword for k in positive[:top_n]]
