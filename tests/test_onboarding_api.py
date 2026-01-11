"""
オンボーディングAPIのテスト
"""

import pytest
from fastapi.testclient import TestClient


class TestOnboardingStatus:
    """オンボーディング状態取得テスト"""

    def test_get_status_unauthorized(self, client: TestClient):
        """未認証ユーザーは状態取得できない"""
        response = client.get("/api/v1/onboarding/status")
        assert response.status_code == 401

    def test_get_status_new_user(self, client: TestClient, auth_headers_free: dict):
        """新規ユーザーの初期状態"""
        response = client.get("/api/v1/onboarding/status", headers=auth_headers_free)
        assert response.status_code == 200

        data = response.json()
        assert data["is_completed"] is False
        assert data["current_step"] == "welcome"
        assert data["progress_percent"] == 0
        assert len(data["steps"]) == 6

    def test_get_status_step_structure(self, client: TestClient, auth_headers_free: dict):
        """ステップ構造の検証"""
        response = client.get("/api/v1/onboarding/status", headers=auth_headers_free)
        assert response.status_code == 200

        data = response.json()
        step_names = [step["name"] for step in data["steps"]]
        expected_steps = [
            "welcome",
            "connect_platform",
            "select_goals",
            "setup_notifications",
            "first_analysis",
            "complete",
        ]
        assert step_names == expected_steps


class TestOnboardingStart:
    """オンボーディング開始テスト"""

    def test_start_onboarding(self, client: TestClient, auth_headers_free: dict):
        """オンボーディング開始"""
        response = client.post("/api/v1/onboarding/start", headers=auth_headers_free)
        assert response.status_code == 200

        data = response.json()
        assert data["is_completed"] is False
        assert data["started_at"] is not None

    def test_start_onboarding_idempotent(self, client: TestClient, auth_headers_free: dict):
        """オンボーディング開始は冪等"""
        # 1回目
        response1 = client.post("/api/v1/onboarding/start", headers=auth_headers_free)
        assert response1.status_code == 200
        started_at1 = response1.json()["started_at"]

        # 2回目
        response2 = client.post("/api/v1/onboarding/start", headers=auth_headers_free)
        assert response2.status_code == 200
        started_at2 = response2.json()["started_at"]

        # 開始日時は変わらない
        assert started_at1 == started_at2


class TestCompleteStep:
    """ステップ完了テスト"""

    def test_complete_welcome_step(self, client: TestClient, auth_headers_free: dict):
        """welcomeステップを完了"""
        # オンボーディング開始
        client.post("/api/v1/onboarding/start", headers=auth_headers_free)

        # welcomeステップ完了
        response = client.post(
            "/api/v1/onboarding/complete-step",
            headers=auth_headers_free,
            json={"step_name": "welcome"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["current_step"] == "connect_platform"
        assert data["progress_percent"] > 0

    def test_complete_step_with_data(self, client: TestClient, auth_headers_free: dict):
        """データ付きでステップ完了"""
        client.post("/api/v1/onboarding/start", headers=auth_headers_free)

        response = client.post(
            "/api/v1/onboarding/complete-step",
            headers=auth_headers_free,
            json={
                "step_name": "welcome",
                "data": {"language": "ja", "source": "search"},
            },
        )
        assert response.status_code == 200

    def test_complete_all_steps(self, client: TestClient, auth_headers_free: dict):
        """全ステップ完了"""
        client.post("/api/v1/onboarding/start", headers=auth_headers_free)

        steps = [
            "welcome",
            "connect_platform",
            "select_goals",
            "setup_notifications",
            "first_analysis",
            "complete",
        ]

        for step in steps:
            response = client.post(
                "/api/v1/onboarding/complete-step",
                headers=auth_headers_free,
                json={"step_name": step},
            )
            assert response.status_code == 200

        data = response.json()
        assert data["is_completed"] is True
        assert data["progress_percent"] == 100
        assert data["completed_at"] is not None


class TestSkipStep:
    """ステップスキップテスト"""

    def test_skip_step(self, client: TestClient, auth_headers_free: dict):
        """ステップをスキップ"""
        client.post("/api/v1/onboarding/start", headers=auth_headers_free)
        client.post(
            "/api/v1/onboarding/complete-step",
            headers=auth_headers_free,
            json={"step_name": "welcome"},
        )

        response = client.post(
            "/api/v1/onboarding/skip-step/connect_platform",
            headers=auth_headers_free,
        )
        assert response.status_code == 200

        data = response.json()
        # スキップしたステップの次に進む
        assert data["current_step"] == "select_goals"

    def test_skip_welcome_not_allowed(self, client: TestClient, auth_headers_free: dict):
        """welcomeステップはスキップ不可"""
        client.post("/api/v1/onboarding/start", headers=auth_headers_free)

        response = client.post(
            "/api/v1/onboarding/skip-step/welcome",
            headers=auth_headers_free,
        )
        assert response.status_code == 400

    def test_skip_complete_not_allowed(self, client: TestClient, auth_headers_free: dict):
        """completeステップはスキップ不可"""
        client.post("/api/v1/onboarding/start", headers=auth_headers_free)

        response = client.post(
            "/api/v1/onboarding/skip-step/complete",
            headers=auth_headers_free,
        )
        assert response.status_code == 400

    def test_skip_invalid_step(self, client: TestClient, auth_headers_free: dict):
        """無効なステップ名"""
        response = client.post(
            "/api/v1/onboarding/skip-step/invalid_step",
            headers=auth_headers_free,
        )
        assert response.status_code == 400


class TestSkipAll:
    """全スキップテスト"""

    def test_skip_all_onboarding(self, client: TestClient, auth_headers_free: dict):
        """オンボーディング全体をスキップ"""
        response = client.post(
            "/api/v1/onboarding/skip-all",
            headers=auth_headers_free,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["is_completed"] is True
        assert data["progress_percent"] == 100

    def test_skip_all_with_reason(self, client: TestClient, auth_headers_free: dict):
        """理由付きで全スキップ"""
        response = client.post(
            "/api/v1/onboarding/skip-all",
            headers=auth_headers_free,
            json={"reason": "既に使い方を知っている"},
        )
        assert response.status_code == 200


class TestResetOnboarding:
    """オンボーディングリセットテスト"""

    def test_reset_onboarding(self, client: TestClient, auth_headers_free: dict):
        """オンボーディングをリセット"""
        # まず開始して一部完了
        client.post("/api/v1/onboarding/start", headers=auth_headers_free)
        client.post(
            "/api/v1/onboarding/complete-step",
            headers=auth_headers_free,
            json={"step_name": "welcome"},
        )

        # リセット
        response = client.post("/api/v1/onboarding/reset", headers=auth_headers_free)
        assert response.status_code == 200

        data = response.json()
        assert data["is_completed"] is False
        assert data["started_at"] is None
        assert data["progress_percent"] == 0


class TestOnboardingProgress:
    """進捗計算テスト"""

    def test_progress_calculation(self, client: TestClient, auth_headers_free: dict):
        """進捗率が正しく計算される"""
        client.post("/api/v1/onboarding/start", headers=auth_headers_free)

        # 各ステップ完了時の進捗率を確認
        steps_progress = [
            ("welcome", 20),
            ("connect_platform", 40),
            ("select_goals", 60),
            ("setup_notifications", 80),
            ("first_analysis", 100),
        ]

        for step, expected_progress in steps_progress:
            response = client.post(
                "/api/v1/onboarding/complete-step",
                headers=auth_headers_free,
                json={"step_name": step},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["progress_percent"] == expected_progress
