"""
スケジュール投稿サービス
"""

import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from ..db.models import ScheduledPost
from ..repositories.schedule_repository import ScheduleRepository
from ..schemas import (
    ContentPlatformType,
    ScheduledPostCreate,
    ScheduledPostResponse,
    ScheduledPostStatus,
    ScheduledPostSummary,
    ScheduledPostUpdate,
    ScheduleStatsResponse,
)


class ScheduleService:
    """スケジュール投稿サービス"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = ScheduleRepository(db)

    def _model_to_response(self, post: ScheduledPost) -> ScheduledPostResponse:
        """モデルをレスポンスに変換"""
        return ScheduledPostResponse(
            id=post.id,
            user_id=post.user_id,
            platform=ContentPlatformType(post.platform),
            content=post.content,
            hashtags=json.loads(post.hashtags),
            media_urls=json.loads(post.media_urls),
            media_type=post.media_type,
            scheduled_at=post.scheduled_at,
            timezone=post.timezone,
            status=ScheduledPostStatus(post.status),
            published_at=post.published_at,
            error_message=post.error_message,
            retry_count=post.retry_count,
            external_post_id=post.external_post_id,
            metadata=json.loads(post.post_metadata) if post.post_metadata else None,
            created_at=post.created_at,
            updated_at=post.updated_at,
        )

    def _model_to_summary(self, post: ScheduledPost) -> ScheduledPostSummary:
        """モデルをサマリーに変換"""
        content_preview = post.content[:100] + "..." if len(post.content) > 100 else post.content
        return ScheduledPostSummary(
            id=post.id,
            platform=ContentPlatformType(post.platform),
            content_preview=content_preview,
            scheduled_at=post.scheduled_at,
            status=ScheduledPostStatus(post.status),
            created_at=post.created_at,
        )

    def create_scheduled_post(
        self, user_id: str, request: ScheduledPostCreate
    ) -> ScheduledPostResponse:
        """スケジュール投稿を作成"""
        # 過去の時刻は許可しない
        now = datetime.now(timezone.utc)
        if request.scheduled_at < now:
            raise ValueError("過去の時刻にはスケジュールできません")

        post = self.repo.create(
            user_id=user_id,
            platform=request.platform.value,
            content=request.content,
            scheduled_at=request.scheduled_at,
            hashtags=request.hashtags,
            media_urls=request.media_urls,
            media_type=request.media_type.value if request.media_type else None,
            timezone_str=request.timezone,
            post_metadata=request.metadata,
        )
        return self._model_to_response(post)

    def get_scheduled_post(
        self, post_id: str, user_id: str
    ) -> Optional[ScheduledPostResponse]:
        """スケジュール投稿を取得"""
        post = self.repo.get_by_id_and_user(post_id, user_id)
        if not post:
            return None
        return self._model_to_response(post)

    def list_scheduled_posts(
        self,
        user_id: str,
        status: str | None = None,
        platform: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[ScheduledPostSummary], int, int]:
        """スケジュール投稿一覧を取得"""
        posts, total = self.repo.list_by_user(
            user_id=user_id,
            status=status,
            platform=platform,
            page=page,
            per_page=per_page,
        )
        summaries = [self._model_to_summary(p) for p in posts]
        pages = (total + per_page - 1) // per_page if per_page > 0 else 0
        return summaries, total, pages

    def update_scheduled_post(
        self, post_id: str, user_id: str, request: ScheduledPostUpdate
    ) -> Optional[ScheduledPostResponse]:
        """スケジュール投稿を更新"""
        # 権限チェック
        post = self.repo.get_by_id_and_user(post_id, user_id)
        if not post:
            return None

        # 既に公開済み・キャンセル済みは更新不可
        if post.status in ("published", "cancelled"):
            raise ValueError("公開済みまたはキャンセル済みの投稿は更新できません")

        # 過去の時刻は許可しない
        if request.scheduled_at:
            now = datetime.now(timezone.utc)
            if request.scheduled_at < now:
                raise ValueError("過去の時刻にはスケジュールできません")

        updated = self.repo.update(
            post_id=post_id,
            content=request.content,
            hashtags=request.hashtags,
            media_urls=request.media_urls,
            media_type=request.media_type.value if request.media_type else None,
            scheduled_at=request.scheduled_at,
            timezone_str=request.timezone,
            post_metadata=request.metadata,
        )
        if not updated:
            return None
        return self._model_to_response(updated)

    def cancel_scheduled_post(
        self, post_id: str, user_id: str
    ) -> Optional[ScheduledPostResponse]:
        """スケジュール投稿をキャンセル"""
        # 権限チェック
        post = self.repo.get_by_id_and_user(post_id, user_id)
        if not post:
            return None

        # 既に公開済み・キャンセル済みは変更不可
        if post.status in ("published", "cancelled"):
            raise ValueError("公開済みまたはキャンセル済みの投稿は変更できません")

        cancelled = self.repo.cancel(post_id)
        if not cancelled:
            return None
        return self._model_to_response(cancelled)

    def delete_scheduled_post(self, post_id: str, user_id: str) -> bool:
        """スケジュール投稿を削除"""
        # 権限チェック
        post = self.repo.get_by_id_and_user(post_id, user_id)
        if not post:
            return False

        return self.repo.delete(post_id)

    def get_upcoming_posts(
        self, user_id: str, hours: int = 24
    ) -> list[ScheduledPostSummary]:
        """今後N時間以内の投稿を取得"""
        posts = self.repo.get_upcoming_posts(user_id, hours)
        return [self._model_to_summary(p) for p in posts]

    def get_stats(self, user_id: str) -> ScheduleStatsResponse:
        """スケジュール統計を取得"""
        stats = self.repo.get_stats(user_id)
        return ScheduleStatsResponse(**stats)

    def bulk_create(
        self, user_id: str, posts: list[ScheduledPostCreate]
    ) -> tuple[list[ScheduledPostResponse], list[str]]:
        """一括でスケジュール投稿を作成"""
        created = []
        errors = []

        for i, request in enumerate(posts):
            try:
                post = self.create_scheduled_post(user_id, request)
                created.append(post)
            except Exception as e:
                errors.append(f"投稿 {i + 1}: {str(e)}")

        return created, errors
