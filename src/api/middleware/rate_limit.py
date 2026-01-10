"""
APIレート制限ミドルウェア

プラン別のレート制限を実装し、DDoS攻撃やAPI濫用を防止
"""

import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass
from threading import Lock
from typing import Callable, Dict, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """レート制限設定"""

    requests_per_minute: int
    requests_per_day: int
    burst_limit: int  # 短時間の連続リクエスト上限


# プラン別レート制限設定
PLAN_RATE_LIMITS: Dict[str, RateLimitConfig] = {
    "free": RateLimitConfig(
        requests_per_minute=30,
        requests_per_day=1000,
        burst_limit=10,
    ),
    "pro": RateLimitConfig(
        requests_per_minute=60,
        requests_per_day=5000,
        burst_limit=20,
    ),
    "business": RateLimitConfig(
        requests_per_minute=120,
        requests_per_day=20000,
        burst_limit=50,
    ),
    "enterprise": RateLimitConfig(
        requests_per_minute=300,
        requests_per_day=100000,
        burst_limit=100,
    ),
}

# 未認証ユーザーのレート制限（IP単位）
ANONYMOUS_RATE_LIMIT = RateLimitConfig(
    requests_per_minute=20,
    requests_per_day=200,
    burst_limit=5,
)


@dataclass
class RateLimitState:
    """レート制限状態"""

    minute_count: int = 0
    minute_reset: float = 0.0
    day_count: int = 0
    day_reset: float = 0.0
    burst_count: int = 0
    burst_reset: float = 0.0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    APIレート制限ミドルウェア

    - IP/ユーザー別のリクエスト制限
    - プラン別の制限値適用
    - バースト制限（短時間の連続リクエスト防止）
    - Redis利用可能時は分散レート制限対応
    """

    # バースト制限のウィンドウ（秒）
    BURST_WINDOW = 1.0

    def __init__(self, app, redis_client=None):
        """
        初期化

        Args:
            app: FastAPIアプリケーション
            redis_client: Redisクライアント（分散環境用、オプション）
        """
        super().__init__(app)
        self._states: Dict[str, RateLimitState] = defaultdict(RateLimitState)
        self._lock = Lock()
        self._redis = redis_client
        self._enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"

        if not self._enabled:
            logger.info("レート制限は無効化されています")

    def _get_client_identifier(self, request: Request) -> tuple[str, str]:
        """
        クライアント識別子とプランを取得

        Args:
            request: HTTPリクエスト

        Returns:
            (識別子, プラン) のタプル
        """
        # 認証ヘッダーからユーザーID取得を試みる
        # 実際の実装ではJWTトークンからユーザー情報を取得
        user_id = getattr(request.state, "user_id", None)
        user_plan = getattr(request.state, "user_plan", None)

        if user_id:
            return f"user:{user_id}", user_plan or "free"

        # 未認証の場合はIPアドレスを使用
        client_ip = request.client.host if request.client else "unknown"

        # X-Forwarded-For対応（プロキシ経由の場合）
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()

        return f"ip:{client_ip}", "anonymous"

    def _get_rate_limit_config(self, plan: str) -> RateLimitConfig:
        """
        プランに対応するレート制限設定を取得

        Args:
            plan: プラン名

        Returns:
            レート制限設定
        """
        if plan == "anonymous":
            return ANONYMOUS_RATE_LIMIT
        return PLAN_RATE_LIMITS.get(plan, PLAN_RATE_LIMITS["free"])

    def _check_rate_limit(
        self, identifier: str, config: RateLimitConfig
    ) -> tuple[bool, dict]:
        """
        レート制限チェック

        Args:
            identifier: クライアント識別子
            config: レート制限設定

        Returns:
            (許可, 制限情報) のタプル
        """
        now = time.time()

        with self._lock:
            state = self._states[identifier]

            # バースト制限チェック
            if now >= state.burst_reset:
                state.burst_count = 0
                state.burst_reset = now + self.BURST_WINDOW

            if state.burst_count >= config.burst_limit:
                return False, {
                    "limit_type": "burst",
                    "limit": config.burst_limit,
                    "remaining": 0,
                    "reset": int(state.burst_reset),
                }

            # 分単位制限チェック
            if now >= state.minute_reset:
                state.minute_count = 0
                state.minute_reset = now + 60

            if state.minute_count >= config.requests_per_minute:
                return False, {
                    "limit_type": "minute",
                    "limit": config.requests_per_minute,
                    "remaining": 0,
                    "reset": int(state.minute_reset),
                }

            # 日単位制限チェック
            if now >= state.day_reset:
                state.day_count = 0
                state.day_reset = now + 86400  # 24時間

            if state.day_count >= config.requests_per_day:
                return False, {
                    "limit_type": "day",
                    "limit": config.requests_per_day,
                    "remaining": 0,
                    "reset": int(state.day_reset),
                }

            # カウント更新
            state.burst_count += 1
            state.minute_count += 1
            state.day_count += 1

            return True, {
                "limit_type": "ok",
                "minute_limit": config.requests_per_minute,
                "minute_remaining": config.requests_per_minute - state.minute_count,
                "minute_reset": int(state.minute_reset),
                "day_limit": config.requests_per_day,
                "day_remaining": config.requests_per_day - state.day_count,
                "day_reset": int(state.day_reset),
            }

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
        # レート制限が無効の場合はスキップ
        if not self._enabled:
            return await call_next(request)

        # 静的ファイルやヘルスチェックはスキップ
        skip_paths = ["/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico"]
        if any(request.url.path.startswith(p) for p in skip_paths):
            return await call_next(request)

        # クライアント識別とレート制限チェック
        identifier, plan = self._get_client_identifier(request)
        config = self._get_rate_limit_config(plan)
        allowed, limit_info = self._check_rate_limit(identifier, config)

        if not allowed:
            logger.warning(
                f"レート制限超過: {identifier}, "
                f"type={limit_info['limit_type']}, "
                f"path={request.url.path}"
            )

            return JSONResponse(
                status_code=429,
                content={
                    "detail": "リクエスト制限を超過しました。しばらくしてから再試行してください。",
                    "error": "rate_limit_exceeded",
                    "limit_type": limit_info["limit_type"],
                    "retry_after": limit_info["reset"] - int(time.time()),
                },
                headers={
                    "Retry-After": str(limit_info["reset"] - int(time.time())),
                    "X-RateLimit-Limit": str(limit_info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(limit_info["reset"]),
                },
            )

        # 通常処理
        response = await call_next(request)

        # レート制限情報をヘッダーに追加
        response.headers["X-RateLimit-Limit-Minute"] = str(limit_info["minute_limit"])
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            limit_info["minute_remaining"]
        )
        response.headers["X-RateLimit-Reset-Minute"] = str(limit_info["minute_reset"])
        response.headers["X-RateLimit-Limit-Day"] = str(limit_info["day_limit"])
        response.headers["X-RateLimit-Remaining-Day"] = str(limit_info["day_remaining"])
        response.headers["X-RateLimit-Reset-Day"] = str(limit_info["day_reset"])

        return response

    def cleanup_expired_states(self) -> int:
        """
        期限切れの状態をクリーンアップ

        Returns:
            削除された状態の数
        """
        now = time.time()
        expired_keys = []

        with self._lock:
            for key, state in self._states.items():
                # 1日以上経過した状態を削除
                if (
                    now >= state.day_reset
                    and now >= state.minute_reset
                    and now >= state.burst_reset
                ):
                    expired_keys.append(key)

            for key in expired_keys:
                del self._states[key]

        if expired_keys:
            logger.info(f"期限切れレート制限状態を削除: {len(expired_keys)}件")

        return len(expired_keys)


def get_rate_limit_stats() -> dict:
    """
    レート制限統計取得

    Returns:
        統計情報
    """
    return {
        "plans": {
            name: {
                "requests_per_minute": config.requests_per_minute,
                "requests_per_day": config.requests_per_day,
                "burst_limit": config.burst_limit,
            }
            for name, config in PLAN_RATE_LIMITS.items()
        },
        "anonymous": {
            "requests_per_minute": ANONYMOUS_RATE_LIMIT.requests_per_minute,
            "requests_per_day": ANONYMOUS_RATE_LIMIT.requests_per_day,
            "burst_limit": ANONYMOUS_RATE_LIMIT.burst_limit,
        },
    }
