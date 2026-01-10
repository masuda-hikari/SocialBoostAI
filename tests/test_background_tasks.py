"""
バックグラウンドタスクサービステスト
"""

import asyncio
import time

import pytest

from src.api.tasks.service import (
    BackgroundTaskService,
    TaskStatus,
    get_task_service,
)


class TestBackgroundTaskService:
    """BackgroundTaskServiceテスト"""

    def test_init(self):
        """初期化テスト"""
        service = BackgroundTaskService()
        assert service is not None

    def test_submit_task(self):
        """タスク登録テスト"""

        def simple_task():
            return "done"

        service = BackgroundTaskService()
        task_id = service.submit(simple_task, task_name="テストタスク")

        assert task_id.startswith("task_")
        assert len(task_id) == 21  # "task_" + 16文字

    def test_get_status(self):
        """ステータス取得テスト"""

        def quick_task():
            return "completed"

        service = BackgroundTaskService()
        task_id = service.submit(quick_task)

        # 少し待機
        time.sleep(0.5)

        result = service.get_status(task_id)
        assert result is not None
        assert result.task_id == task_id
        assert result.status in (TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.COMPLETED)

    def test_task_completion(self):
        """タスク完了テスト"""

        def slow_task():
            time.sleep(0.2)
            return "result_value"

        service = BackgroundTaskService()
        task_id = service.submit(slow_task)

        # タスク完了を待機
        time.sleep(1)

        result = service.get_status(task_id)
        assert result is not None
        assert result.status == TaskStatus.COMPLETED
        assert result.result == "result_value"
        assert result.completed_at is not None

    def test_task_failure(self):
        """タスク失敗テスト"""

        def failing_task():
            raise ValueError("テストエラー")

        service = BackgroundTaskService()
        task_id = service.submit(failing_task)

        # タスク完了を待機
        time.sleep(1)

        result = service.get_status(task_id)
        assert result is not None
        assert result.status == TaskStatus.FAILED
        assert "ValueError" in result.error
        assert "テストエラー" in result.error

    def test_task_with_args(self):
        """引数付きタスクテスト"""

        def add_task(a: int, b: int) -> int:
            return a + b

        service = BackgroundTaskService()
        task_id = service.submit(add_task, 3, 5)

        time.sleep(0.5)

        result = service.get_status(task_id)
        assert result is not None
        assert result.status == TaskStatus.COMPLETED
        assert result.result == 8

    def test_task_with_kwargs(self):
        """キーワード引数付きタスクテスト"""

        def greet_task(name: str, greeting: str = "Hello") -> str:
            return f"{greeting}, {name}!"

        service = BackgroundTaskService()
        task_id = service.submit(greet_task, name="World", greeting="Hi")

        time.sleep(0.5)

        result = service.get_status(task_id)
        assert result is not None
        assert result.status == TaskStatus.COMPLETED
        assert result.result == "Hi, World!"

    def test_get_nonexistent_task(self):
        """存在しないタスク取得テスト"""
        service = BackgroundTaskService()
        result = service.get_status("nonexistent_task_id")
        assert result is None

    def test_get_all_tasks(self):
        """全タスク取得テスト"""

        def dummy_task():
            return "done"

        service = BackgroundTaskService()
        service.submit(dummy_task)
        service.submit(dummy_task)
        service.submit(dummy_task)

        time.sleep(0.5)

        tasks = service.get_all_tasks()
        assert len(tasks) >= 3

    def test_get_all_tasks_with_filter(self):
        """フィルタ付き全タスク取得テスト"""

        def quick_task():
            return "done"

        def slow_task():
            time.sleep(2)
            return "done"

        service = BackgroundTaskService()
        service.submit(quick_task)
        service.submit(quick_task)
        service.submit(slow_task)

        time.sleep(0.5)

        completed_tasks = service.get_all_tasks(status=TaskStatus.COMPLETED)
        # 少なくとも2つは完了しているはず
        assert len(completed_tasks) >= 2

    def test_is_completed(self):
        """完了確認テスト"""

        def quick_task():
            return "done"

        service = BackgroundTaskService()
        task_id = service.submit(quick_task)

        # 最初は完了していない可能性
        time.sleep(0.5)

        # 完了している
        assert service.is_completed(task_id) is True

    def test_get_pending_count(self):
        """保留中タスク数取得テスト"""
        service = BackgroundTaskService()
        count = service.get_pending_count()
        assert isinstance(count, int)
        assert count >= 0

    def test_get_running_count(self):
        """実行中タスク数取得テスト"""
        service = BackgroundTaskService()
        count = service.get_running_count()
        assert isinstance(count, int)
        assert count >= 0

    def test_multiple_concurrent_tasks(self):
        """複数タスク同時実行テスト"""
        results = []

        def append_task(value: int):
            time.sleep(0.1)
            results.append(value)
            return value

        service = BackgroundTaskService(max_workers=4)

        # 4つのタスクを同時に登録
        task_ids = [service.submit(append_task, i) for i in range(4)]

        # 全タスク完了を待機
        time.sleep(1)

        # 全タスク完了確認
        for task_id in task_ids:
            assert service.is_completed(task_id) is True

        # 結果確認（順序は保証されない）
        assert sorted(results) == [0, 1, 2, 3]


class TestBackgroundTaskServiceSingleton:
    """get_task_serviceテスト"""

    def test_singleton(self):
        """シングルトンパターンテスト"""
        service1 = get_task_service()
        service2 = get_task_service()
        assert service1 is service2


class TestTaskStatus:
    """TaskStatusテスト"""

    def test_status_values(self):
        """ステータス値テスト"""
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.RUNNING == "running"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"


@pytest.mark.asyncio
class TestAsyncTasks:
    """非同期タスクテスト"""

    async def test_submit_async(self):
        """非同期タスク登録テスト"""

        async def async_task():
            await asyncio.sleep(0.1)
            return "async_done"

        service = BackgroundTaskService()
        task_id = await service.submit_async(async_task)

        assert task_id.startswith("task_")

        # 完了を待機
        await asyncio.sleep(0.5)

        result = service.get_status(task_id)
        assert result is not None
        assert result.status == TaskStatus.COMPLETED
        assert result.result == "async_done"

    async def test_submit_async_with_args(self):
        """引数付き非同期タスクテスト"""

        async def async_multiply(a: int, b: int) -> int:
            await asyncio.sleep(0.1)
            return a * b

        service = BackgroundTaskService()
        task_id = await service.submit_async(async_multiply, 3, 4)

        await asyncio.sleep(0.5)

        result = service.get_status(task_id)
        assert result is not None
        assert result.status == TaskStatus.COMPLETED
        assert result.result == 12
