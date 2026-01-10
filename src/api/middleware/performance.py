"""
パフォーマンスモニタリングミドルウェア
"""

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    パフォーマンスモニタリングミドルウェア

    リクエスト処理時間を計測しログ出力
    """

    # 遅いリクエストの閾値（秒）
    SLOW_REQUEST_THRESHOLD = 1.0

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        リクエスト処理

        Args:
            request: HTTPリクエスト
            call_next: 次のミドルウェア/ハンドラ

        Returns:
            HTTPレスポンス
        """
        start_time = time.perf_counter()

        # リクエスト処理
        response = await call_next(request)

        # 処理時間計算
        process_time = time.perf_counter() - start_time

        # ヘッダーに処理時間追加
        response.headers["X-Process-Time"] = f"{process_time:.4f}"

        # ログ出力
        log_data = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time_ms": round(process_time * 1000, 2),
        }

        if process_time > self.SLOW_REQUEST_THRESHOLD:
            logger.warning(f"遅いリクエスト検出: {log_data}")
        else:
            logger.debug(f"リクエスト完了: {log_data}")

        return response


def get_performance_stats() -> dict:
    """
    パフォーマンス統計取得（将来の拡張用）

    Returns:
        統計情報
    """
    return {
        "note": "パフォーマンス統計機能は将来実装予定",
    }
