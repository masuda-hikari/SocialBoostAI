"""
スケジュール投稿サービスのテスト
"""

import json
from datetime import datetime, timedelta, timezone

import pytest

from src.api.db.models import ScheduledPost, User
from src.api.repositories.schedule_repository import ScheduleRepository
from src.api.schedule.service import ScheduleService
from src.api.schemas import (
    ContentPlatformType,
    ScheduledPostCreate,
    ScheduledPostMediaType,
    ScheduledPostUpdate,
)


class TestScheduleRepository:
    """ScheduleRepositoryのテスト"""

    def test_create_scheduled_post(self, db_session, test_user):
        """スケジュール投稿を作成できる"""
        repo = ScheduleRepository(db_session)
        future = datetime.now(timezone.utc) + timedelta(hours=1)

        post = repo.create(
            user_id=test_user.id,
            platform="twitter",
            content="テスト投稿",
            scheduled_at=future,
            hashtags=["テスト", "SocialBoostAI"],
            media_urls=[],
            media_type=None,
        )

        assert post.id.startswith("sched_")
        assert post.user_id == test_user.id
        assert post.platform == "twitter"
        assert post.content == "テスト投稿"
        assert post.status == "pending"
        assert json.loads(post.hashtags) == ["テスト", "SocialBoostAI"]

    def test_get_by_id(self, db_session, test_user):
        """IDで投稿を取得できる"""
        repo = ScheduleRepository(db_session)
        future = datetime.now(timezone.utc) + timedelta(hours=1)

        created = repo.create(
            user_id=test_user.id,
            platform="twitter",
            content="テスト",
            scheduled_at=future,
        )

        found = repo.get_by_id(created.id)
        assert found is not None
        assert found.id == created.id

    def test_get_by_id_not_found(self, db_session):
        """存在しないIDはNoneを返す"""
        repo = ScheduleRepository(db_session)
        found = repo.get_by_id("nonexistent")
        assert found is None

    def test_get_by_id_and_user(self, db_session, test_user):
        """ユーザーIDとIDで投稿を取得できる"""
        repo = ScheduleRepository(db_session)
        future = datetime.now(timezone.utc) + timedelta(hours=1)

        created = repo.create(
            user_id=test_user.id,
            platform="twitter",
            content="テスト",
            scheduled_at=future,
        )

        # 正しいユーザー
        found = repo.get_by_id_and_user(created.id, test_user.id)
        assert found is not None

        # 別のユーザー
        found = repo.get_by_id_and_user(created.id, "other_user")
        assert found is None

    def test_list_by_user(self, db_session, test_user):
        """ユーザーの投稿一覧を取得できる"""
        repo = ScheduleRepository(db_session)
        future = datetime.now(timezone.utc) + timedelta(hours=1)

        # 複数投稿作成
        for i in range(5):
            repo.create(
                user_id=test_user.id,
                platform="twitter",
                content=f"テスト{i}",
                scheduled_at=future + timedelta(hours=i),
            )

        posts, total = repo.list_by_user(test_user.id)
        assert total == 5
        assert len(posts) == 5

    def test_list_by_user_with_status_filter(self, db_session, test_user):
        """ステータスでフィルタできる"""
        repo = ScheduleRepository(db_session)
        future = datetime.now(timezone.utc) + timedelta(hours=1)

        # 保留中の投稿
        repo.create(
            user_id=test_user.id,
            platform="twitter",
            content="保留中",
            scheduled_at=future,
        )

        # キャンセル済み投稿
        post = repo.create(
            user_id=test_user.id,
            platform="twitter",
            content="キャンセル済み",
            scheduled_at=future,
        )
        repo.update_status(post.id, "cancelled")

        pending_posts, total = repo.list_by_user(test_user.id, status="pending")
        assert total == 1
        assert pending_posts[0].content == "保留中"

    def test_list_by_user_with_platform_filter(self, db_session, test_user):
        """プラットフォームでフィルタできる"""
        repo = ScheduleRepository(db_session)
        future = datetime.now(timezone.utc) + timedelta(hours=1)

        repo.create(
            user_id=test_user.id,
            platform="twitter",
            content="Twitter投稿",
            scheduled_at=future,
        )
        repo.create(
            user_id=test_user.id,
            platform="instagram",
            content="Instagram投稿",
            scheduled_at=future,
        )

        twitter_posts, total = repo.list_by_user(test_user.id, platform="twitter")
        assert total == 1
        assert twitter_posts[0].platform == "twitter"

    def test_get_pending_posts(self, db_session, test_user):
        """保留中の投稿を取得できる（実行対象）"""
        repo = ScheduleRepository(db_session)
        now = datetime.now(timezone.utc)
        past = now - timedelta(minutes=5)
        future = now + timedelta(hours=1)

        # 過去の時刻（実行対象）
        repo.create(
            user_id=test_user.id,
            platform="twitter",
            content="実行対象",
            scheduled_at=past,
        )
        # 将来の時刻（実行対象外）
        repo.create(
            user_id=test_user.id,
            platform="twitter",
            content="将来",
            scheduled_at=future,
        )

        pending = repo.get_pending_posts()
        assert len(pending) == 1
        assert pending[0].content == "実行対象"

    def test_get_upcoming_posts(self, db_session, test_user):
        """今後N時間以内の投稿を取得できる"""
        repo = ScheduleRepository(db_session)
        now = datetime.now(timezone.utc)

        # 1時間後（対象）
        repo.create(
            user_id=test_user.id,
            platform="twitter",
            content="1時間後",
            scheduled_at=now + timedelta(hours=1),
        )
        # 48時間後（対象外）
        repo.create(
            user_id=test_user.id,
            platform="twitter",
            content="48時間後",
            scheduled_at=now + timedelta(hours=48),
        )

        upcoming = repo.get_upcoming_posts(test_user.id, hours=24)
        assert len(upcoming) == 1
        assert upcoming[0].content == "1時間後"

    def test_update(self, db_session, test_user):
        """投稿を更新できる"""
        repo = ScheduleRepository(db_session)
        future = datetime.now(timezone.utc) + timedelta(hours=1)

        post = repo.create(
            user_id=test_user.id,
            platform="twitter",
            content="元のコンテンツ",
            scheduled_at=future,
        )

        updated = repo.update(
            post_id=post.id,
            content="更新後のコンテンツ",
            hashtags=["更新"],
        )

        assert updated.content == "更新後のコンテンツ"
        assert json.loads(updated.hashtags) == ["更新"]

    def test_update_status(self, db_session, test_user):
        """ステータスを更新できる"""
        repo = ScheduleRepository(db_session)
        future = datetime.now(timezone.utc) + timedelta(hours=1)

        post = repo.create(
            user_id=test_user.id,
            platform="twitter",
            content="テスト",
            scheduled_at=future,
        )

        updated = repo.update_status(
            post_id=post.id,
            status="published",
            external_post_id="tweet_123",
            published_at=datetime.now(timezone.utc),
        )

        assert updated.status == "published"
        assert updated.external_post_id == "tweet_123"
        assert updated.published_at is not None

    def test_increment_retry(self, db_session, test_user):
        """リトライ回数を増加できる"""
        repo = ScheduleRepository(db_session)
        future = datetime.now(timezone.utc) + timedelta(hours=1)

        post = repo.create(
            user_id=test_user.id,
            platform="twitter",
            content="テスト",
            scheduled_at=future,
        )

        assert post.retry_count == 0

        repo.increment_retry(post.id)
        post = repo.get_by_id(post.id)
        assert post.retry_count == 1

    def test_cancel(self, db_session, test_user):
        """投稿をキャンセルできる"""
        repo = ScheduleRepository(db_session)
        future = datetime.now(timezone.utc) + timedelta(hours=1)

        post = repo.create(
            user_id=test_user.id,
            platform="twitter",
            content="テスト",
            scheduled_at=future,
        )

        cancelled = repo.cancel(post.id)
        assert cancelled.status == "cancelled"

    def test_delete(self, db_session, test_user):
        """投稿を削除できる"""
        repo = ScheduleRepository(db_session)
        future = datetime.now(timezone.utc) + timedelta(hours=1)

        post = repo.create(
            user_id=test_user.id,
            platform="twitter",
            content="テスト",
            scheduled_at=future,
        )

        result = repo.delete(post.id)
        assert result is True

        found = repo.get_by_id(post.id)
        assert found is None

    def test_get_stats(self, db_session, test_user):
        """統計を取得できる"""
        repo = ScheduleRepository(db_session)
        now = datetime.now(timezone.utc)
        future = now + timedelta(hours=1)

        # 保留中
        repo.create(
            user_id=test_user.id,
            platform="twitter",
            content="保留中1",
            scheduled_at=future,
        )
        repo.create(
            user_id=test_user.id,
            platform="instagram",
            content="保留中2",
            scheduled_at=future,
        )

        # 公開済み
        post = repo.create(
            user_id=test_user.id,
            platform="twitter",
            content="公開済み",
            scheduled_at=now - timedelta(hours=1),
        )
        repo.update_status(post.id, "published")

        stats = repo.get_stats(test_user.id)

        assert stats["total_scheduled"] == 3
        assert stats["pending"] == 2
        assert stats["published"] == 1
        assert stats["by_platform"]["twitter"] == 2
        assert stats["by_platform"]["instagram"] == 1


class TestScheduleService:
    """ScheduleServiceのテスト"""

    def test_create_scheduled_post(self, db_session, test_user):
        """スケジュール投稿を作成できる"""
        service = ScheduleService(db_session)
        future = datetime.now(timezone.utc) + timedelta(hours=1)

        request = ScheduledPostCreate(
            platform=ContentPlatformType.TWITTER,
            content="テスト投稿です",
            hashtags=["テスト"],
            scheduled_at=future,
        )

        response = service.create_scheduled_post(test_user.id, request)

        assert response.platform == ContentPlatformType.TWITTER
        assert response.content == "テスト投稿です"
        assert response.hashtags == ["テスト"]
        assert response.status.value == "pending"

    def test_create_scheduled_post_past_time_error(self, db_session, test_user):
        """過去の時刻にはスケジュールできない"""
        service = ScheduleService(db_session)
        past = datetime.now(timezone.utc) - timedelta(hours=1)

        request = ScheduledPostCreate(
            platform=ContentPlatformType.TWITTER,
            content="テスト",
            scheduled_at=past,
        )

        with pytest.raises(ValueError, match="過去の時刻"):
            service.create_scheduled_post(test_user.id, request)

    def test_get_scheduled_post(self, db_session, test_user):
        """スケジュール投稿を取得できる"""
        service = ScheduleService(db_session)
        future = datetime.now(timezone.utc) + timedelta(hours=1)

        request = ScheduledPostCreate(
            platform=ContentPlatformType.TWITTER,
            content="テスト",
            scheduled_at=future,
        )

        created = service.create_scheduled_post(test_user.id, request)
        found = service.get_scheduled_post(created.id, test_user.id)

        assert found is not None
        assert found.id == created.id

    def test_get_scheduled_post_not_found(self, db_session, test_user):
        """存在しない投稿はNoneを返す"""
        service = ScheduleService(db_session)
        found = service.get_scheduled_post("nonexistent", test_user.id)
        assert found is None

    def test_list_scheduled_posts(self, db_session, test_user):
        """スケジュール投稿一覧を取得できる"""
        service = ScheduleService(db_session)
        future = datetime.now(timezone.utc) + timedelta(hours=1)

        for i in range(3):
            request = ScheduledPostCreate(
                platform=ContentPlatformType.TWITTER,
                content=f"テスト{i}",
                scheduled_at=future + timedelta(hours=i),
            )
            service.create_scheduled_post(test_user.id, request)

        items, total, pages = service.list_scheduled_posts(test_user.id)

        assert total == 3
        assert len(items) == 3

    def test_update_scheduled_post(self, db_session, test_user):
        """スケジュール投稿を更新できる"""
        service = ScheduleService(db_session)
        future = datetime.now(timezone.utc) + timedelta(hours=1)

        request = ScheduledPostCreate(
            platform=ContentPlatformType.TWITTER,
            content="元のコンテンツ",
            scheduled_at=future,
        )

        created = service.create_scheduled_post(test_user.id, request)

        update_request = ScheduledPostUpdate(
            content="更新後のコンテンツ",
        )

        updated = service.update_scheduled_post(created.id, test_user.id, update_request)

        assert updated.content == "更新後のコンテンツ"

    def test_update_scheduled_post_cannot_update_published(self, db_session, test_user):
        """公開済み投稿は更新できない"""
        service = ScheduleService(db_session)
        repo = ScheduleRepository(db_session)
        future = datetime.now(timezone.utc) + timedelta(hours=1)

        request = ScheduledPostCreate(
            platform=ContentPlatformType.TWITTER,
            content="テスト",
            scheduled_at=future,
        )

        created = service.create_scheduled_post(test_user.id, request)
        repo.update_status(created.id, "published")

        update_request = ScheduledPostUpdate(content="更新")

        with pytest.raises(ValueError, match="公開済み"):
            service.update_scheduled_post(created.id, test_user.id, update_request)

    def test_cancel_scheduled_post(self, db_session, test_user):
        """スケジュール投稿をキャンセルできる"""
        service = ScheduleService(db_session)
        future = datetime.now(timezone.utc) + timedelta(hours=1)

        request = ScheduledPostCreate(
            platform=ContentPlatformType.TWITTER,
            content="テスト",
            scheduled_at=future,
        )

        created = service.create_scheduled_post(test_user.id, request)
        cancelled = service.cancel_scheduled_post(created.id, test_user.id)

        assert cancelled.status.value == "cancelled"

    def test_delete_scheduled_post(self, db_session, test_user):
        """スケジュール投稿を削除できる"""
        service = ScheduleService(db_session)
        future = datetime.now(timezone.utc) + timedelta(hours=1)

        request = ScheduledPostCreate(
            platform=ContentPlatformType.TWITTER,
            content="テスト",
            scheduled_at=future,
        )

        created = service.create_scheduled_post(test_user.id, request)
        result = service.delete_scheduled_post(created.id, test_user.id)

        assert result is True

        found = service.get_scheduled_post(created.id, test_user.id)
        assert found is None

    def test_get_upcoming_posts(self, db_session, test_user):
        """今後の投稿を取得できる"""
        service = ScheduleService(db_session)
        now = datetime.now(timezone.utc)

        # 1時間後
        request = ScheduledPostCreate(
            platform=ContentPlatformType.TWITTER,
            content="1時間後",
            scheduled_at=now + timedelta(hours=1),
        )
        service.create_scheduled_post(test_user.id, request)

        upcoming = service.get_upcoming_posts(test_user.id, hours=24)
        assert len(upcoming) == 1

    def test_get_stats(self, db_session, test_user):
        """統計を取得できる"""
        service = ScheduleService(db_session)
        future = datetime.now(timezone.utc) + timedelta(hours=1)

        request = ScheduledPostCreate(
            platform=ContentPlatformType.TWITTER,
            content="テスト",
            scheduled_at=future,
        )
        service.create_scheduled_post(test_user.id, request)

        stats = service.get_stats(test_user.id)

        assert stats.total_scheduled == 1
        assert stats.pending == 1

    def test_bulk_create(self, db_session, test_user):
        """一括作成できる"""
        service = ScheduleService(db_session)
        future = datetime.now(timezone.utc) + timedelta(hours=1)

        requests = [
            ScheduledPostCreate(
                platform=ContentPlatformType.TWITTER,
                content=f"投稿{i}",
                scheduled_at=future + timedelta(hours=i),
            )
            for i in range(3)
        ]

        created, errors = service.bulk_create(test_user.id, requests)

        assert len(created) == 3
        assert len(errors) == 0
