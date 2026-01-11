"""
CSRF保護ミドルウェア

状態変更リクエスト（POST/PUT/DELETE/PATCH）に対してCSRFトークン検証を行う。
"""

import hashlib
import hmac
import os
import secrets
import time
from typing import Optional

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

# CSRF設定
CSRF_SECRET = os.getenv("CSRF_SECRET", os.getenv("SECRET_KEY", "dev-csrf-secret"))
CSRF_TOKEN_NAME = "X-CSRF-Token"
CSRF_COOKIE_NAME = "csrf_token"
CSRF_TOKEN_EXPIRE_SECONDS = 3600 * 24  # 24時間


def generate_csrf_token(session_id: Optional[str] = None) -> str:
    """
    CSRFトークン生成

    Args:
        session_id: セッションID（オプション）

    Returns:
        CSRFトークン
    """
    timestamp = str(int(time.time()))
    random_value = secrets.token_hex(16)
    session = session_id or "anonymous"

    # トークン生成: timestamp.random_value.signature
    data = f"{timestamp}.{random_value}.{session}"
    signature = hmac.new(
        CSRF_SECRET.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()

    return f"{timestamp}.{random_value}.{signature[:32]}"


def verify_csrf_token(token: str, max_age: int = CSRF_TOKEN_EXPIRE_SECONDS) -> bool:
    """
    CSRFトークン検証

    Args:
        token: CSRFトークン
        max_age: 最大有効期間（秒）

    Returns:
        検証成功の場合True
    """
    if not token:
        return False

    try:
        parts = token.split(".")
        if len(parts) != 3:
            return False

        timestamp, random_value, signature = parts

        # タイムスタンプ検証
        token_time = int(timestamp)
        current_time = int(time.time())

        # max_age=0の場合、同じ秒でも期限切れとする（即座に失効）
        if max_age == 0 or current_time - token_time > max_age:
            return False

        # 署名検証
        data = f"{timestamp}.{random_value}.anonymous"
        expected_signature = hmac.new(
            CSRF_SECRET.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()[:32]

        return hmac.compare_digest(signature, expected_signature)

    except (ValueError, AttributeError):
        return False


# CSRF保護から除外するパス
CSRF_EXEMPT_PATHS = [
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/billing/webhook",  # Stripe Webhook
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/ws",  # WebSocket
]


def is_csrf_exempt(path: str) -> bool:
    """
    CSRF保護除外パス判定

    Args:
        path: リクエストパス

    Returns:
        除外対象の場合True
    """
    for exempt_path in CSRF_EXEMPT_PATHS:
        if path.startswith(exempt_path):
            return True
    return False


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF保護ミドルウェア

    - GET/HEAD/OPTIONS以外のリクエストにCSRFトークン検証
    - レスポンスヘッダーにCSRFトークン付与
    - 環境変数CSRF_ENABLEDで有効/無効切替（デフォルト: 本番は有効）
    """

    def __init__(self, app, enabled: Optional[bool] = None):
        """
        初期化

        Args:
            app: FastAPIアプリケーション
            enabled: CSRF保護有効/無効（None時は環境変数参照）
        """
        super().__init__(app)
        if enabled is not None:
            self.enabled = enabled
        else:
            env_enabled = os.getenv("CSRF_ENABLED", "true")
            self.enabled = env_enabled.lower() in ("true", "1", "yes")

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        リクエスト処理

        Args:
            request: リクエスト
            call_next: 次のミドルウェア

        Returns:
            レスポンス
        """
        # CSRF保護無効時はスキップ
        if not self.enabled:
            return await call_next(request)

        # 除外パスはスキップ
        if is_csrf_exempt(request.url.path):
            response = await call_next(request)
            # GETリクエスト時はCSRFトークンを発行
            if request.method == "GET":
                self._set_csrf_token(response)
            return response

        # 安全なメソッドはスキップ（トークン発行のみ）
        if request.method in ("GET", "HEAD", "OPTIONS"):
            response = await call_next(request)
            self._set_csrf_token(response)
            return response

        # 状態変更リクエスト: CSRFトークン検証
        csrf_token_header = request.headers.get(CSRF_TOKEN_NAME)
        csrf_token_cookie = request.cookies.get(CSRF_COOKIE_NAME)

        # ヘッダーまたはCookieからトークン取得
        csrf_token = csrf_token_header or csrf_token_cookie

        if not csrf_token or not verify_csrf_token(csrf_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRFトークンが無効です。ページを再読み込みしてください。",
            )

        # 検証成功: リクエスト処理続行
        response = await call_next(request)
        self._set_csrf_token(response)
        return response

    def _set_csrf_token(self, response: Response) -> None:
        """
        レスポンスにCSRFトークン設定

        Args:
            response: レスポンス
        """
        token = generate_csrf_token()
        response.headers[CSRF_TOKEN_NAME] = token
        response.set_cookie(
            CSRF_COOKIE_NAME,
            token,
            max_age=CSRF_TOKEN_EXPIRE_SECONDS,
            httponly=False,  # JavaScriptからアクセス可能
            samesite="strict",
            secure=os.getenv("ENVIRONMENT", "development") == "production",
        )
