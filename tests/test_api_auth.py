"""
認証APIテスト
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


class TestAuthRegister:
    """ユーザー登録テスト"""

    def test_register_success(self):
        """正常にユーザー登録できる"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "password123",
                "username": "testuser",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"
        assert data["role"] == "free"
        assert data["is_active"] is True
        assert "id" in data

    def test_register_duplicate_email(self):
        """重複メールアドレスでエラー"""
        # 1回目の登録
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "dup@example.com",
                "password": "password123",
                "username": "testuser1",
            },
        )
        # 2回目の登録（同じメール）
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "dup@example.com",
                "password": "password456",
                "username": "testuser2",
            },
        )
        assert response.status_code == 400
        assert "既に使用" in response.json()["detail"]

    def test_register_invalid_email(self):
        """無効なメールアドレスでエラー"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "password": "password123",
                "username": "testuser",
            },
        )
        assert response.status_code == 422

    def test_register_short_password(self):
        """短すぎるパスワードでエラー"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "short",
                "username": "testuser",
            },
        )
        assert response.status_code == 422


class TestAuthLogin:
    """ログインテスト"""

    def test_login_success(self):
        """正常にログインできる"""
        # 登録
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@example.com",
                "password": "password123",
                "username": "testuser",
            },
        )
        # ログイン
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "login@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    def test_login_wrong_password(self):
        """間違ったパスワードでエラー"""
        # 登録
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "wrongpass@example.com",
                "password": "password123",
                "username": "testuser",
            },
        )
        # ログイン（間違ったパスワード）
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "wrongpass@example.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self):
        """存在しないユーザーでエラー"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 401


class TestAuthMe:
    """ユーザー情報取得テスト"""

    def test_get_me_success(self):
        """認証済みユーザーが自分の情報を取得できる"""
        # 登録
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "me@example.com",
                "password": "password123",
                "username": "testuser",
            },
        )
        # ログイン
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "me@example.com",
                "password": "password123",
            },
        )
        token = login_response.json()["access_token"]

        # 自分の情報取得
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"
        assert data["username"] == "testuser"

    def test_get_me_unauthorized(self):
        """未認証でエラー"""
        response = client.get("/api/v1/auth/me")
        # HTTPBearerは認証ヘッダーがない場合401/403を返す
        assert response.status_code in [401, 403]

    def test_get_me_invalid_token(self):
        """無効なトークンでエラー"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401


class TestAuthLogout:
    """ログアウトテスト"""

    def test_logout_success(self):
        """正常にログアウトできる"""
        # 登録
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "logout@example.com",
                "password": "password123",
                "username": "testuser",
            },
        )
        # ログイン
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "logout@example.com",
                "password": "password123",
            },
        )
        token = login_response.json()["access_token"]

        # ログアウト
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 204

        # ログアウト後にトークンが無効になっている
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401
