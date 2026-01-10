"""
スケジュール投稿リポジトリ
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from ..db.models import ScheduledPost


class ScheduleRepository:
    """スケジュール投稿リポジトリ"""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: str,
        platform: str,
        content: str,
        scheduled_at: datetime,
        hashtags: list[str] | None = None,
        media_urls: list[str] | None = None,
        media_type: str | None = None,
        timezone_str: str = "Asia/Tokyo",
        post_metadata: dict | None = None,
    ) -> ScheduledPost:
        """スケジュール投稿を作成"""
        post = ScheduledPost(
            user_id=user_id,
            platform=platform,
            content=content,
            scheduled_at=scheduled_at,
            hashtags=json.dumps(hashtags or []),
            media_urls=json.dumps(media_urls or []),
            media_type=media_type,
            timezone=timezone_str,
            post_metadata=json.dumps(post_metadata or {}),
        )
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post

    def get_by_id(self, post_id: str) -> Optional[ScheduledPost]:
        """IDでスケジュール投稿を取得"""
        return self.db.execute(
            select(ScheduledPost).where(ScheduledPost.id == post_id)
        ).scalar_one_or_none()

    def get_by_id_and_user(
        self, post_id: str, user_id: str
    ) -> Optional[ScheduledPost]:
        """IDとユーザーIDでスケジュール投稿を取得"""
        return self.db.execute(
            select(ScheduledPost).where(
                and_(ScheduledPost.id == post_id, ScheduledPost.user_id == user_id)
            )
        ).scalar_one_or_none()

    def list_by_user(
        self,
        user_id: str,
        status: str | None = None,
        platform: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[ScheduledPost], int]:
        """ユーザーのスケジュール投稿一覧を取得"""
        query = select(ScheduledPost).where(ScheduledPost.user_id == user_id)

        if status:
            query = query.where(ScheduledPost.status == status)
        if platform:
            query = query.where(ScheduledPost.platform == platform)

        # 総件数
        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_query).scalar() or 0

        # ページネーション
        query = (
            query.order_by(ScheduledPost.scheduled_at.asc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )

        posts = list(self.db.execute(query).scalars().all())
        return posts, total

    def get_pending_posts(
        self, before: datetime | None = None, limit: int = 100
    ) -> list[ScheduledPost]:
        """保留中の投稿を取得（実行対象）"""
        query = select(ScheduledPost).where(ScheduledPost.status == "pending")

        if before is None:
            before = datetime.now(timezone.utc)
        query = query.where(ScheduledPost.scheduled_at <= before)

        query = query.order_by(ScheduledPost.scheduled_at.asc()).limit(limit)

        return list(self.db.execute(query).scalars().all())

    def get_upcoming_posts(
        self, user_id: str, hours: int = 24
    ) -> list[ScheduledPost]:
        """今後N時間以内の投稿を取得"""
        now = datetime.now(timezone.utc)
        future = now + timedelta(hours=hours)

        query = select(ScheduledPost).where(
            and_(
                ScheduledPost.user_id == user_id,
                ScheduledPost.status == "pending",
                ScheduledPost.scheduled_at >= now,
                ScheduledPost.scheduled_at <= future,
            )
        ).order_by(ScheduledPost.scheduled_at.asc())

        return list(self.db.execute(query).scalars().all())

    def update(
        self,
        post_id: str,
        content: str | None = None,
        hashtags: list[str] | None = None,
        media_urls: list[str] | None = None,
        media_type: str | None = None,
        scheduled_at: datetime | None = None,
        timezone_str: str | None = None,
        post_metadata: dict | None = None,
    ) -> Optional[ScheduledPost]:
        """スケジュール投稿を更新"""
        post = self.get_by_id(post_id)
        if not post:
            return None

        if content is not None:
            post.content = content
        if hashtags is not None:
            post.hashtags = json.dumps(hashtags)
        if media_urls is not None:
            post.media_urls = json.dumps(media_urls)
        if media_type is not None:
            post.media_type = media_type
        if scheduled_at is not None:
            post.scheduled_at = scheduled_at
        if timezone_str is not None:
            post.timezone = timezone_str
        if post_metadata is not None:
            post.post_metadata = json.dumps(post_metadata)

        self.db.commit()
        self.db.refresh(post)
        return post

    def update_status(
        self,
        post_id: str,
        status: str,
        external_post_id: str | None = None,
        error_message: str | None = None,
        published_at: datetime | None = None,
    ) -> Optional[ScheduledPost]:
        """ステータスを更新"""
        post = self.get_by_id(post_id)
        if not post:
            return None

        post.status = status
        if external_post_id is not None:
            post.external_post_id = external_post_id
        if error_message is not None:
            post.error_message = error_message
        if published_at is not None:
            post.published_at = published_at

        self.db.commit()
        self.db.refresh(post)
        return post

    def increment_retry(self, post_id: str) -> Optional[ScheduledPost]:
        """リトライ回数を増加"""
        post = self.get_by_id(post_id)
        if not post:
            return None

        post.retry_count += 1
        self.db.commit()
        self.db.refresh(post)
        return post

    def cancel(self, post_id: str) -> Optional[ScheduledPost]:
        """スケジュール投稿をキャンセル"""
        return self.update_status(post_id, "cancelled")

    def delete(self, post_id: str) -> bool:
        """スケジュール投稿を削除"""
        post = self.get_by_id(post_id)
        if not post:
            return False

        self.db.delete(post)
        self.db.commit()
        return True

    def get_stats(self, user_id: str) -> dict:
        """スケジュール統計を取得"""
        # ステータス別カウント
        status_counts = dict(
            self.db.execute(
                select(ScheduledPost.status, func.count())
                .where(ScheduledPost.user_id == user_id)
                .group_by(ScheduledPost.status)
            ).all()
        )

        # プラットフォーム別カウント
        platform_counts = dict(
            self.db.execute(
                select(ScheduledPost.platform, func.count())
                .where(ScheduledPost.user_id == user_id)
                .group_by(ScheduledPost.platform)
            ).all()
        )

        # 今後24時間以内
        now = datetime.now(timezone.utc)
        future = now + timedelta(hours=24)
        upcoming = self.db.execute(
            select(func.count()).where(
                and_(
                    ScheduledPost.user_id == user_id,
                    ScheduledPost.status == "pending",
                    ScheduledPost.scheduled_at >= now,
                    ScheduledPost.scheduled_at <= future,
                )
            )
        ).scalar() or 0

        return {
            "total_scheduled": sum(status_counts.values()),
            "pending": status_counts.get("pending", 0),
            "published": status_counts.get("published", 0),
            "failed": status_counts.get("failed", 0),
            "cancelled": status_counts.get("cancelled", 0),
            "upcoming_24h": upcoming,
            "by_platform": platform_counts,
            "by_status": status_counts,
        }
