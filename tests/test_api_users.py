"""
ユーザーAPIテスト
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


@pytest.fixture
def auth_token():
    """認証トークン取得用フィクスチャ"""
    # 登録
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "users@example.com",
            "password": "password123",
            "username": "testuser",
        },
    )
    # ログイン
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "users@example.com",
            "password": "password123",
        },
    )
    return login_response.json()["access_token"]


class TestUserProfile:
    """ユーザープロフィールテスト"""

    def test_get_profile(self, auth_token):
        """プロフィールを取得できる"""
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "users@example.com"
        assert data["username"] == "testuser"
        assert data["role"] == "free"

    def test_update_profile_username(self, auth_token):
        """ユーザー名を更新できる"""
        response = client.patch(
            "/api/v1/users/me",
            json={"username": "newusername"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newusername"

    def test_update_profile_email(self, auth_token):
        """メールアドレスを更新できる"""
        response = client.patch(
            "/api/v1/users/me",
            json={"email": "newemail@example.com"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newemail@example.com"

    def test_update_profile_duplicate_email(self, auth_token):
        """重複メールアドレスでエラー"""
        # 別のユーザーを登録
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "other@example.com",
                "password": "password123",
                "username": "otheruser",
            },
        )

        # 重複メールで更新試行
        response = client.patch(
            "/api/v1/users/me",
            json={"email": "other@example.com"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 400
        assert "既に使用" in response.json()["detail"]


class TestPasswordChange:
    """パスワード変更テスト"""

    def test_change_password_success(self, auth_token):
        """パスワードを変更できる"""
        response = client.post(
            "/api/v1/users/me/password",
            json={
                "current_password": "password123",
                "new_password": "newpassword123",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 204

        # 新しいパスワードでログイン
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "users@example.com",
                "password": "newpassword123",
            },
        )
        assert login_response.status_code == 200

    def test_change_password_wrong_current(self, auth_token):
        """間違った現在のパスワードでエラー"""
        response = client.post(
            "/api/v1/users/me/password",
            json={
                "current_password": "wrongpassword",
                "new_password": "newpassword123",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 400
        assert "正しくありません" in response.json()["detail"]


class TestUserStats:
    """ユーザー統計テスト"""

    def test_get_stats(self, auth_token):
        """統計を取得できる"""
        response = client.get(
            "/api/v1/users/me/stats",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert data["role"] == "free"
        assert data["api_calls_limit"] == 100


class TestUserDelete:
    """ユーザー削除テスト"""

    def test_delete_account(self, auth_token):
        """アカウントを削除できる"""
        response = client.delete(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 204

        # 削除後はログインできない（論理削除のため）
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "users@example.com",
                "password": "password123",
            },
        )
        assert login_response.status_code == 401
