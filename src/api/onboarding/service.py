"""
オンボーディングサービス

新規ユーザーのオンボーディングフローを管理するサービス
"""

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from ..db.models import User
from ..schemas import (
    OnboardingStep,
    OnboardingStepName,
    OnboardingStepStatus,
    OnboardingStatusResponse,
)


class OnboardingService:
    """オンボーディングサービス"""

    # オンボーディングステップの順序
    STEP_ORDER = [
        OnboardingStepName.WELCOME,
        OnboardingStepName.CONNECT_PLATFORM,
        OnboardingStepName.SELECT_GOALS,
        OnboardingStepName.SETUP_NOTIFICATIONS,
        OnboardingStepName.FIRST_ANALYSIS,
        OnboardingStepName.COMPLETE,
    ]

    def __init__(self, db: Session):
        self.db = db

    def _get_steps_data(self, user: User) -> dict[str, Any]:
        """ユーザーのオンボーディングステップデータを取得"""
        try:
            return json.loads(user.onboarding_steps or "{}")
        except (json.JSONDecodeError, TypeError):
            return {}

    def _save_steps_data(self, user: User, steps_data: dict[str, Any]) -> None:
        """ユーザーのオンボーディングステップデータを保存"""
        user.onboarding_steps = json.dumps(steps_data)
        self.db.commit()

    def get_status(self, user: User) -> OnboardingStatusResponse:
        """オンボーディング状態を取得"""
        steps_data = self._get_steps_data(user)
        steps: list[OnboardingStep] = []
        current_step = OnboardingStepName.WELCOME
        completed_count = 0

        for step_name in self.STEP_ORDER:
            step_info = steps_data.get(step_name.value, {})
            status = OnboardingStepStatus(
                step_info.get("status", OnboardingStepStatus.NOT_STARTED.value)
            )
            completed_at = None
            if step_info.get("completed_at"):
                try:
                    completed_at = datetime.fromisoformat(step_info["completed_at"])
                except (ValueError, TypeError):
                    pass

            steps.append(
                OnboardingStep(
                    name=step_name,
                    status=status,
                    completed_at=completed_at,
                    data=step_info.get("data"),
                )
            )

            if status in (
                OnboardingStepStatus.COMPLETED,
                OnboardingStepStatus.SKIPPED,
            ):
                completed_count += 1
            elif status == OnboardingStepStatus.NOT_STARTED and current_step == OnboardingStepName.WELCOME:
                # 最初の未完了ステップを現在のステップとする
                current_step = step_name

        # 現在のステップを正確に判定
        for step_name in self.STEP_ORDER:
            step_info = steps_data.get(step_name.value, {})
            status = step_info.get("status", OnboardingStepStatus.NOT_STARTED.value)
            if status not in (
                OnboardingStepStatus.COMPLETED.value,
                OnboardingStepStatus.SKIPPED.value,
            ):
                current_step = step_name
                break

        # 進捗率計算（COMPLETEステップを除く5ステップ）
        progress_percent = int((completed_count / (len(self.STEP_ORDER) - 1)) * 100)
        if user.onboarding_completed:
            progress_percent = 100

        return OnboardingStatusResponse(
            is_completed=user.onboarding_completed,
            current_step=current_step,
            steps=steps,
            started_at=user.onboarding_started_at,
            completed_at=user.onboarding_completed_at,
            progress_percent=min(progress_percent, 100),
        )

    def start_onboarding(self, user: User) -> OnboardingStatusResponse:
        """オンボーディングを開始"""
        now = datetime.now(timezone.utc)

        # 既に開始済みの場合は現在の状態を返す
        if user.onboarding_started_at:
            return self.get_status(user)

        # オンボーディング開始
        user.onboarding_started_at = now
        user.onboarding_completed = False

        # welcomeステップをin_progressに設定
        steps_data = self._get_steps_data(user)
        steps_data[OnboardingStepName.WELCOME.value] = {
            "status": OnboardingStepStatus.IN_PROGRESS.value,
        }
        self._save_steps_data(user, steps_data)

        return self.get_status(user)

    def complete_step(
        self,
        user: User,
        step_name: OnboardingStepName,
        data: dict[str, Any] | None = None,
    ) -> OnboardingStatusResponse:
        """ステップを完了"""
        now = datetime.now(timezone.utc)
        steps_data = self._get_steps_data(user)

        # ステップを完了済みに設定
        steps_data[step_name.value] = {
            "status": OnboardingStepStatus.COMPLETED.value,
            "completed_at": now.isoformat(),
            "data": data,
        }

        # 次のステップをin_progressに設定
        step_index = self.STEP_ORDER.index(step_name)
        if step_index + 1 < len(self.STEP_ORDER):
            next_step = self.STEP_ORDER[step_index + 1]
            if next_step.value not in steps_data:
                steps_data[next_step.value] = {}
            if steps_data[next_step.value].get("status") != OnboardingStepStatus.COMPLETED.value:
                steps_data[next_step.value]["status"] = OnboardingStepStatus.IN_PROGRESS.value

        # COMPLETEステップが完了した場合、オンボーディング全体を完了
        if step_name == OnboardingStepName.COMPLETE:
            user.onboarding_completed = True
            user.onboarding_completed_at = now

        self._save_steps_data(user, steps_data)

        return self.get_status(user)

    def skip_step(
        self,
        user: User,
        step_name: OnboardingStepName,
    ) -> OnboardingStatusResponse:
        """ステップをスキップ"""
        now = datetime.now(timezone.utc)
        steps_data = self._get_steps_data(user)

        # スキップ可能なステップかチェック（WELCOMEとCOMPLETEはスキップ不可）
        if step_name in (OnboardingStepName.WELCOME, OnboardingStepName.COMPLETE):
            raise ValueError(f"ステップ '{step_name.value}' はスキップできません")

        # ステップをスキップ済みに設定
        steps_data[step_name.value] = {
            "status": OnboardingStepStatus.SKIPPED.value,
            "completed_at": now.isoformat(),
        }

        # 次のステップをin_progressに設定
        step_index = self.STEP_ORDER.index(step_name)
        if step_index + 1 < len(self.STEP_ORDER):
            next_step = self.STEP_ORDER[step_index + 1]
            if next_step.value not in steps_data:
                steps_data[next_step.value] = {}
            steps_data[next_step.value]["status"] = OnboardingStepStatus.IN_PROGRESS.value

        self._save_steps_data(user, steps_data)

        return self.get_status(user)

    def skip_all(self, user: User) -> OnboardingStatusResponse:
        """オンボーディング全体をスキップ"""
        now = datetime.now(timezone.utc)

        user.onboarding_completed = True
        user.onboarding_completed_at = now
        if not user.onboarding_started_at:
            user.onboarding_started_at = now

        # 全ステップをスキップ済みに設定
        steps_data = {}
        for step_name in self.STEP_ORDER:
            steps_data[step_name.value] = {
                "status": OnboardingStepStatus.SKIPPED.value,
                "completed_at": now.isoformat(),
            }

        self._save_steps_data(user, steps_data)

        return self.get_status(user)

    def reset_onboarding(self, user: User) -> OnboardingStatusResponse:
        """オンボーディングをリセット（開発/テスト用）"""
        user.onboarding_completed = False
        user.onboarding_started_at = None
        user.onboarding_completed_at = None
        user.onboarding_steps = "{}"
        self.db.commit()

        return self.get_status(user)
