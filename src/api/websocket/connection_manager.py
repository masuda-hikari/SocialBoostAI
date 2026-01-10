"""
WebSocket接続管理
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import WebSocket, WebSocketDisconnect

from .types import Notification

logger = logging.getLogger(__name__)


@dataclass
class Connection:
    """WebSocket接続情報"""

    websocket: WebSocket
    user_id: str
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_ping: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ConnectionManager:
    """
    WebSocket接続管理クラス

    ユーザーごとの接続管理、メッセージブロードキャストを担当
    """

    def __init__(self):
        # user_id -> list[Connection]
        self._connections: dict[str, list[Connection]] = {}
        self._lock = asyncio.Lock()

    @property
    def connection_count(self) -> int:
        """総接続数"""
        return sum(len(conns) for conns in self._connections.values())

    @property
    def user_count(self) -> int:
        """接続ユーザー数"""
        return len(self._connections)

    async def connect(self, websocket: WebSocket, user_id: str) -> Connection:
        """
        WebSocket接続を受け入れ

        Args:
            websocket: WebSocket接続
            user_id: ユーザーID

        Returns:
            接続情報
        """
        await websocket.accept()
        connection = Connection(websocket=websocket, user_id=user_id)

        async with self._lock:
            if user_id not in self._connections:
                self._connections[user_id] = []
            self._connections[user_id].append(connection)

        logger.info(f"WebSocket接続: user_id={user_id}, 総接続数={self.connection_count}")
        return connection

    async def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        """
        WebSocket接続を切断

        Args:
            websocket: WebSocket接続
            user_id: ユーザーID
        """
        async with self._lock:
            if user_id in self._connections:
                self._connections[user_id] = [
                    conn for conn in self._connections[user_id]
                    if conn.websocket != websocket
                ]
                # 接続がなくなったら削除
                if not self._connections[user_id]:
                    del self._connections[user_id]

        logger.info(f"WebSocket切断: user_id={user_id}, 総接続数={self.connection_count}")

    async def send_to_user(
        self,
        user_id: str,
        notification: Notification,
    ) -> int:
        """
        特定ユーザーに通知を送信

        Args:
            user_id: ユーザーID
            notification: 通知

        Returns:
            送信成功した接続数
        """
        if user_id not in self._connections:
            return 0

        message = json.dumps(notification.to_dict(), ensure_ascii=False)
        sent_count = 0
        failed_connections: list[Connection] = []

        for connection in self._connections[user_id]:
            try:
                await connection.websocket.send_text(message)
                sent_count += 1
            except Exception as e:
                logger.warning(f"WebSocket送信失敗: user_id={user_id}, error={e}")
                failed_connections.append(connection)

        # 失敗した接続を削除
        if failed_connections:
            async with self._lock:
                for conn in failed_connections:
                    if user_id in self._connections:
                        self._connections[user_id] = [
                            c for c in self._connections[user_id]
                            if c.websocket != conn.websocket
                        ]

        return sent_count

    async def broadcast(self, notification: Notification) -> int:
        """
        全ユーザーにブロードキャスト

        Args:
            notification: 通知

        Returns:
            送信成功した接続数
        """
        total_sent = 0
        for user_id in list(self._connections.keys()):
            total_sent += await self.send_to_user(user_id, notification)
        return total_sent

    async def send_to_users(
        self,
        user_ids: list[str],
        notification: Notification,
    ) -> int:
        """
        複数ユーザーに通知を送信

        Args:
            user_ids: ユーザーIDリスト
            notification: 通知

        Returns:
            送信成功した接続数
        """
        total_sent = 0
        for user_id in user_ids:
            total_sent += await self.send_to_user(user_id, notification)
        return total_sent

    def is_user_connected(self, user_id: str) -> bool:
        """ユーザーが接続中か確認"""
        return user_id in self._connections and len(self._connections[user_id]) > 0

    def get_user_connections(self, user_id: str) -> list[Connection]:
        """ユーザーの接続リストを取得"""
        return self._connections.get(user_id, [])

    async def ping_all(self) -> dict[str, int]:
        """
        全接続にpingを送信（生存確認）

        Returns:
            {"success": 成功数, "failed": 失敗数}
        """
        success = 0
        failed = 0
        failed_connections: list[tuple[str, Connection]] = []

        for user_id, connections in self._connections.items():
            for conn in connections:
                try:
                    await conn.websocket.send_json({"type": "ping"})
                    conn.last_ping = datetime.now(timezone.utc)
                    success += 1
                except Exception:
                    failed += 1
                    failed_connections.append((user_id, conn))

        # 失敗した接続を削除
        async with self._lock:
            for user_id, conn in failed_connections:
                if user_id in self._connections:
                    self._connections[user_id] = [
                        c for c in self._connections[user_id]
                        if c.websocket != conn.websocket
                    ]
                    if not self._connections[user_id]:
                        del self._connections[user_id]

        return {"success": success, "failed": failed}

    def get_stats(self) -> dict[str, Any]:
        """接続統計を取得"""
        return {
            "total_connections": self.connection_count,
            "unique_users": self.user_count,
            "users": {
                user_id: len(conns)
                for user_id, conns in self._connections.items()
            },
        }


# シングルトンインスタンス
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """ConnectionManagerインスタンスを取得"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager
