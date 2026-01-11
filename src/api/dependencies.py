"""
FastAPI 依存性注入
"""

import hashlib
import os
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .db import get_db
from .db.models import User
from .repositories import TokenRepository, UserRepository

# セキュリティ設定
security = HTTPBearer()
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
TOKEN_EXPIRE_HOURS = int(os.getenv("TOKEN_EXPIRE_HOURS", "24"))


def hash_password(password: str) -> str:
    """
    パスワードハッシュ化（本番ではbcrypt使用推奨）

    Args:
        password: 平文パスワード

    Returns:
        ハッシュ化されたパスワード
    """
    return hashlib.sha256((password + SECRET_KEY).encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """
    パスワード検証

    Args:
        password: 平文パスワード
        password_hash: ハッシュ化されたパスワード

    Returns:
        一致する場合True
    """
    return hash_password(password) == password_hash


# 型エイリアス
DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """
    現在のユーザーを取得

    Args:
        db: データベースセッション
        credentials: 認証情報

    Returns:
        現在のユーザー

    Raises:
        HTTPException: 認証エラー
    """
    token_str = credentials.credentials
    token_repo = TokenRepository(db)

    # トークン検証
    token = token_repo.get_valid_token(token_str)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効なトークンまたは有効期限切れ",
        )

    # ユーザー取得
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(token.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザーが見つかりません",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="アカウントが無効化されています",
        )

    return user


# 型エイリアス
CurrentUser = Annotated[User, Depends(get_current_user)]


# プラン階層定義
PLAN_HIERARCHY = {
    "free": 0,
    "pro": 1,
    "business": 2,
    "enterprise": 3,
}


def require_plan(required_plan: str):
    """
    特定のプラン以上を要求する依存性

    Args:
        required_plan: 必要なプラン（free, pro, business, enterprise）

    Returns:
        依存性関数
    """
    required_level = PLAN_HIERARCHY.get(required_plan.lower(), 0)

    def check_plan(current_user: User = Depends(get_current_user)) -> User:
        # Userモデルでは role フィールドにプラン情報を格納
        user_plan = getattr(current_user, "role", "free") or "free"
        user_level = PLAN_HIERARCHY.get(user_plan.lower(), 0)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"この機能には{required_plan}プラン以上が必要です",
            )
        return current_user

    return check_plan


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    管理者権限を要求する依存性

    Args:
        current_user: 現在のユーザー

    Returns:
        管理者ユーザー

    Raises:
        HTTPException: 管理者権限がない場合
    """
    user_role = getattr(current_user, "role", "free") or "free"

    # admin または enterprise を管理者として扱う
    if user_role.lower() not in ("admin", "enterprise"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です",
        )
    return current_user


# 型エイリアス
AdminUser = Annotated[User, Depends(require_admin)]
