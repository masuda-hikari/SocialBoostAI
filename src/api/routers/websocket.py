"""
WebSocket APIルーター
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from ..db import get_db
from ..repositories import TokenRepository, UserRepository
from ..websocket import (
    ConnectionManager,
    NotificationService,
    get_connection_manager,
    get_notification_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_user_from_token(
    token: str,
    db: Session,
) -> Optional[str]:
    """
    トークンからユーザーIDを取得

    Args:
        token: 認証トークン
        db: データベースセッション

    Returns:
        ユーザーID（無効な場合はNone）
    """
    token_repo = TokenRepository(db)
    token_obj = token_repo.get_valid_token(token)
    if not token_obj:
        return None

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(token_obj.user_id)
    if not user or not user.is_active:
        return None

    return user.id


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="認証トークン"),
):
    """
    WebSocket接続エンドポイント

    クライアントからのWebSocket接続を受け入れ、リアルタイム通知を送信する。

    **接続方法**:
    ```javascript
    const ws = new WebSocket('wss://api.example.com/ws?token=YOUR_TOKEN');
    ```

    **受信メッセージ形式**:
    ```json
    {
        "type": "analysis_complete",
        "payload": { ... },
        "timestamp": "2026-01-10T12:00:00Z",
        "notification_id": "notif_abc123"
    }
    ```

    **通知タイプ**:
    - analysis_started: 分析開始
    - analysis_progress: 分析進捗
    - analysis_complete: 分析完了
    - analysis_failed: 分析失敗
    - report_generating: レポート生成中
    - report_ready: レポート完了
    - subscription_updated: サブスクリプション更新
    - payment_failed: 支払い失敗
    - system_notification: システム通知
    - dashboard_update: ダッシュボード更新
    - metrics_update: メトリクス更新
    """
    # データベースセッション取得
    db = next(get_db())
    try:
        # トークン認証
        user_id = await get_user_from_token(token, db)
        if not user_id:
            await websocket.close(code=4001, reason="認証エラー")
            return

        # 接続管理
        manager = get_connection_manager()
        connection = await manager.connect(websocket, user_id)

        try:
            # 接続成功通知
            await websocket.send_json({
                "type": "connected",
                "payload": {
                    "message": "WebSocket接続成功",
                    "user_id": user_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            })

            # メッセージ受信ループ
            while True:
                data = await websocket.receive_json()
                # クライアントからのメッセージ処理
                msg_type = data.get("type", "")

                if msg_type == "ping":
                    # Ping応答
                    await websocket.send_json({"type": "pong"})

                elif msg_type == "subscribe":
                    # 特定チャネルの購読（将来拡張用）
                    channel = data.get("channel", "")
                    await websocket.send_json({
                        "type": "subscribed",
                        "payload": {"channel": channel},
                    })

                elif msg_type == "unsubscribe":
                    # 購読解除
                    channel = data.get("channel", "")
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "payload": {"channel": channel},
                    })

                else:
                    # 未知のメッセージタイプ
                    await websocket.send_json({
                        "type": "error",
                        "payload": {"message": f"未知のメッセージタイプ: {msg_type}"},
                    })

        except WebSocketDisconnect:
            logger.info(f"WebSocket切断: user_id={user_id}")
        finally:
            await manager.disconnect(websocket, user_id)

    finally:
        db.close()


@router.get("/ws/stats")
async def get_websocket_stats():
    """
    WebSocket接続統計を取得

    管理者向けエンドポイント。現在の接続状況を返す。

    Returns:
        接続統計
    """
    manager = get_connection_manager()
    return manager.get_stats()
