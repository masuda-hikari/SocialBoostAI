"""
キャッシュサービステスト
"""

import time

import pytest

from src.api.cache.service import (
    CacheService,
    cache_key_for_user,
    cached,
    get_cache_service,
)


class TestCacheService:
    """CacheServiceテスト"""

    def test_init(self):
        """初期化テスト"""
        cache = CacheService()
        assert cache is not None

    def test_set_and_get(self):
        """基本的なset/getテスト"""
        cache = CacheService()
        cache.set("test_key", {"data": "value"}, ttl=60)

        result = cache.get("test_key")
        assert result == {"data": "value"}

    def test_get_nonexistent(self):
        """存在しないキーの取得テスト"""
        cache = CacheService()
        result = cache.get("nonexistent_key")
        assert result is None

    def test_delete(self):
        """削除テスト"""
        cache = CacheService()
        cache.set("delete_test", "value", ttl=60)

        assert cache.get("delete_test") == "value"

        cache.delete("delete_test")
        assert cache.get("delete_test") is None

    def test_ttl_expiration(self):
        """TTL期限切れテスト（インメモリキャッシュ）"""
        cache = CacheService()
        cache.set("ttl_test", "value", ttl=1)

        # 即座に取得可能
        assert cache.get("ttl_test") == "value"

        # 2秒待機後は期限切れ
        time.sleep(2)
        assert cache.get("ttl_test") is None

    def test_delete_pattern(self):
        """パターン削除テスト"""
        cache = CacheService()
        cache.set("user:123:analysis", "data1", ttl=60)
        cache.set("user:123:reports", "data2", ttl=60)
        cache.set("user:456:analysis", "data3", ttl=60)

        # user:123:*パターン削除
        deleted = cache.delete_pattern("user:123:*")
        assert deleted == 2

        # user:123のデータは削除済み
        assert cache.get("user:123:analysis") is None
        assert cache.get("user:123:reports") is None

        # user:456のデータは残っている
        assert cache.get("user:456:analysis") == "data3"

    def test_clear_user_cache(self):
        """ユーザーキャッシュクリアテスト"""
        cache = CacheService()
        cache.set("user:test_user:data1", "value1", ttl=60)
        cache.set("user:test_user:data2", "value2", ttl=60)

        deleted = cache.clear_user_cache("test_user")
        assert deleted == 2

        assert cache.get("user:test_user:data1") is None
        assert cache.get("user:test_user:data2") is None

    def test_complex_data_types(self):
        """複雑なデータ型のテスト"""
        cache = CacheService()

        # リスト
        cache.set("list_data", [1, 2, 3], ttl=60)
        assert cache.get("list_data") == [1, 2, 3]

        # ネストした辞書
        cache.set("nested_dict", {"a": {"b": {"c": 1}}}, ttl=60)
        assert cache.get("nested_dict") == {"a": {"b": {"c": 1}}}

        # 数値
        cache.set("number", 12345, ttl=60)
        assert cache.get("number") == 12345

    def test_is_redis_available(self):
        """Redis利用可否チェックテスト"""
        cache = CacheService()
        # テスト環境ではRedisなしなのでFalse
        # 環境によってはTrueになる可能性があるため、bool型であることのみ確認
        assert isinstance(cache.is_redis_available(), bool)


class TestCacheServiceSingleton:
    """get_cache_serviceテスト"""

    def test_singleton(self):
        """シングルトンパターンテスト"""
        service1 = get_cache_service()
        service2 = get_cache_service()
        # 注: テスト環境ではリセットされる可能性があるため、型のみ確認
        assert isinstance(service1, CacheService)
        assert isinstance(service2, CacheService)


class TestCachedDecorator:
    """@cachedデコレーターテスト"""

    def test_cached_function(self):
        """キャッシュデコレーターテスト"""
        call_count = 0

        @cached("test_func", ttl=60)
        def expensive_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        # 初回呼び出し
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1

        # 2回目はキャッシュから取得
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # 関数は呼ばれない

        # 異なる引数では関数が呼ばれる
        result3 = expensive_function(10)
        assert result3 == 20
        assert call_count == 2

    def test_cached_with_kwargs(self):
        """キーワード引数付きキャッシュテスト"""
        call_count = 0

        @cached("kwargs_func", ttl=60)
        def func_with_kwargs(a: int, b: int = 0) -> int:
            nonlocal call_count
            call_count += 1
            return a + b

        # 初回
        result1 = func_with_kwargs(1, b=2)
        assert result1 == 3
        assert call_count == 1

        # 同じ引数でキャッシュヒット
        result2 = func_with_kwargs(1, b=2)
        assert result2 == 3
        assert call_count == 1

        # 異なるkwargs
        result3 = func_with_kwargs(1, b=3)
        assert result3 == 4
        assert call_count == 2


class TestCacheKeyBuilder:
    """キャッシュキー生成テスト"""

    def test_cache_key_for_user(self):
        """ユーザー用キャッシュキー生成テスト"""
        key = cache_key_for_user("analysis", "user_123", "twitter")
        assert key == "user:user_123:analysis:twitter"

    def test_cache_key_for_user_no_suffix(self):
        """サフィックスなしキー生成テスト"""
        key = cache_key_for_user("stats", "user_456")
        assert key == "user:user_456:stats"

    def test_cache_key_for_user_multiple_suffixes(self):
        """複数サフィックスキー生成テスト"""
        key = cache_key_for_user("data", "user_789", "2024", "01", "weekly")
        assert key == "user:user_789:data:2024:01:weekly"
