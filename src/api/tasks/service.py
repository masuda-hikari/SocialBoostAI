"""
バックグラウンドタスクサービス

FastAPI BackgroundTasksを活用した非同期処理基盤
"""

import asyncio
import inspect
import logging
import secrets
import traceback
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """タスクステータス"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskResult:
    """タスク実行結果"""

    task_id: str
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class BackgroundTaskService:
    """
    バックグラウンドタスクサービス

    重い処理を非同期で実行し、結果を追跡
    """

    def __init__(self, max_workers: int = 4):
        """
        初期化

        Args:
            max_workers: 最大ワーカー数
        """
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._tasks: dict[str, TaskResult] = {}
        self._max_history = 1000  # 保持する最大タスク履歴数

    def _generate_task_id(self) -> str:
        """タスクID生成"""
        return f"task_{secrets.token_hex(8)}"

    def _cleanup_old_tasks(self) -> None:
        """古いタスク履歴をクリーンアップ"""
        if len(self._tasks) > self._max_history:
            # 古い完了タスクを削除
            completed_tasks = [
                (tid, t)
                for tid, t in self._tasks.items()
                if t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
            ]
            completed_tasks.sort(key=lambda x: x[1].created_at)
            for tid, _ in completed_tasks[: len(self._tasks) - self._max_history]:
                del self._tasks[tid]

    def submit(
        self,
        func: Callable[..., Any],
        *args: Any,
        task_name: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        タスクを非同期実行キューに登録

        Args:
            func: 実行する関数
            *args: 関数の引数
            task_name: タスク名（ログ用）
            **kwargs: 関数のキーワード引数

        Returns:
            タスクID
        """
        task_id = self._generate_task_id()
        task_result = TaskResult(task_id=task_id, status=TaskStatus.PENDING)
        self._tasks[task_id] = task_result

        self._cleanup_old_tasks()

        def wrapper():
            task_result.status = TaskStatus.RUNNING
            task_result.started_at = datetime.now(timezone.utc)
            try:
                result = func(*args, **kwargs)
                task_result.result = result
                task_result.status = TaskStatus.COMPLETED
                logger.info(f"タスク完了: {task_id} ({task_name or func.__name__})")
            except Exception as e:
                task_result.error = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
                task_result.status = TaskStatus.FAILED
                logger.error(f"タスク失敗: {task_id} ({task_name or func.__name__}): {e}")
            finally:
                task_result.completed_at = datetime.now(timezone.utc)

        self._executor.submit(wrapper)
        logger.info(f"タスク登録: {task_id} ({task_name or func.__name__})")
        return task_id

    async def submit_async(
        self,
        func: Callable[..., Any],
        *args: Any,
        task_name: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        非同期関数をタスクキューに登録

        Args:
            func: 実行する非同期関数
            *args: 関数の引数
            task_name: タスク名（ログ用）
            **kwargs: 関数のキーワード引数

        Returns:
            タスクID
        """
        task_id = self._generate_task_id()
        task_result = TaskResult(task_id=task_id, status=TaskStatus.PENDING)
        self._tasks[task_id] = task_result

        self._cleanup_old_tasks()

        async def wrapper():
            task_result.status = TaskStatus.RUNNING
            task_result.started_at = datetime.now(timezone.utc)
            try:
                if inspect.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                task_result.result = result
                task_result.status = TaskStatus.COMPLETED
                logger.info(f"タスク完了: {task_id} ({task_name or func.__name__})")
            except Exception as e:
                task_result.error = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
                task_result.status = TaskStatus.FAILED
                logger.error(f"タスク失敗: {task_id} ({task_name or func.__name__}): {e}")
            finally:
                task_result.completed_at = datetime.now(timezone.utc)

        asyncio.create_task(wrapper())
        logger.info(f"非同期タスク登録: {task_id} ({task_name or func.__name__})")
        return task_id

    def get_status(self, task_id: str) -> Optional[TaskResult]:
        """
        タスクステータス取得

        Args:
            task_id: タスクID

        Returns:
            タスク結果（存在しない場合None）
        """
        return self._tasks.get(task_id)

    def get_all_tasks(
        self, status: Optional[TaskStatus] = None, limit: int = 100
    ) -> list[TaskResult]:
        """
        タスク一覧取得

        Args:
            status: フィルタするステータス
            limit: 取得件数

        Returns:
            タスク結果リスト
        """
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return tasks[:limit]

    def is_completed(self, task_id: str) -> bool:
        """タスク完了確認"""
        task = self._tasks.get(task_id)
        return task is not None and task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)

    def get_pending_count(self) -> int:
        """保留中タスク数取得"""
        return sum(1 for t in self._tasks.values() if t.status == TaskStatus.PENDING)

    def get_running_count(self) -> int:
        """実行中タスク数取得"""
        return sum(1 for t in self._tasks.values() if t.status == TaskStatus.RUNNING)

    def shutdown(self, wait: bool = True) -> None:
        """
        サービスシャットダウン

        Args:
            wait: タスク完了を待つか
        """
        self._executor.shutdown(wait=wait)


# シングルトンインスタンス
_task_service: Optional[BackgroundTaskService] = None


def get_task_service() -> BackgroundTaskService:
    """タスクサービス取得"""
    global _task_service
    if _task_service is None:
        _task_service = BackgroundTaskService()
    return _task_service
