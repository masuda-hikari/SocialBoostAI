"""
オンボーディングAPIルーター

新規ユーザーのオンボーディングフロー管理
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db import get_db
from ..db.models import User
from ..dependencies import get_current_user
from ..onboarding import OnboardingService
from ..schemas import (
    OnboardingCompleteStepRequest,
    OnboardingSkipRequest,
    OnboardingStatusResponse,
)

router = APIRouter()


def get_onboarding_service(db: Session = Depends(get_db)) -> OnboardingService:
    """オンボーディングサービスを取得"""
    return OnboardingService(db)


@router.get(
    "/status",
    response_model=OnboardingStatusResponse,
    summary="オンボーディング状態取得",
    description="現在のユーザーのオンボーディング進捗状態を取得します",
)
def get_onboarding_status(
    current_user: User = Depends(get_current_user),
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingStatusResponse:
    """オンボーディング状態を取得"""
    return service.get_status(current_user)


@router.post(
    "/start",
    response_model=OnboardingStatusResponse,
    summary="オンボーディング開始",
    description="オンボーディングフローを開始します",
)
def start_onboarding(
    current_user: User = Depends(get_current_user),
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingStatusResponse:
    """オンボーディングを開始"""
    return service.start_onboarding(current_user)


@router.post(
    "/complete-step",
    response_model=OnboardingStatusResponse,
    summary="ステップ完了",
    description="指定したオンボーディングステップを完了します",
)
def complete_step(
    request: OnboardingCompleteStepRequest,
    current_user: User = Depends(get_current_user),
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingStatusResponse:
    """オンボーディングステップを完了"""
    return service.complete_step(
        current_user,
        request.step_name,
        request.data,
    )


@router.post(
    "/skip-step/{step_name}",
    response_model=OnboardingStatusResponse,
    summary="ステップスキップ",
    description="指定したオンボーディングステップをスキップします",
)
def skip_step(
    step_name: str,
    current_user: User = Depends(get_current_user),
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingStatusResponse:
    """オンボーディングステップをスキップ"""
    from ..schemas import OnboardingStepName

    try:
        step = OnboardingStepName(step_name)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"無効なステップ名: {step_name}",
        )

    try:
        return service.skip_step(current_user, step)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/skip-all",
    response_model=OnboardingStatusResponse,
    summary="オンボーディング全スキップ",
    description="オンボーディング全体をスキップして完了状態にします",
)
def skip_all_onboarding(
    request: OnboardingSkipRequest | None = None,
    current_user: User = Depends(get_current_user),
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingStatusResponse:
    """オンボーディング全体をスキップ"""
    return service.skip_all(current_user)


@router.post(
    "/reset",
    response_model=OnboardingStatusResponse,
    summary="オンボーディングリセット",
    description="オンボーディング状態をリセットします（開発/テスト用）",
)
def reset_onboarding(
    current_user: User = Depends(get_current_user),
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingStatusResponse:
    """オンボーディングをリセット"""
    return service.reset_onboarding(current_user)
