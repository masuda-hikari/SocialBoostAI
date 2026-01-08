"""
ユーザーエンドポイント
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from ..routers.auth import _hash_password, _users_db, get_current_user
from ..schemas import ErrorResponse, UserResponse, UserRole

router = APIRouter()


class UserUpdateRequest(BaseModel):
    """ユーザー更新リクエスト"""

    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: EmailStr | None = None


class PasswordChangeRequest(BaseModel):
    """パスワード変更リクエスト"""

    current_password: str
    new_password: str = Field(min_length=8)


class UserStatsResponse(BaseModel):
    """ユーザー統計レスポンス"""

    user_id: str
    role: UserRole
    total_analyses: int
    total_reports: int
    api_calls_today: int
    api_calls_limit: int


@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
) -> UserResponse:
    """現在のユーザープロフィール取得"""
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        username=current_user["username"],
        role=current_user["role"],
        created_at=current_user["created_at"],
        is_active=current_user["is_active"],
    )


@router.patch(
    "/me",
    response_model=UserResponse,
    responses={400: {"model": ErrorResponse}},
)
async def update_current_user(
    update_data: UserUpdateRequest,
    current_user: dict = Depends(get_current_user),
) -> UserResponse:
    """ユーザープロフィール更新"""
    user_id = current_user["id"]

    # メール重複チェック
    if update_data.email:
        for uid, user in _users_db.items():
            if uid != user_id and user["email"] == update_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="このメールアドレスは既に使用されています",
                )
        _users_db[user_id]["email"] = update_data.email

    if update_data.username:
        _users_db[user_id]["username"] = update_data.username

    updated_user = _users_db[user_id]

    return UserResponse(
        id=updated_user["id"],
        email=updated_user["email"],
        username=updated_user["username"],
        role=updated_user["role"],
        created_at=updated_user["created_at"],
        is_active=updated_user["is_active"],
    )


@router.post(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={400: {"model": ErrorResponse}},
)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user),
) -> None:
    """パスワード変更"""
    user_id = current_user["id"]

    # 現在のパスワード検証
    if _users_db[user_id]["password_hash"] != _hash_password(
        password_data.current_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="現在のパスワードが正しくありません",
        )

    # 新しいパスワード設定
    _users_db[user_id]["password_hash"] = _hash_password(password_data.new_password)


@router.get(
    "/me/stats",
    response_model=UserStatsResponse,
)
async def get_user_stats(
    current_user: dict = Depends(get_current_user),
) -> UserStatsResponse:
    """ユーザー統計取得"""
    # API制限（プラン別）
    api_limits = {
        UserRole.FREE: 100,
        UserRole.PRO: 1000,
        UserRole.BUSINESS: 10000,
        UserRole.ENTERPRISE: 100000,
    }

    return UserStatsResponse(
        user_id=current_user["id"],
        role=current_user["role"],
        total_analyses=0,  # 本番ではDBから取得
        total_reports=0,  # 本番ではDBから取得
        api_calls_today=0,  # 本番ではRedis等から取得
        api_calls_limit=api_limits[current_user["role"]],
    )


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_current_user(
    current_user: dict = Depends(get_current_user),
) -> None:
    """アカウント削除"""
    user_id = current_user["id"]

    # 論理削除（本番では関連データも処理）
    _users_db[user_id]["is_active"] = False

    # 物理削除する場合
    # del _users_db[user_id]
