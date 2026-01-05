"""
AI提案機能モジュール
"""

import logging
import os
from typing import Optional

from dotenv import load_dotenv

from .models import AnalysisResult, PostRecommendation, Tweet

load_dotenv()

logger = logging.getLogger(__name__)


class AIContentSuggester:
    """AIによるコンテンツ提案"""

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

    def suggest_content_ideas(
        self,
        top_posts: list[Tweet],
        topic: Optional[str] = None,
        count: int = 3,
    ) -> list[str]:
        """投稿アイデアを提案

        Args:
            top_posts: 過去のパフォーマンスの高い投稿
            topic: トピック（指定なしの場合は過去投稿から推測）
            count: 提案数

        Returns:
            list[str]: 投稿アイデアリスト
        """
        client = self._get_client()

        # 過去の投稿内容をコンテキストとして使用
        past_content = "\n".join([f"- {t.text[:100]}..." for t in top_posts[:5]])

        prompt = f"""以下は過去にエンゲージメントが高かったツイートです：

{past_content}

{"トピック: " + topic if topic else ""}

上記を参考に、同様のスタイルとトーンで新しいツイートのアイデアを{count}個提案してください。
各アイデアは280文字以内で、エンゲージメントを高める要素（質問、感情、具体的な数字など）を含めてください。

形式:
1. [アイデア1]
2. [アイデア2]
3. [アイデア3]
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "あなたはソーシャルメディアマーケティングの専門家です。エンゲージメントの高い投稿を提案します。",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=0.8,
        )

        content = response.choices[0].message.content or ""

        # 番号付きリストをパース
        ideas = []
        for line in content.split("\n"):
            line = line.strip()
            if line and line[0].isdigit() and "." in line:
                idea = line.split(".", 1)[1].strip()
                ideas.append(idea)

        logger.info(f"{len(ideas)}個のコンテンツアイデアを生成しました")
        return ideas[:count]

    def suggest_hashtags(
        self,
        content: str,
        count: int = 5,
    ) -> list[str]:
        """ハッシュタグを提案

        Args:
            content: 投稿内容
            count: 提案数

        Returns:
            list[str]: ハッシュタグリスト
        """
        client = self._get_client()

        prompt = f"""以下の投稿に最適なハッシュタグを{count}個提案してください。

投稿内容:
{content}

ハッシュタグは以下の基準で選んでください:
- 関連性が高い
- 検索されやすい
- 過度に競争が激しくない
- 日本語のタグも含める

形式（#は含めない）:
1. タグ1
2. タグ2
..."""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "あなたはソーシャルメディアの専門家です。効果的なハッシュタグを提案します。",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
            temperature=0.5,
        )

        content_response = response.choices[0].message.content or ""

        # タグをパース
        tags = []
        for line in content_response.split("\n"):
            line = line.strip()
            if line and line[0].isdigit() and "." in line:
                tag = line.split(".", 1)[1].strip()
                # #を除去
                tag = tag.lstrip("#").strip()
                if tag:
                    tags.append(tag)

        logger.info(f"{len(tags)}個のハッシュタグを提案しました")
        return tags[:count]

    def enhance_recommendations(
        self,
        analysis_result: AnalysisResult,
    ) -> PostRecommendation:
        """分析結果にAI提案を追加

        Args:
            analysis_result: 分析結果

        Returns:
            PostRecommendation: 強化されたレコメンデーション
        """
        existing = analysis_result.recommendations
        if existing is None:
            existing = PostRecommendation(
                best_hours=[],
                suggested_hashtags=[],
                content_ideas=[],
                reasoning="",
            )

        # コンテンツアイデアを生成
        content_ideas = []
        if analysis_result.top_performing_posts:
            try:
                content_ideas = self.suggest_content_ideas(
                    analysis_result.top_performing_posts
                )
            except Exception as e:
                logger.warning(f"コンテンツアイデア生成に失敗: {e}")

        # ハッシュタグを提案
        suggested_hashtags = []
        if analysis_result.top_performing_posts:
            try:
                # 最もパフォーマンスの高い投稿を元にハッシュタグを提案
                top_post = analysis_result.top_performing_posts[0]
                suggested_hashtags = self.suggest_hashtags(top_post.text)
            except Exception as e:
                logger.warning(f"ハッシュタグ提案に失敗: {e}")

        return PostRecommendation(
            best_hours=existing.best_hours,
            suggested_hashtags=suggested_hashtags,
            content_ideas=content_ideas,
            reasoning=existing.reasoning,
        )
