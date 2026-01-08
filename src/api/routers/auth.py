"""
認証エンドポイント
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from ..schemas import (
    ErrorResponse,
    LoginRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
    UserRole,
)

router = APIRouter()
security = HTTPBearer()

# 仮のインメモリストレージ（本番ではDBを使用）
_users_db: dict[str, dict] = {}
_tokens_db: dict[str, dict] = {}

# 設定（本番では環境変数から読み込む）
TOKEN_EXPIRE_HOURS = 24
SECRET_KEY = "dev-secret-key-change-in-production"


def _hash_password(password: str) -> str:
    """パスワードハッシュ化（本番ではbcrypt使用推奨）"""
    return hashlib.sha256((password + SECRET_KEY).encode()).hexdigest()


def _generate_token() -> str:
    """トークン生成"""
    return secrets.token_urlsafe(32)


def _generate_user_id() -> str:
    """ユーザーID生成"""
    return f"user_{secrets.token_hex(8)}"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """現在のユーザーを取得"""
    token = credentials.credentials
    token_data = _tokens_db.get(token)

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効なトークン",
        )

    if datetime.now(timezone.utc) > token_data["expires_at"]:
        del _tokens_db[token]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="トークンの有効期限切れ",
        )

    user = _users_db.get(token_data["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザーが見つかりません",
        )

    return user


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}},
)
async def register(user_data: UserCreate) -> UserResponse:
    """ユーザー登録"""
    # メール重複チェック
    for user in _users_db.values():
        if user["email"] == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="このメールアドレスは既に使用されています",
            )

    user_id = _generate_user_id()
    now = datetime.now(timezone.utc)

    user = {
        "id": user_id,
        "email": user_data.email,
        "username": user_data.username,
        "password_hash": _hash_password(user_data.password),
        "role": UserRole.FREE,
        "created_at": now,
        "is_active": True,
    }

    _users_db[user_id] = user

    return UserResponse(
        id=user_id,
        email=user_data.email,
        username=user_data.username,
        role=UserRole.FREE,
        created_at=now,
        is_active=True,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse}},
)
async def login(login_data: LoginRequest) -> TokenResponse:
    """ログイン"""
    # ユーザー検索
    user = None
    for u in _users_db.values():
        if u["email"] == login_data.email:
            user = u
            break

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="メールアドレスまたはパスワードが正しくありません",
        )

    # パスワード検証
    if user["password_hash"] != _hash_password(login_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="メールアドレスまたはパスワードが正しくありません",
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="アカウントが無効化されています",
        )

    # トークン生成
    token = _generate_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)

    _tokens_db[token] = {
        "user_id": user["id"],
        "expires_at": expires_at,
    }

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=TOKEN_EXPIRE_HOURS * 3600,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> None:
    """ログアウト"""
    token = credentials.credentials
    if token in _tokens_db:
        del _tokens_db[token]


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)) -> UserResponse:
    """現在のユーザー情報取得"""
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        username=current_user["username"],
        role=current_user["role"],
        created_at=current_user["created_at"],
        is_active=current_user["is_active"],
    )
