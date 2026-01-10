"""
AIコンテンツ生成モジュール - v1.6
マルチプラットフォーム対応のコンテンツ生成機能
"""

import logging
import os
import re
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

logger = logging.getLogger(__name__)


# =============================================================================
# 定数・型定義
# =============================================================================


class ContentPlatform(str, Enum):
    """対応プラットフォーム"""

    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    LINKEDIN = "linkedin"


class ContentType(str, Enum):
    """コンテンツタイプ"""

    POST = "post"  # 通常投稿
    THREAD = "thread"  # スレッド/連投
    STORY = "story"  # ストーリー
    REEL = "reel"  # リール/ショート動画
    VIDEO = "video"  # 長尺動画
    ARTICLE = "article"  # 記事（LinkedIn）
    CAPTION = "caption"  # キャプション


class ContentTone(str, Enum):
    """コンテンツトーン"""

    PROFESSIONAL = "professional"
    CASUAL = "casual"
    HUMOROUS = "humorous"
    EDUCATIONAL = "educational"
    INSPIRATIONAL = "inspirational"
    PROMOTIONAL = "promotional"


class ContentGoal(str, Enum):
    """コンテンツ目標"""

    ENGAGEMENT = "engagement"  # エンゲージメント獲得
    AWARENESS = "awareness"  # 認知度向上
    CONVERSION = "conversion"  # コンバージョン
    TRAFFIC = "traffic"  # トラフィック誘導
    COMMUNITY = "community"  # コミュニティ構築


# =============================================================================
# データモデル
# =============================================================================


class GeneratedContent(BaseModel):
    """生成されたコンテンツ"""

    id: str
    platform: ContentPlatform
    content_type: ContentType
    main_text: str
    hashtags: list[str] = []
    call_to_action: Optional[str] = None
    media_suggestion: Optional[str] = None
    estimated_engagement: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ContentVariation(BaseModel):
    """A/Bテスト用バリエーション"""

    version: str  # "A", "B", "C"
    text: str
    hashtags: list[str] = []
    focus: str  # バリエーションの特徴


class ContentCalendarItem(BaseModel):
    """投稿カレンダーアイテム"""

    scheduled_date: datetime
    platform: ContentPlatform
    content_type: ContentType
    topic: str
    draft_content: str
    hashtags: list[str] = []
    optimal_time: str
    rationale: str


class ContentGenerationRequest(BaseModel):
    """コンテンツ生成リクエスト"""

    platform: ContentPlatform
    content_type: ContentType = ContentType.POST
    topic: Optional[str] = None
    keywords: list[str] = []
    tone: ContentTone = ContentTone.CASUAL
    goal: ContentGoal = ContentGoal.ENGAGEMENT
    reference_content: Optional[str] = None  # 参考コンテンツ
    target_audience: Optional[str] = None
    include_hashtags: bool = True
    include_cta: bool = False
    max_length: Optional[int] = None


class ContentRewriteRequest(BaseModel):
    """コンテンツリライトリクエスト"""

    original_content: str
    source_platform: ContentPlatform
    target_platform: ContentPlatform
    preserve_hashtags: bool = False
    tone: Optional[ContentTone] = None


class ABTestRequest(BaseModel):
    """A/Bテストバリエーション生成リクエスト"""

    base_topic: str
    platform: ContentPlatform
    variation_count: int = Field(default=3, ge=2, le=5)
    tone: ContentTone = ContentTone.CASUAL


class ContentCalendarRequest(BaseModel):
    """コンテンツカレンダー生成リクエスト"""

    platforms: list[ContentPlatform]
    days: int = Field(default=7, ge=1, le=30)
    posts_per_day: int = Field(default=2, ge=1, le=5)
    topics: list[str] = []
    tone: ContentTone = ContentTone.CASUAL
    goal: ContentGoal = ContentGoal.ENGAGEMENT


# =============================================================================
# プラットフォーム固有設定
# =============================================================================

PLATFORM_LIMITS = {
    ContentPlatform.TWITTER: {
        "max_length": 280,
        "optimal_hashtags": 3,
        "best_times": ["7:00", "12:00", "18:00", "21:00"],
    },
    ContentPlatform.INSTAGRAM: {
        "max_length": 2200,
        "optimal_hashtags": 10,
        "best_times": ["11:00", "14:00", "19:00"],
    },
    ContentPlatform.TIKTOK: {
        "max_length": 2200,
        "optimal_hashtags": 5,
        "best_times": ["12:00", "15:00", "19:00", "21:00"],
    },
    ContentPlatform.YOUTUBE: {
        "max_length": 5000,  # 概要欄
        "optimal_hashtags": 3,
        "best_times": ["14:00", "16:00", "18:00"],
    },
    ContentPlatform.LINKEDIN: {
        "max_length": 3000,
        "optimal_hashtags": 5,
        "best_times": ["7:00", "12:00", "17:00"],
        "best_days": ["火曜日", "水曜日", "木曜日"],
    },
}

PLATFORM_GUIDELINES = {
    ContentPlatform.TWITTER: """
- 280文字以内
- 簡潔で印象的な文章
- 質問や意見を促す要素
- 適度な絵文字使用
- ハッシュタグは2-3個
""",
    ContentPlatform.INSTAGRAM: """
- 視覚的な要素を意識
- ストーリー性のある文章
- 改行を活用した読みやすさ
- ハッシュタグは5-10個
- CTAを含める
""",
    ContentPlatform.TIKTOK: """
- 短く印象的なフック
- トレンドを意識
- 若い世代向けの言葉遣い
- ハッシュタグは3-5個
- 動画の内容を補完
""",
    ContentPlatform.YOUTUBE: """
- SEOを意識したタイトル/概要
- キーワードを自然に含める
- チャプター用タイムスタンプ
- 関連動画への誘導
- チャンネル登録促進
""",
    ContentPlatform.LINKEDIN: """
- プロフェッショナルなトーン
- ビジネス価値を提供
- 業界キーワードを含める
- ストーリーテリング重視
- ネットワーキング促進
""",
}


# =============================================================================
# AIコンテンツジェネレーター
# =============================================================================


class AIContentGenerator:
    """AIコンテンツ生成クラス"""

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

    def generate_content(
        self,
        request: ContentGenerationRequest,
    ) -> GeneratedContent:
        """コンテンツを生成

        Args:
            request: コンテンツ生成リクエスト

        Returns:
            GeneratedContent: 生成されたコンテンツ
        """
        client = self._get_client()
        platform_config = PLATFORM_LIMITS.get(request.platform, {})
        max_length = request.max_length or platform_config.get("max_length", 280)
        guidelines = PLATFORM_GUIDELINES.get(request.platform, "")

        # プロンプト構築
        prompt = f"""以下の条件で{request.platform.value}向けのコンテンツを作成してください。

## 条件
- コンテンツタイプ: {request.content_type.value}
- トーン: {request.tone.value}
- 目標: {request.goal.value}
- 最大文字数: {max_length}文字
{"- トピック: " + request.topic if request.topic else ""}
{"- キーワード: " + ", ".join(request.keywords) if request.keywords else ""}
{"- ターゲット: " + request.target_audience if request.target_audience else ""}
{"- 参考: " + request.reference_content[:200] + "..." if request.reference_content else ""}

## プラットフォームガイドライン
{guidelines}

## 出力形式
以下の形式で出力してください:

【本文】
(コンテンツ本文)

【ハッシュタグ】
#タグ1 #タグ2 ...

【CTA】
(行動喚起の一文)

【メディア提案】
(推奨する画像/動画の説明)

【期待効果】
(期待されるエンゲージメント効果)
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": f"あなたは{request.platform.value}に精通したソーシャルメディアマーケターです。エンゲージメントを最大化するコンテンツを作成します。",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=1500,
            temperature=0.8,
        )

        content = response.choices[0].message.content or ""

        # レスポンスをパース
        parsed = self._parse_generated_content(content)

        return GeneratedContent(
            id=f"gen_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            platform=request.platform,
            content_type=request.content_type,
            main_text=parsed.get("main_text", ""),
            hashtags=parsed.get("hashtags", []) if request.include_hashtags else [],
            call_to_action=parsed.get("cta") if request.include_cta else None,
            media_suggestion=parsed.get("media_suggestion"),
            estimated_engagement=parsed.get("expected_effect"),
        )

    def _parse_generated_content(self, content: str) -> dict:
        """生成されたコンテンツをパース"""
        result = {
            "main_text": "",
            "hashtags": [],
            "cta": "",
            "media_suggestion": "",
            "expected_effect": "",
        }

        # セクション抽出
        sections = {
            "main_text": r"【本文】\s*([\s\S]*?)(?=【|$)",
            "hashtags": r"【ハッシュタグ】\s*([\s\S]*?)(?=【|$)",
            "cta": r"【CTA】\s*([\s\S]*?)(?=【|$)",
            "media_suggestion": r"【メディア提案】\s*([\s\S]*?)(?=【|$)",
            "expected_effect": r"【期待効果】\s*([\s\S]*?)(?=【|$)",
        }

        for key, pattern in sections.items():
            match = re.search(pattern, content)
            if match:
                value = match.group(1).strip()
                if key == "hashtags":
                    # ハッシュタグを抽出
                    result[key] = re.findall(r"#([^\s#]+)", value)
                else:
                    result[key] = value

        # 本文が見つからない場合、全体を本文とする
        if not result["main_text"] and content:
            result["main_text"] = content.split("【")[0].strip()

        return result

    def rewrite_for_platform(
        self,
        request: ContentRewriteRequest,
    ) -> GeneratedContent:
        """コンテンツを別プラットフォーム向けにリライト

        Args:
            request: リライトリクエスト

        Returns:
            GeneratedContent: リライトされたコンテンツ
        """
        client = self._get_client()
        target_config = PLATFORM_LIMITS.get(request.target_platform, {})
        target_guidelines = PLATFORM_GUIDELINES.get(request.target_platform, "")

        prompt = f"""以下のコンテンツを{request.source_platform.value}から{request.target_platform.value}向けにリライトしてください。

## 元のコンテンツ（{request.source_platform.value}）
{request.original_content}

## ターゲットプラットフォーム: {request.target_platform.value}
- 最大文字数: {target_config.get("max_length", 280)}文字
- 推奨ハッシュタグ数: {target_config.get("optimal_hashtags", 3)}個
{"- トーン: " + request.tone.value if request.tone else ""}

## ガイドライン
{target_guidelines}

## 要件
- 元のメッセージの本質を維持
- ターゲットプラットフォームの文化・スタイルに適応
- エンゲージメントを最大化する形式に変換

## 出力形式
【リライト後の本文】
(コンテンツ)

【ハッシュタグ】
#タグ1 #タグ2 ...

【変更ポイント】
(リライトで変更した主なポイント)
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "あなたはクロスプラットフォームコンテンツ戦略の専門家です。各プラットフォームの特性を理解し、最適化されたコンテンツを作成します。",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=0.7,
        )

        content = response.choices[0].message.content or ""

        # パース
        main_text = ""
        hashtags = []

        main_match = re.search(r"【リライト後の本文】\s*([\s\S]*?)(?=【|$)", content)
        if main_match:
            main_text = main_match.group(1).strip()

        hashtag_match = re.search(r"【ハッシュタグ】\s*([\s\S]*?)(?=【|$)", content)
        if hashtag_match:
            hashtags = re.findall(r"#([^\s#]+)", hashtag_match.group(1))

        # 元のハッシュタグを保持する場合
        if request.preserve_hashtags:
            original_hashtags = re.findall(r"#([^\s#]+)", request.original_content)
            hashtags = list(set(hashtags + original_hashtags))

        return GeneratedContent(
            id=f"rewrite_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            platform=request.target_platform,
            content_type=ContentType.POST,
            main_text=main_text,
            hashtags=hashtags,
        )

    def generate_ab_variations(
        self,
        request: ABTestRequest,
    ) -> list[ContentVariation]:
        """A/Bテスト用のバリエーションを生成

        Args:
            request: A/Bテストリクエスト

        Returns:
            list[ContentVariation]: バリエーションリスト
        """
        client = self._get_client()
        platform_config = PLATFORM_LIMITS.get(request.platform, {})
        guidelines = PLATFORM_GUIDELINES.get(request.platform, "")

        variation_labels = ["A", "B", "C", "D", "E"][:request.variation_count]

        prompt = f"""以下のトピックについて、A/Bテスト用に{request.variation_count}個のバリエーションを作成してください。

## トピック
{request.base_topic}

## プラットフォーム: {request.platform.value}
- 最大文字数: {platform_config.get("max_length", 280)}文字
- トーン: {request.tone.value}

## ガイドライン
{guidelines}

## 要件
各バリエーションは異なるアプローチで同じトピックを表現:
- バリエーションA: 質問形式（エンゲージメント重視）
- バリエーションB: 数字/データ重視（信頼性重視）
- バリエーションC: ストーリー/感情重視（共感重視）
{"- バリエーションD: FOMO/緊急性重視" if request.variation_count >= 4 else ""}
{"- バリエーションE: ユーモア/親しみやすさ重視" if request.variation_count >= 5 else ""}

## 出力形式（各バリエーション）
【バリエーション{variation_labels[0]}】
フォーカス: (このバリエーションの特徴)
本文: (コンテンツ)
ハッシュタグ: #タグ1 #タグ2

（以下同様）
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "あなたはソーシャルメディアマーケティングのA/Bテスト専門家です。効果的なバリエーションを作成します。",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=2000,
            temperature=0.9,
        )

        content = response.choices[0].message.content or ""

        # パース
        variations = []
        for label in variation_labels:
            pattern = rf"【バリエーション{label}】\s*([\s\S]*?)(?=【バリエーション|$)"
            match = re.search(pattern, content)
            if match:
                var_content = match.group(1)

                focus = ""
                text = ""
                hashtags = []

                focus_match = re.search(r"フォーカス:\s*(.+)", var_content)
                if focus_match:
                    focus = focus_match.group(1).strip()

                text_match = re.search(r"本文:\s*([\s\S]*?)(?=ハッシュタグ:|$)", var_content)
                if text_match:
                    text = text_match.group(1).strip()

                hashtag_match = re.search(r"ハッシュタグ:\s*(.+)", var_content)
                if hashtag_match:
                    hashtags = re.findall(r"#([^\s#]+)", hashtag_match.group(1))

                if text:
                    variations.append(
                        ContentVariation(
                            version=label,
                            text=text,
                            hashtags=hashtags,
                            focus=focus,
                        )
                    )

        return variations

    def generate_content_calendar(
        self,
        request: ContentCalendarRequest,
    ) -> list[ContentCalendarItem]:
        """投稿カレンダーを生成

        Args:
            request: カレンダー生成リクエスト

        Returns:
            list[ContentCalendarItem]: カレンダーアイテムリスト
        """
        client = self._get_client()

        platforms_info = "\n".join(
            [
                f"- {p.value}: 最適時間{PLATFORM_LIMITS.get(p, {}).get('best_times', [])}"
                for p in request.platforms
            ]
        )

        topics_text = ", ".join(request.topics) if request.topics else "自動選定"

        prompt = f"""以下の条件で{request.days}日分の投稿カレンダーを作成してください。

## 条件
- プラットフォーム: {", ".join([p.value for p in request.platforms])}
- 期間: {request.days}日間
- 1日あたりの投稿数: {request.posts_per_day}
- トピック: {topics_text}
- トーン: {request.tone.value}
- 目標: {request.goal.value}

## プラットフォーム別最適時間
{platforms_info}

## 要件
- 各日付に{request.posts_per_day}件の投稿を計画
- プラットフォーム間でトピックを分散
- 週末と平日で適切なコンテンツを調整
- 各投稿に適切なハッシュタグを含める

## 出力形式（1投稿あたり）
【日付】YYYY-MM-DD
【時間】HH:MM
【プラットフォーム】(platform)
【タイプ】(post/story/reel/video/article)
【トピック】(トピック概要)
【下書き】(投稿内容)
【ハッシュタグ】#tag1 #tag2
【理由】(この日時・内容を選んだ理由)
---

開始日: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "あなたはソーシャルメディアコンテンツプランナーです。戦略的な投稿カレンダーを作成します。",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=4000,
            temperature=0.7,
        )

        content = response.choices[0].message.content or ""

        # パース
        calendar_items = []
        entries = content.split("---")

        for entry in entries:
            if not entry.strip():
                continue

            date_match = re.search(r"【日付】\s*(\d{4}-\d{2}-\d{2})", entry)
            time_match = re.search(r"【時間】\s*(\d{2}:\d{2})", entry)
            platform_match = re.search(r"【プラットフォーム】\s*(\w+)", entry)
            type_match = re.search(r"【タイプ】\s*(\w+)", entry)
            topic_match = re.search(r"【トピック】\s*(.+)", entry)
            draft_match = re.search(r"【下書き】\s*([\s\S]*?)(?=【ハッシュタグ】|【理由】|$)", entry)
            hashtag_match = re.search(r"【ハッシュタグ】\s*(.+)", entry)
            reason_match = re.search(r"【理由】\s*(.+)", entry)

            if date_match and platform_match:
                try:
                    date_str = date_match.group(1)
                    time_str = time_match.group(1) if time_match else "12:00"
                    scheduled_datetime = datetime.strptime(
                        f"{date_str} {time_str}", "%Y-%m-%d %H:%M"
                    ).replace(tzinfo=timezone.utc)

                    platform_str = platform_match.group(1).lower()
                    platform = ContentPlatform(platform_str)

                    type_str = type_match.group(1).lower() if type_match else "post"
                    content_type = ContentType(type_str) if type_str in [ct.value for ct in ContentType] else ContentType.POST

                    hashtags = []
                    if hashtag_match:
                        hashtags = re.findall(r"#([^\s#]+)", hashtag_match.group(1))

                    calendar_items.append(
                        ContentCalendarItem(
                            scheduled_date=scheduled_datetime,
                            platform=platform,
                            content_type=content_type,
                            topic=topic_match.group(1).strip() if topic_match else "",
                            draft_content=draft_match.group(1).strip() if draft_match else "",
                            hashtags=hashtags,
                            optimal_time=time_str,
                            rationale=reason_match.group(1).strip() if reason_match else "",
                        )
                    )
                except (ValueError, KeyError) as e:
                    logger.warning(f"カレンダーエントリのパースに失敗: {e}")
                    continue

        return calendar_items

    def generate_trending_content(
        self,
        platform: ContentPlatform,
        trend_keywords: list[str],
        brand_context: Optional[str] = None,
        tone: ContentTone = ContentTone.CASUAL,
    ) -> list[GeneratedContent]:
        """トレンドを活用したコンテンツを生成

        Args:
            platform: プラットフォーム
            trend_keywords: トレンドキーワード
            brand_context: ブランドコンテキスト
            tone: トーン

        Returns:
            list[GeneratedContent]: 生成されたコンテンツリスト
        """
        client = self._get_client()
        platform_config = PLATFORM_LIMITS.get(platform, {})
        guidelines = PLATFORM_GUIDELINES.get(platform, "")

        prompt = f"""以下のトレンドキーワードを活用した{platform.value}向けコンテンツを3つ作成してください。

## トレンドキーワード
{", ".join(trend_keywords)}

## プラットフォーム: {platform.value}
- 最大文字数: {platform_config.get("max_length", 280)}文字
- トーン: {tone.value}
{"- ブランドコンテキスト: " + brand_context if brand_context else ""}

## ガイドライン
{guidelines}

## 要件
- トレンドに自然に乗りつつオリジナリティを出す
- スパム的な印象を与えない
- 価値のある情報や視点を提供

## 出力形式（各コンテンツ）
【コンテンツ1】
トレンド活用: (使用したトレンドキーワード)
本文: (投稿内容)
ハッシュタグ: #tag1 #tag2
エンゲージメント予測: (高/中/低と理由)

（以下同様）
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "あなたはトレンドマーケティングの専門家です。トレンドを活用しつつ価値のあるコンテンツを作成します。",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=2000,
            temperature=0.8,
        )

        content = response.choices[0].message.content or ""

        # パース
        results = []
        for i in range(1, 4):
            pattern = rf"【コンテンツ{i}】\s*([\s\S]*?)(?=【コンテンツ|$)"
            match = re.search(pattern, content)
            if match:
                item_content = match.group(1)

                text = ""
                hashtags = []
                engagement = ""

                text_match = re.search(r"本文:\s*([\s\S]*?)(?=ハッシュタグ:|$)", item_content)
                if text_match:
                    text = text_match.group(1).strip()

                hashtag_match = re.search(r"ハッシュタグ:\s*(.+)", item_content)
                if hashtag_match:
                    hashtags = re.findall(r"#([^\s#]+)", hashtag_match.group(1))

                engagement_match = re.search(r"エンゲージメント予測:\s*(.+)", item_content)
                if engagement_match:
                    engagement = engagement_match.group(1).strip()

                if text:
                    results.append(
                        GeneratedContent(
                            id=f"trend_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{i}",
                            platform=platform,
                            content_type=ContentType.POST,
                            main_text=text,
                            hashtags=hashtags,
                            estimated_engagement=engagement,
                        )
                    )

        return results


# =============================================================================
# ユーティリティ関数
# =============================================================================


def get_platform_limits(platform: ContentPlatform) -> dict:
    """プラットフォームの制限を取得"""
    return PLATFORM_LIMITS.get(platform, {})


def get_platform_guidelines(platform: ContentPlatform) -> str:
    """プラットフォームのガイドラインを取得"""
    return PLATFORM_GUIDELINES.get(platform, "")


def validate_content_length(content: str, platform: ContentPlatform) -> bool:
    """コンテンツ長が制限内か検証"""
    limits = get_platform_limits(platform)
    max_length = limits.get("max_length", 280)
    return len(content) <= max_length
