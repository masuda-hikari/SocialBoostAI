"""
Redisキャッシュサービス

パフォーマンス最適化のためのキャッシュレイヤー
"""

import json
import os
from datetime import timedelta
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T")

# Redis接続（オプション）
_redis_client: Optional[Any] = None


def _get_redis_client():
    """Redis クライアント取得（遅延初期化）"""
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                import redis

                _redis_client = redis.from_url(redis_url, decode_responses=True)
                # 接続テスト
                _redis_client.ping()
            except Exception:
                # Redis接続失敗時はNone（フォールバック）
                _redis_client = None
    return _redis_client


class CacheService:
    """
    キャッシュサービス

    Redis利用可能時はRedisを使用、そうでなければインメモリキャッシュ
    """

    def __init__(self):
        """初期化"""
        self.redis = _get_redis_client()
        self._memory_cache: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        """
        キャッシュ取得

        Args:
            key: キャッシュキー

        Returns:
            キャッシュ値（存在しない場合None）
        """
        if self.redis:
            try:
                data = self.redis.get(key)
                if data:
                    return json.loads(data)
            except Exception:
                pass
        else:
            # インメモリフォールバック
            import time

            if key in self._memory_cache:
                value, expires_at = self._memory_cache[key]
                if time.time() < expires_at:
                    return value
                else:
                    del self._memory_cache[key]
        return None

    def set(
        self, key: str, value: Any, ttl: int = 300, ttl_timedelta: Optional[timedelta] = None
    ) -> bool:
        """
        キャッシュ設定

        Args:
            key: キャッシュキー
            value: キャッシュ値（JSON シリアライズ可能）
            ttl: TTL（秒）デフォルト5分
            ttl_timedelta: TTL（timedelta形式）

        Returns:
            成功/失敗
        """
        if ttl_timedelta:
            ttl = int(ttl_timedelta.total_seconds())

        if self.redis:
            try:
                self.redis.setex(key, ttl, json.dumps(value, default=str))
                return True
            except Exception:
                pass
        else:
            # インメモリフォールバック
            import time

            self._memory_cache[key] = (value, time.time() + ttl)
            return True
        return False

    def delete(self, key: str) -> bool:
        """
        キャッシュ削除

        Args:
            key: キャッシュキー

        Returns:
            成功/失敗
        """
        if self.redis:
            try:
                self.redis.delete(key)
                return True
            except Exception:
                pass
        else:
            if key in self._memory_cache:
                del self._memory_cache[key]
                return True
        return False

    def delete_pattern(self, pattern: str) -> int:
        """
        パターンマッチでキャッシュ削除

        Args:
            pattern: キーパターン（例: "user:123:*"）

        Returns:
            削除件数
        """
        deleted = 0
        if self.redis:
            try:
                keys = self.redis.keys(pattern)
                if keys:
                    deleted = self.redis.delete(*keys)
            except Exception:
                pass
        else:
            # インメモリフォールバック（シンプルなプレフィックスマッチ）
            prefix = pattern.rstrip("*")
            to_delete = [k for k in self._memory_cache if k.startswith(prefix)]
            for k in to_delete:
                del self._memory_cache[k]
            deleted = len(to_delete)
        return deleted

    def clear_user_cache(self, user_id: str) -> int:
        """
        ユーザー関連キャッシュを全削除

        Args:
            user_id: ユーザーID

        Returns:
            削除件数
        """
        return self.delete_pattern(f"user:{user_id}:*")

    def is_redis_available(self) -> bool:
        """Redis利用可能かチェック"""
        if self.redis:
            try:
                return self.redis.ping()
            except Exception:
                pass
        return False


# シングルトンインスタンス
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """キャッシュサービス取得"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def cached(
    key_prefix: str,
    ttl: int = 300,
    key_builder: Optional[Callable[..., str]] = None,
):
    """
    キャッシュデコレーター

    Args:
        key_prefix: キャッシュキープレフィックス
        ttl: TTL（秒）
        key_builder: カスタムキー生成関数

    Example:
        @cached("user_stats", ttl=600)
        def get_user_stats(user_id: str):
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            cache = get_cache_service()

            # キー生成
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # デフォルト: 引数をキーに含める
                key_parts = [key_prefix]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)

            # キャッシュ取得
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 関数実行
            result = func(*args, **kwargs)

            # キャッシュ設定
            cache.set(cache_key, result, ttl=ttl)

            return result

        return wrapper

    return decorator


def cache_key_for_user(prefix: str, user_id: str, *suffixes: str) -> str:
    """
    ユーザー用キャッシュキー生成

    Args:
        prefix: プレフィックス
        user_id: ユーザーID
        suffixes: 追加サフィックス

    Returns:
        キャッシュキー
    """
    parts = [f"user:{user_id}", prefix]
    parts.extend(suffixes)
    return ":".join(parts)
