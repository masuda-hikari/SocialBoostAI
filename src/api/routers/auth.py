"""
認証エンドポイント
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..db import get_db
from ..db.models import User
from ..dependencies import (
    TOKEN_EXPIRE_HOURS,
    CurrentUser,
    DbSession,
    hash_password,
    verify_password,
)
from ..repositories import TokenRepository, UserRepository
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


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}},
)
async def register(
    user_data: UserCreate,
    db: DbSession,
) -> UserResponse:
    """ユーザー登録"""
    user_repo = UserRepository(db)

    # メール重複チェック
    existing_user = user_repo.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このメールアドレスは既に使用されています",
        )

    # ユーザー作成
    user = user_repo.create(
        email=user_data.email,
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        role="free",
    )

    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        role=UserRole(user.role),
        created_at=user.created_at,
        is_active=user.is_active,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse}},
)
async def login(
    login_data: LoginRequest,
    db: DbSession,
) -> TokenResponse:
    """ログイン"""
    user_repo = UserRepository(db)
    token_repo = TokenRepository(db)

    # ユーザー検索
    user = user_repo.get_by_email(login_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="メールアドレスまたはパスワードが正しくありません",
        )

    # パスワード検証
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="メールアドレスまたはパスワードが正しくありません",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="アカウントが無効化されています",
        )

    # トークン生成
    token = token_repo.create(user_id=user.id, expire_hours=TOKEN_EXPIRE_HOURS)

    return TokenResponse(
        access_token=token.token,
        token_type="bearer",
        expires_in=TOKEN_EXPIRE_HOURS * 3600,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    db: DbSession,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> None:
    """ログアウト"""
    token_repo = TokenRepository(db)
    token_repo.delete_by_token_str(credentials.credentials)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> UserResponse:
    """現在のユーザー情報取得"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        role=UserRole(current_user.role),
        created_at=current_user.created_at,
        is_active=current_user.is_active,
    )
