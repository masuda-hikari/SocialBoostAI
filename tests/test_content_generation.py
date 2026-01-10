"""
AIコンテンツ生成モジュールのテスト - v1.6
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.ai_content_generator import (
    AIContentGenerator,
    ContentPlatform,
    ContentType,
    ContentTone,
    ContentGoal,
    ContentGenerationRequest,
    ContentRewriteRequest,
    ABTestRequest,
    ContentCalendarRequest,
    GeneratedContent,
    ContentVariation,
    ContentCalendarItem,
    get_platform_limits,
    get_platform_guidelines,
    validate_content_length,
    PLATFORM_LIMITS,
    PLATFORM_GUIDELINES,
)


class TestContentPlatform:
    """ContentPlatformのテスト"""

    def test_platform_values(self):
        """プラットフォーム値が正しいことを確認"""
        assert ContentPlatform.TWITTER.value == "twitter"
        assert ContentPlatform.INSTAGRAM.value == "instagram"
        assert ContentPlatform.TIKTOK.value == "tiktok"
        assert ContentPlatform.YOUTUBE.value == "youtube"
        assert ContentPlatform.LINKEDIN.value == "linkedin"


class TestContentType:
    """ContentTypeのテスト"""

    def test_content_type_values(self):
        """コンテンツタイプ値が正しいことを確認"""
        assert ContentType.POST.value == "post"
        assert ContentType.THREAD.value == "thread"
        assert ContentType.STORY.value == "story"
        assert ContentType.REEL.value == "reel"
        assert ContentType.VIDEO.value == "video"
        assert ContentType.ARTICLE.value == "article"


class TestContentTone:
    """ContentToneのテスト"""

    def test_tone_values(self):
        """トーン値が正しいことを確認"""
        assert ContentTone.PROFESSIONAL.value == "professional"
        assert ContentTone.CASUAL.value == "casual"
        assert ContentTone.HUMOROUS.value == "humorous"


class TestContentGoal:
    """ContentGoalのテスト"""

    def test_goal_values(self):
        """目標値が正しいことを確認"""
        assert ContentGoal.ENGAGEMENT.value == "engagement"
        assert ContentGoal.AWARENESS.value == "awareness"
        assert ContentGoal.CONVERSION.value == "conversion"


class TestPlatformLimits:
    """プラットフォーム制限のテスト"""

    def test_twitter_limits(self):
        """Twitter制限が正しいことを確認"""
        limits = PLATFORM_LIMITS[ContentPlatform.TWITTER]
        assert limits["max_length"] == 280
        assert limits["optimal_hashtags"] == 3
        assert "7:00" in limits["best_times"]

    def test_instagram_limits(self):
        """Instagram制限が正しいことを確認"""
        limits = PLATFORM_LIMITS[ContentPlatform.INSTAGRAM]
        assert limits["max_length"] == 2200
        assert limits["optimal_hashtags"] == 10

    def test_linkedin_limits(self):
        """LinkedIn制限が正しいことを確認"""
        limits = PLATFORM_LIMITS[ContentPlatform.LINKEDIN]
        assert limits["max_length"] == 3000
        assert "best_days" in limits


class TestPlatformGuidelines:
    """プラットフォームガイドラインのテスト"""

    def test_twitter_guidelines(self):
        """Twitterガイドラインが存在することを確認"""
        guidelines = PLATFORM_GUIDELINES[ContentPlatform.TWITTER]
        assert "280文字" in guidelines
        assert "簡潔" in guidelines

    def test_linkedin_guidelines(self):
        """LinkedInガイドラインが存在することを確認"""
        guidelines = PLATFORM_GUIDELINES[ContentPlatform.LINKEDIN]
        assert "プロフェッショナル" in guidelines
        assert "ビジネス" in guidelines


class TestGetPlatformLimits:
    """get_platform_limits関数のテスト"""

    def test_get_twitter_limits(self):
        """Twitterの制限を取得できることを確認"""
        limits = get_platform_limits(ContentPlatform.TWITTER)
        assert limits["max_length"] == 280

    def test_get_unknown_platform_returns_empty(self):
        """不明なプラットフォームは空の辞書を返すことを確認"""
        # 無効な値でも動作することを確認（型チェック無効時）
        limits = get_platform_limits("unknown")  # type: ignore
        assert limits == {}


class TestGetPlatformGuidelines:
    """get_platform_guidelines関数のテスト"""

    def test_get_instagram_guidelines(self):
        """Instagramのガイドラインを取得できることを確認"""
        guidelines = get_platform_guidelines(ContentPlatform.INSTAGRAM)
        assert "ハッシュタグ" in guidelines


class TestValidateContentLength:
    """validate_content_length関数のテスト"""

    def test_valid_twitter_content(self):
        """有効なTwitterコンテンツ長を検証"""
        content = "これはテスト投稿です"
        assert validate_content_length(content, ContentPlatform.TWITTER) is True

    def test_invalid_twitter_content(self):
        """無効なTwitterコンテンツ長を検証"""
        content = "あ" * 281
        assert validate_content_length(content, ContentPlatform.TWITTER) is False

    def test_valid_instagram_content(self):
        """有効なInstagramコンテンツ長を検証"""
        content = "あ" * 2000
        assert validate_content_length(content, ContentPlatform.INSTAGRAM) is True


class TestGeneratedContent:
    """GeneratedContentモデルのテスト"""

    def test_create_generated_content(self):
        """GeneratedContentを作成できることを確認"""
        content = GeneratedContent(
            id="test_123",
            platform=ContentPlatform.TWITTER,
            content_type=ContentType.POST,
            main_text="テスト投稿です",
            hashtags=["テスト", "AI"],
        )
        assert content.id == "test_123"
        assert content.platform == ContentPlatform.TWITTER
        assert content.main_text == "テスト投稿です"
        assert len(content.hashtags) == 2

    def test_generated_content_default_values(self):
        """デフォルト値が正しく設定されることを確認"""
        content = GeneratedContent(
            id="test",
            platform=ContentPlatform.TWITTER,
            content_type=ContentType.POST,
            main_text="テスト",
        )
        assert content.hashtags == []
        assert content.call_to_action is None
        assert content.media_suggestion is None


class TestContentVariation:
    """ContentVariationモデルのテスト"""

    def test_create_content_variation(self):
        """ContentVariationを作成できることを確認"""
        variation = ContentVariation(
            version="A",
            text="バリエーションAのテキスト",
            hashtags=["テスト"],
            focus="質問形式",
        )
        assert variation.version == "A"
        assert variation.focus == "質問形式"


class TestContentCalendarItem:
    """ContentCalendarItemモデルのテスト"""

    def test_create_calendar_item(self):
        """ContentCalendarItemを作成できることを確認"""
        item = ContentCalendarItem(
            scheduled_date=datetime.now(timezone.utc),
            platform=ContentPlatform.TWITTER,
            content_type=ContentType.POST,
            topic="週末セール",
            draft_content="お得な週末セールを開催中！",
            hashtags=["セール", "週末"],
            optimal_time="12:00",
            rationale="昼休み時間帯が効果的",
        )
        assert item.platform == ContentPlatform.TWITTER
        assert item.topic == "週末セール"


class TestContentGenerationRequest:
    """ContentGenerationRequestモデルのテスト"""

    def test_create_request(self):
        """リクエストを作成できることを確認"""
        request = ContentGenerationRequest(
            platform=ContentPlatform.TWITTER,
            topic="新商品発表",
            tone=ContentTone.PROFESSIONAL,
            goal=ContentGoal.AWARENESS,
        )
        assert request.platform == ContentPlatform.TWITTER
        assert request.topic == "新商品発表"
        assert request.tone == ContentTone.PROFESSIONAL

    def test_request_default_values(self):
        """デフォルト値が正しく設定されることを確認"""
        request = ContentGenerationRequest(
            platform=ContentPlatform.INSTAGRAM,
        )
        assert request.content_type == ContentType.POST
        assert request.tone == ContentTone.CASUAL
        assert request.goal == ContentGoal.ENGAGEMENT
        assert request.include_hashtags is True
        assert request.include_cta is False


class TestContentRewriteRequest:
    """ContentRewriteRequestモデルのテスト"""

    def test_create_rewrite_request(self):
        """リライトリクエストを作成できることを確認"""
        request = ContentRewriteRequest(
            original_content="元のコンテンツです",
            source_platform=ContentPlatform.TWITTER,
            target_platform=ContentPlatform.INSTAGRAM,
        )
        assert request.original_content == "元のコンテンツです"
        assert request.source_platform == ContentPlatform.TWITTER
        assert request.target_platform == ContentPlatform.INSTAGRAM


class TestABTestRequest:
    """ABTestRequestモデルのテスト"""

    def test_create_ab_request(self):
        """A/Bテストリクエストを作成できることを確認"""
        request = ABTestRequest(
            base_topic="新機能リリース",
            platform=ContentPlatform.TWITTER,
            variation_count=3,
        )
        assert request.base_topic == "新機能リリース"
        assert request.variation_count == 3


class TestContentCalendarRequest:
    """ContentCalendarRequestモデルのテスト"""

    def test_create_calendar_request(self):
        """カレンダーリクエストを作成できることを確認"""
        request = ContentCalendarRequest(
            platforms=[ContentPlatform.TWITTER, ContentPlatform.INSTAGRAM],
            days=7,
            posts_per_day=2,
        )
        assert len(request.platforms) == 2
        assert request.days == 7


class TestAIContentGenerator:
    """AIContentGeneratorのテスト"""

    def test_init(self):
        """初期化が成功することを確認"""
        generator = AIContentGenerator()
        assert generator._client is None

    @patch("src.ai_content_generator.os.getenv")
    def test_get_client_without_api_key(self, mock_getenv):
        """APIキーなしでクライアント取得がエラーになることを確認"""
        mock_getenv.return_value = None
        generator = AIContentGenerator()

        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            generator._get_client()

    def test_parse_generated_content_with_main_text(self):
        """本文パースが正しく動作することを確認"""
        generator = AIContentGenerator()
        content = """【本文】
これはテスト投稿です。

【ハッシュタグ】
#テスト #AI #投稿

【CTA】
詳しくはこちらをご覧ください

【メディア提案】
製品画像を使用

【期待効果】
高いエンゲージメントが期待できます
"""
        result = generator._parse_generated_content(content)
        assert "テスト投稿" in result["main_text"]
        assert "テスト" in result["hashtags"]
        assert "AI" in result["hashtags"]
        assert "詳しく" in result["cta"]

    def test_parse_generated_content_no_sections(self):
        """セクションなしのコンテンツパースが正しく動作することを確認"""
        generator = AIContentGenerator()
        content = "これは単純なテキストです"
        result = generator._parse_generated_content(content)
        assert result["main_text"] == "これは単純なテキストです"

    @patch.object(AIContentGenerator, "_get_client")
    def test_generate_content_success(self, mock_get_client):
        """コンテンツ生成が成功することを確認"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="""【本文】
テスト投稿です！

【ハッシュタグ】
#テスト #AI

【CTA】
いいねしてね

【メディア提案】
画像

【期待効果】
高
"""
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        generator = AIContentGenerator()
        request = ContentGenerationRequest(
            platform=ContentPlatform.TWITTER,
            topic="テスト",
        )
        result = generator.generate_content(request)

        assert result.platform == ContentPlatform.TWITTER
        assert "テスト投稿" in result.main_text
        mock_client.chat.completions.create.assert_called_once()

    @patch.object(AIContentGenerator, "_get_client")
    def test_rewrite_for_platform_success(self, mock_get_client):
        """リライトが成功することを確認"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="""【リライト後の本文】
Instagram向けにリライトされた投稿です！

【ハッシュタグ】
#Instagram #リライト
"""
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        generator = AIContentGenerator()
        request = ContentRewriteRequest(
            original_content="元の投稿",
            source_platform=ContentPlatform.TWITTER,
            target_platform=ContentPlatform.INSTAGRAM,
        )
        result = generator.rewrite_for_platform(request)

        assert result.platform == ContentPlatform.INSTAGRAM
        assert "Instagram向け" in result.main_text

    @patch.object(AIContentGenerator, "_get_client")
    def test_generate_ab_variations_success(self, mock_get_client):
        """A/Bテストバリエーション生成が成功することを確認"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="""【バリエーションA】
フォーカス: 質問形式
本文: これはバリエーションAです。どう思いますか？
ハッシュタグ: #テスト #A

【バリエーションB】
フォーカス: データ重視
本文: 99%の人が知らない事実をご紹介します。
ハッシュタグ: #テスト #B

【バリエーションC】
フォーカス: 感情重視
本文: 感動のストーリーをお届けします。
ハッシュタグ: #テスト #C
"""
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        generator = AIContentGenerator()
        request = ABTestRequest(
            base_topic="テストトピック",
            platform=ContentPlatform.TWITTER,
            variation_count=3,
        )
        result = generator.generate_ab_variations(request)

        assert len(result) == 3
        assert result[0].version == "A"
        assert result[1].version == "B"
        assert result[2].version == "C"

    @patch.object(AIContentGenerator, "_get_client")
    def test_generate_content_calendar_success(self, mock_get_client):
        """カレンダー生成が成功することを確認"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="""【日付】2026-01-15
【時間】12:00
【プラットフォーム】twitter
【タイプ】post
【トピック】新機能発表
【下書き】新機能をリリースしました！
【ハッシュタグ】#新機能 #リリース
【理由】昼休み時間帯で効果的
---
【日付】2026-01-16
【時間】18:00
【プラットフォーム】instagram
【タイプ】post
【トピック】製品紹介
【下書き】製品のご紹介です
【ハッシュタグ】#製品 #紹介
【理由】夕方時間帯で効果的
"""
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        generator = AIContentGenerator()
        request = ContentCalendarRequest(
            platforms=[ContentPlatform.TWITTER, ContentPlatform.INSTAGRAM],
            days=7,
            posts_per_day=1,
        )
        result = generator.generate_content_calendar(request)

        assert len(result) == 2
        assert result[0].platform == ContentPlatform.TWITTER
        assert result[1].platform == ContentPlatform.INSTAGRAM

    @patch.object(AIContentGenerator, "_get_client")
    def test_generate_trending_content_success(self, mock_get_client):
        """トレンドコンテンツ生成が成功することを確認"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="""【コンテンツ1】
トレンド活用: AI
本文: AIを活用した新しい働き方をご紹介！
ハッシュタグ: #AI #働き方改革
エンゲージメント予測: 高

【コンテンツ2】
トレンド活用: ChatGPT
本文: ChatGPTでできること10選
ハッシュタグ: #ChatGPT #効率化
エンゲージメント予測: 中

【コンテンツ3】
トレンド活用: AI, 働き方
本文: リモートワークをAIで効率化する方法
ハッシュタグ: #リモートワーク #AI
エンゲージメント予測: 高
"""
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        generator = AIContentGenerator()
        result = generator.generate_trending_content(
            platform=ContentPlatform.TWITTER,
            trend_keywords=["AI", "ChatGPT", "働き方改革"],
        )

        assert len(result) == 3
        assert all(c.platform == ContentPlatform.TWITTER for c in result)


class TestEdgeCases:
    """エッジケースのテスト"""

    def test_empty_hashtags_list(self):
        """空のハッシュタグリストの処理"""
        generator = AIContentGenerator()
        content = """【本文】
ハッシュタグなしの投稿です

【ハッシュタグ】

【CTA】
なし
"""
        result = generator._parse_generated_content(content)
        assert result["hashtags"] == []

    def test_parse_content_with_special_characters(self):
        """特殊文字を含むコンテンツのパース"""
        generator = AIContentGenerator()
        content = """【本文】
絵文字付き投稿！🎉✨

【ハッシュタグ】
#お祝い #パーティー
"""
        result = generator._parse_generated_content(content)
        assert "🎉" in result["main_text"]
        assert "お祝い" in result["hashtags"]

    def test_platform_limits_all_defined(self):
        """すべてのプラットフォームに制限が定義されていることを確認"""
        for platform in ContentPlatform:
            assert platform in PLATFORM_LIMITS

    def test_platform_guidelines_all_defined(self):
        """すべてのプラットフォームにガイドラインが定義されていることを確認"""
        for platform in ContentPlatform:
            assert platform in PLATFORM_GUIDELINES
