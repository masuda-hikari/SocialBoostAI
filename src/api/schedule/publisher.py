"""
投稿パブリッシャー - 各プラットフォームへの投稿実行
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from ..db.models import ScheduledPost
from ..repositories.schedule_repository import ScheduleRepository

logger = logging.getLogger(__name__)


@dataclass
class PublishResult:
    """投稿結果"""

    success: bool
    external_post_id: Optional[str] = None
    error_message: Optional[str] = None


class BasePlatformPublisher(ABC):
    """プラットフォーム別パブリッシャー基底クラス"""

    @property
    @abstractmethod
    def platform(self) -> str:
        """プラットフォーム名"""
        pass

    @abstractmethod
    async def publish(
        self,
        content: str,
        hashtags: list[str],
        media_urls: list[str],
        media_type: Optional[str],
        metadata: dict,
    ) -> PublishResult:
        """投稿を実行"""
        pass


class TwitterPublisher(BasePlatformPublisher):
    """Twitter投稿パブリッシャー"""

    @property
    def platform(self) -> str:
        return "twitter"

    async def publish(
        self,
        content: str,
        hashtags: list[str],
        media_urls: list[str],
        media_type: Optional[str],
        metadata: dict,
    ) -> PublishResult:
        """Twitterに投稿"""
        try:
            # ハッシュタグを追加
            full_content = content
            if hashtags:
                hashtag_str = " ".join(f"#{tag}" for tag in hashtags)
                full_content = f"{content}\n\n{hashtag_str}"

            # TODO: 実際のTwitter API呼び出し
            # tweepy等を使用して投稿
            # 現在はモック実装
            logger.info(f"Twitter投稿: {full_content[:50]}...")

            # モック: 成功を返す（実際はAPIレスポンスのIDを返す）
            mock_tweet_id = f"tweet_{datetime.now().timestamp()}"
            return PublishResult(success=True, external_post_id=mock_tweet_id)

        except Exception as e:
            logger.error(f"Twitter投稿エラー: {e}")
            return PublishResult(success=False, error_message=str(e))


class InstagramPublisher(BasePlatformPublisher):
    """Instagram投稿パブリッシャー"""

    @property
    def platform(self) -> str:
        return "instagram"

    async def publish(
        self,
        content: str,
        hashtags: list[str],
        media_urls: list[str],
        media_type: Optional[str],
        metadata: dict,
    ) -> PublishResult:
        """Instagramに投稿"""
        try:
            # Instagramはメディア必須
            if not media_urls:
                return PublishResult(
                    success=False, error_message="Instagramはメディアが必須です"
                )

            # ハッシュタグを追加
            full_content = content
            if hashtags:
                hashtag_str = " ".join(f"#{tag}" for tag in hashtags)
                full_content = f"{content}\n\n{hashtag_str}"

            # TODO: 実際のInstagram API呼び出し
            logger.info(f"Instagram投稿: {full_content[:50]}...")

            mock_post_id = f"ig_{datetime.now().timestamp()}"
            return PublishResult(success=True, external_post_id=mock_post_id)

        except Exception as e:
            logger.error(f"Instagram投稿エラー: {e}")
            return PublishResult(success=False, error_message=str(e))


class TikTokPublisher(BasePlatformPublisher):
    """TikTok投稿パブリッシャー"""

    @property
    def platform(self) -> str:
        return "tiktok"

    async def publish(
        self,
        content: str,
        hashtags: list[str],
        media_urls: list[str],
        media_type: Optional[str],
        metadata: dict,
    ) -> PublishResult:
        """TikTokに投稿"""
        try:
            # TikTokは動画必須
            if not media_urls or media_type != "video":
                return PublishResult(
                    success=False, error_message="TikTokは動画が必須です"
                )

            full_content = content
            if hashtags:
                hashtag_str = " ".join(f"#{tag}" for tag in hashtags)
                full_content = f"{content} {hashtag_str}"

            # TODO: 実際のTikTok API呼び出し
            logger.info(f"TikTok投稿: {full_content[:50]}...")

            mock_post_id = f"tiktok_{datetime.now().timestamp()}"
            return PublishResult(success=True, external_post_id=mock_post_id)

        except Exception as e:
            logger.error(f"TikTok投稿エラー: {e}")
            return PublishResult(success=False, error_message=str(e))


class YouTubePublisher(BasePlatformPublisher):
    """YouTube投稿パブリッシャー"""

    @property
    def platform(self) -> str:
        return "youtube"

    async def publish(
        self,
        content: str,
        hashtags: list[str],
        media_urls: list[str],
        media_type: Optional[str],
        metadata: dict,
    ) -> PublishResult:
        """YouTubeに投稿"""
        try:
            # YouTubeは動画必須
            if not media_urls or media_type != "video":
                return PublishResult(
                    success=False, error_message="YouTubeは動画が必須です"
                )

            # タイトルと説明文を取得
            title = metadata.get("title", content[:100])
            description = content
            if hashtags:
                hashtag_str = " ".join(f"#{tag}" for tag in hashtags)
                description = f"{content}\n\n{hashtag_str}"

            # TODO: 実際のYouTube API呼び出し
            logger.info(f"YouTube投稿: {title[:50]}...")

            mock_video_id = f"yt_{datetime.now().timestamp()}"
            return PublishResult(success=True, external_post_id=mock_video_id)

        except Exception as e:
            logger.error(f"YouTube投稿エラー: {e}")
            return PublishResult(success=False, error_message=str(e))


class LinkedInPublisher(BasePlatformPublisher):
    """LinkedIn投稿パブリッシャー"""

    @property
    def platform(self) -> str:
        return "linkedin"

    async def publish(
        self,
        content: str,
        hashtags: list[str],
        media_urls: list[str],
        media_type: Optional[str],
        metadata: dict,
    ) -> PublishResult:
        """LinkedInに投稿"""
        try:
            full_content = content
            if hashtags:
                hashtag_str = " ".join(f"#{tag}" for tag in hashtags)
                full_content = f"{content}\n\n{hashtag_str}"

            # TODO: 実際のLinkedIn API呼び出し
            logger.info(f"LinkedIn投稿: {full_content[:50]}...")

            mock_post_id = f"li_{datetime.now().timestamp()}"
            return PublishResult(success=True, external_post_id=mock_post_id)

        except Exception as e:
            logger.error(f"LinkedIn投稿エラー: {e}")
            return PublishResult(success=False, error_message=str(e))


class PostPublisher:
    """投稿パブリッシャー - スケジュール投稿の実行管理"""

    MAX_RETRIES = 3

    def __init__(self, db: Session):
        self.db = db
        self.repo = ScheduleRepository(db)
        self._publishers: dict[str, BasePlatformPublisher] = {
            "twitter": TwitterPublisher(),
            "instagram": InstagramPublisher(),
            "tiktok": TikTokPublisher(),
            "youtube": YouTubePublisher(),
            "linkedin": LinkedInPublisher(),
        }

    async def publish_post(self, post: ScheduledPost) -> PublishResult:
        """スケジュール投稿を実行"""
        publisher = self._publishers.get(post.platform)
        if not publisher:
            return PublishResult(
                success=False,
                error_message=f"未対応プラットフォーム: {post.platform}",
            )

        try:
            hashtags = json.loads(post.hashtags)
            media_urls = json.loads(post.media_urls)
            metadata = json.loads(post.post_metadata) if post.post_metadata else {}

            result = await publisher.publish(
                content=post.content,
                hashtags=hashtags,
                media_urls=media_urls,
                media_type=post.media_type,
                metadata=metadata,
            )

            # ステータス更新
            now = datetime.now(timezone.utc)
            if result.success:
                self.repo.update_status(
                    post_id=post.id,
                    status="published",
                    external_post_id=result.external_post_id,
                    published_at=now,
                )
                logger.info(f"投稿成功: {post.id} -> {result.external_post_id}")
            else:
                self.repo.increment_retry(post.id)
                post_after_retry = self.repo.get_by_id(post.id)

                if post_after_retry and post_after_retry.retry_count >= self.MAX_RETRIES:
                    self.repo.update_status(
                        post_id=post.id,
                        status="failed",
                        error_message=result.error_message,
                    )
                    logger.error(
                        f"投稿失敗（最大リトライ到達）: {post.id} - {result.error_message}"
                    )
                else:
                    self.repo.update_status(
                        post_id=post.id,
                        status="pending",
                        error_message=result.error_message,
                    )
                    logger.warning(
                        f"投稿リトライ予定: {post.id} - {result.error_message}"
                    )

            return result

        except Exception as e:
            logger.error(f"投稿実行エラー: {post.id} - {e}")
            self.repo.update_status(
                post_id=post.id,
                status="failed",
                error_message=str(e),
            )
            return PublishResult(success=False, error_message=str(e))

    async def process_pending_posts(self) -> tuple[int, int]:
        """保留中の投稿を処理"""
        posts = self.repo.get_pending_posts()
        success_count = 0
        fail_count = 0

        for post in posts:
            result = await self.publish_post(post)
            if result.success:
                success_count += 1
            else:
                fail_count += 1

        return success_count, fail_count
