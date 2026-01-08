"""
ユーザーエンドポイント
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from ..dependencies import CurrentUser, DbSession, hash_password, verify_password
from ..repositories import AnalysisRepository, ReportRepository, UserRepository
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


# API制限（プラン別）
API_LIMITS = {
    "free": 100,
    "pro": 1000,
    "business": 10000,
    "enterprise": 100000,
}


@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_current_user_profile(
    current_user: CurrentUser,
) -> UserResponse:
    """現在のユーザープロフィール取得"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        role=UserRole(current_user.role),
        created_at=current_user.created_at,
        is_active=current_user.is_active,
    )


@router.patch(
    "/me",
    response_model=UserResponse,
    responses={400: {"model": ErrorResponse}},
)
async def update_current_user(
    update_data: UserUpdateRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> UserResponse:
    """ユーザープロフィール更新"""
    user_repo = UserRepository(db)

    # メール重複チェック
    if update_data.email:
        existing_user = user_repo.get_by_email(update_data.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="このメールアドレスは既に使用されています",
            )

    # 更新
    updated_user = user_repo.update(
        user=current_user,
        username=update_data.username,
        email=update_data.email,
    )

    return UserResponse(
        id=updated_user.id,
        email=updated_user.email,
        username=updated_user.username,
        role=UserRole(updated_user.role),
        created_at=updated_user.created_at,
        is_active=updated_user.is_active,
    )


@router.post(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={400: {"model": ErrorResponse}},
)
async def change_password(
    password_data: PasswordChangeRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """パスワード変更"""
    # 現在のパスワード検証
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="現在のパスワードが正しくありません",
        )

    # 新しいパスワード設定
    user_repo = UserRepository(db)
    user_repo.update_password(
        user=current_user,
        password_hash=hash_password(password_data.new_password),
    )


@router.get(
    "/me/stats",
    response_model=UserStatsResponse,
)
async def get_user_stats(
    db: DbSession,
    current_user: CurrentUser,
) -> UserStatsResponse:
    """ユーザー統計取得"""
    analysis_repo = AnalysisRepository(db)
    report_repo = ReportRepository(db)

    # 統計取得
    total_analyses = analysis_repo.count_by_user_id(current_user.id)
    total_reports = report_repo.count_by_user_id(current_user.id)
    api_limit = API_LIMITS.get(current_user.role, API_LIMITS["free"])

    return UserStatsResponse(
        user_id=current_user.id,
        role=UserRole(current_user.role),
        total_analyses=total_analyses,
        total_reports=total_reports,
        api_calls_today=0,  # 本番ではRedis等から取得
        api_calls_limit=api_limit,
    )


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_current_user(
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """アカウント削除"""
    user_repo = UserRepository(db)

    # 論理削除
    user_repo.deactivate(current_user)
