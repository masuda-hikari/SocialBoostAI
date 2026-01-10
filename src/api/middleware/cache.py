"""
APIキャッシュミドルウェア
"""

import hashlib
import json
import logging
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from ..cache import get_cache_service

logger = logging.getLogger(__name__)


class CacheMiddleware(BaseHTTPMiddleware):
    """
    APIレスポンスキャッシュミドルウェア

    GETリクエストのレスポンスをキャッシュ
    """

    # キャッシュ対象パス（プレフィックス）
    CACHEABLE_PATHS = [
        "/api/v1/analysis",
        "/api/v1/reports",
        "/api/v1/users/me/stats",
        "/api/v1/billing/plans",
    ]

    # キャッシュ除外パス
    EXCLUDED_PATHS = [
        "/api/v1/auth",
        "/api/v1/billing/checkout",
        "/api/v1/billing/portal",
        "/api/v1/billing/webhook",
    ]

    # デフォルトTTL（秒）
    DEFAULT_TTL = 300  # 5分

    # パス別TTL設定
    PATH_TTL = {
        "/api/v1/billing/plans": 3600,  # 1時間
        "/api/v1/users/me/stats": 600,  # 10分
    }

    def _should_cache(self, request: Request) -> bool:
        """
        キャッシュ対象かチェック

        Args:
            request: HTTPリクエスト

        Returns:
            キャッシュ対象か
        """
        # GETリクエストのみ
        if request.method != "GET":
            return False

        # 除外パスチェック
        for path in self.EXCLUDED_PATHS:
            if request.url.path.startswith(path):
                return False

        # 対象パスチェック
        for path in self.CACHEABLE_PATHS:
            if request.url.path.startswith(path):
                return True

        return False

    def _generate_cache_key(self, request: Request) -> str:
        """
        キャッシュキー生成

        Args:
            request: HTTPリクエスト

        Returns:
            キャッシュキー
        """
        # パス + クエリパラメータ + 認証ユーザー
        key_parts = [
            request.url.path,
            str(request.query_params),
        ]

        # 認証ヘッダーがあればユーザー識別に使用
        auth_header = request.headers.get("Authorization", "")
        if auth_header:
            # トークンのハッシュを使用（セキュリティのため）
            token_hash = hashlib.md5(auth_header.encode()).hexdigest()[:8]
            key_parts.append(token_hash)

        key_string = ":".join(key_parts)
        return f"api_cache:{hashlib.md5(key_string.encode()).hexdigest()}"

    def _get_ttl(self, path: str) -> int:
        """
        パス別TTL取得

        Args:
            path: リクエストパス

        Returns:
            TTL（秒）
        """
        for prefix, ttl in self.PATH_TTL.items():
            if path.startswith(prefix):
                return ttl
        return self.DEFAULT_TTL

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
        # キャッシュ対象外の場合はそのまま処理
        if not self._should_cache(request):
            return await call_next(request)

        cache = get_cache_service()
        cache_key = self._generate_cache_key(request)

        # キャッシュ確認
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f"キャッシュヒット: {cache_key}")
            return Response(
                content=cached_data.get("body", ""),
                status_code=cached_data.get("status_code", 200),
                headers={
                    **cached_data.get("headers", {}),
                    "X-Cache": "HIT",
                },
                media_type=cached_data.get("media_type", "application/json"),
            )

        # リクエスト処理
        response = await call_next(request)

        # 成功レスポンスのみキャッシュ
        if 200 <= response.status_code < 300:
            # レスポンスボディ読み取り
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            # キャッシュ保存
            cache_data = {
                "body": body.decode("utf-8"),
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "media_type": response.media_type,
            }

            ttl = self._get_ttl(request.url.path)
            cache.set(cache_key, cache_data, ttl=ttl)
            logger.debug(f"キャッシュ保存: {cache_key} (TTL: {ttl}s)")

            # 新しいレスポンスを返す
            return Response(
                content=body,
                status_code=response.status_code,
                headers={**dict(response.headers), "X-Cache": "MISS"},
                media_type=response.media_type,
            )

        return response


def invalidate_cache_for_user(user_id: str) -> int:
    """
    ユーザー関連キャッシュを無効化

    Args:
        user_id: ユーザーID

    Returns:
        削除件数
    """
    cache = get_cache_service()
    return cache.clear_user_cache(user_id)


def invalidate_cache_pattern(pattern: str) -> int:
    """
    パターンでキャッシュ無効化

    Args:
        pattern: キーパターン

    Returns:
        削除件数
    """
    cache = get_cache_service()
    return cache.delete_pattern(pattern)
