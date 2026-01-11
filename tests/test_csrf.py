"""
CSRF保護ミドルウェアテスト
"""

import time

import pytest

from src.api.middleware.csrf import (
    CSRF_TOKEN_EXPIRE_SECONDS,
    generate_csrf_token,
    is_csrf_exempt,
    verify_csrf_token,
)


class TestGenerateCSRFToken:
    """CSRFトークン生成テスト"""

    def test_generate_token_format(self):
        """トークンが正しいフォーマットで生成される"""
        token = generate_csrf_token()
        parts = token.split(".")
        assert len(parts) == 3
        # timestamp.random_value.signature

    def test_generate_unique_tokens(self):
        """毎回異なるトークンが生成される"""
        tokens = [generate_csrf_token() for _ in range(10)]
        assert len(set(tokens)) == 10

    def test_generate_with_session_id(self):
        """セッションID付きでトークン生成"""
        token = generate_csrf_token(session_id="test-session")
        assert token is not None
        parts = token.split(".")
        assert len(parts) == 3


class TestVerifyCSRFToken:
    """CSRFトークン検証テスト"""

    def test_verify_valid_token(self):
        """有効なトークンの検証成功"""
        token = generate_csrf_token()
        assert verify_csrf_token(token) is True

    def test_verify_empty_token(self):
        """空トークンの検証失敗"""
        assert verify_csrf_token("") is False
        assert verify_csrf_token(None) is False

    def test_verify_invalid_format(self):
        """不正フォーマットの検証失敗"""
        assert verify_csrf_token("invalid") is False
        assert verify_csrf_token("a.b") is False
        assert verify_csrf_token("a.b.c.d") is False

    def test_verify_tampered_token(self):
        """改ざんトークンの検証失敗"""
        token = generate_csrf_token()
        parts = token.split(".")
        # タイムスタンプ改ざん
        tampered = f"9999999999.{parts[1]}.{parts[2]}"
        assert verify_csrf_token(tampered) is False

        # 署名改ざん
        tampered = f"{parts[0]}.{parts[1]}.{'x' * 32}"
        assert verify_csrf_token(tampered) is False

    def test_verify_expired_token(self):
        """期限切れトークンの検証失敗"""
        # 非常に短い有効期限でテスト
        token = generate_csrf_token()
        # max_age=0で即座に期限切れ
        assert verify_csrf_token(token, max_age=0) is False


class TestIsCSRFExempt:
    """CSRF除外パス判定テスト"""

    def test_exempt_login(self):
        """ログインパスは除外"""
        assert is_csrf_exempt("/api/v1/auth/login") is True

    def test_exempt_register(self):
        """登録パスは除外"""
        assert is_csrf_exempt("/api/v1/auth/register") is True

    def test_exempt_webhook(self):
        """Webhookパスは除外"""
        assert is_csrf_exempt("/api/v1/billing/webhook") is True

    def test_exempt_health(self):
        """ヘルスチェックパスは除外"""
        assert is_csrf_exempt("/health") is True
        assert is_csrf_exempt("/health/detailed") is True

    def test_exempt_docs(self):
        """ドキュメントパスは除外"""
        assert is_csrf_exempt("/docs") is True
        assert is_csrf_exempt("/redoc") is True
        assert is_csrf_exempt("/openapi.json") is True

    def test_exempt_websocket(self):
        """WebSocketパスは除外"""
        assert is_csrf_exempt("/ws") is True

    def test_not_exempt_api(self):
        """通常APIパスは除外されない"""
        assert is_csrf_exempt("/api/v1/analysis") is False
        assert is_csrf_exempt("/api/v1/users") is False
        assert is_csrf_exempt("/api/v1/reports") is False


class TestCSRFTokenExpiration:
    """CSRFトークン有効期限テスト"""

    def test_token_valid_within_expiry(self):
        """有効期限内のトークンは有効"""
        token = generate_csrf_token()
        # デフォルト有効期限（24時間）より十分短い時間
        assert verify_csrf_token(token, max_age=3600) is True

    def test_default_expiry_is_24_hours(self):
        """デフォルト有効期限は24時間"""
        assert CSRF_TOKEN_EXPIRE_SECONDS == 3600 * 24
