"""
管理者APIテスト
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from src.api.db.models import Analysis, Report, ScheduledPost, Subscription, User
from src.api.main import app


class TestAdminAuth:
    """管理者認証テスト"""

    def test_require_admin_unauthorized(self, client: TestClient):
        """未認証ユーザーは管理者APIにアクセス不可（401）"""
        response = client.get("/api/v1/admin/users")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_require_admin_free_user(
        self, client: TestClient, auth_token: str
    ):
        """Freeプランユーザーは管理者APIにアクセス不可"""
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "管理者権限" in response.json()["detail"]

    def test_require_admin_pro_user(
        self, client: TestClient, db_session, auth_token: str, test_user: User
    ):
        """Proプランユーザーは管理者APIにアクセス不可"""
        # プランをProに変更
        test_user.role = "pro"
        db_session.commit()

        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_require_admin_enterprise_user(
        self, client: TestClient, db_session, auth_token: str, test_user: User
    ):
        """Enterpriseプランユーザーは管理者APIにアクセス可能"""
        # プランをEnterpriseに変更
        test_user.role = "enterprise"
        db_session.commit()

        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

    def test_require_admin_admin_user(
        self, client: TestClient, db_session, auth_token: str, test_user: User
    ):
        """adminロールユーザーは管理者APIにアクセス可能"""
        test_user.role = "admin"
        db_session.commit()

        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == status.HTTP_200_OK


class TestAdminUserManagement:
    """ユーザー管理APIテスト"""

    @pytest.fixture(autouse=True)
    def setup_admin(self, db_session, test_user: User):
        """管理者としてセットアップ"""
        test_user.role = "admin"
        db_session.commit()

    def test_list_users(self, client: TestClient, auth_token: str, test_user: User):
        """ユーザー一覧取得"""
        response = client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert data["total"] >= 1

    def test_list_users_pagination(
        self, client: TestClient, auth_token: str
    ):
        """ユーザー一覧ページネーション"""
        response = client.get(
            "/api/v1/admin/users?page=1&per_page=10",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 10

    def test_list_users_filter_role(
        self, client: TestClient, auth_token: str
    ):
        """ユーザー一覧プランフィルター"""
        response = client.get(
            "/api/v1/admin/users?role=admin",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # 全てがadminであることを確認
        for user in data["users"]:
            assert user["role"] == "admin"

    def test_list_users_search(
        self, client: TestClient, auth_token: str, test_user: User
    ):
        """ユーザー一覧検索"""
        response = client.get(
            f"/api/v1/admin/users?search={test_user.username}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 1

    def test_get_user_detail(
        self, client: TestClient, auth_token: str, test_user: User
    ):
        """ユーザー詳細取得"""
        response = client.get(
            f"/api/v1/admin/users/{test_user.id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert "analysis_count" in data
        assert "report_count" in data
        assert "scheduled_post_count" in data

    def test_get_user_detail_not_found(
        self, client: TestClient, auth_token: str
    ):
        """存在しないユーザー詳細取得"""
        response = client.get(
            "/api/v1/admin/users/nonexistent_user",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_user(
        self, client: TestClient, auth_token: str, db_session
    ):
        """ユーザー更新"""
        # 別のユーザーを作成
        from src.api.dependencies import hash_password

        other_user = User(
            id="test_other_user",
            email="other@test.com",
            username="other_user",
            password_hash=hash_password("password"),
            role="free",
        )
        db_session.add(other_user)
        db_session.commit()

        response = client.put(
            f"/api/v1/admin/users/{other_user.id}",
            json={"username": "updated_name", "role": "pro"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "updated_name"
        assert data["role"] == "pro"

    def test_update_user_invalid_role(
        self, client: TestClient, auth_token: str, db_session
    ):
        """無効なロールでユーザー更新"""
        from src.api.dependencies import hash_password

        other_user = User(
            id="test_invalid_role",
            email="invalid_role@test.com",
            username="invalid_role_user",
            password_hash=hash_password("password"),
            role="free",
        )
        db_session.add(other_user)
        db_session.commit()

        response = client.put(
            f"/api/v1/admin/users/{other_user.id}",
            json={"role": "invalid_role"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_delete_user(
        self, client: TestClient, auth_token: str, db_session
    ):
        """ユーザー削除（論理削除）"""
        from src.api.dependencies import hash_password

        other_user = User(
            id="test_delete_user",
            email="delete@test.com",
            username="delete_user",
            password_hash=hash_password("password"),
            role="free",
        )
        db_session.add(other_user)
        db_session.commit()

        response = client.delete(
            f"/api/v1/admin/users/{other_user.id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == status.HTTP_200_OK

        # 論理削除確認
        db_session.refresh(other_user)
        assert other_user.is_active is False

    def test_delete_self_forbidden(
        self, client: TestClient, auth_token: str, test_user: User
    ):
        """自分自身の削除は禁止"""
        response = client.delete(
            f"/api/v1/admin/users/{test_user.id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "自分自身" in response.json()["detail"]

    def test_reset_password(
        self, client: TestClient, auth_token: str, db_session
    ):
        """パスワードリセット"""
        from src.api.dependencies import hash_password

        other_user = User(
            id="test_reset_pw",
            email="reset@test.com",
            username="reset_user",
            password_hash=hash_password("password"),
            role="free",
        )
        db_session.add(other_user)
        db_session.commit()

        response = client.post(
            f"/api/v1/admin/users/{other_user.id}/reset-password",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "temporary_password" in data
        assert len(data["temporary_password"]) > 0


class TestAdminStats:
    """統計APIテスト"""

    @pytest.fixture(autouse=True)
    def setup_admin(self, db_session, test_user: User):
        """管理者としてセットアップ"""
        test_user.role = "admin"
        db_session.commit()

    def test_get_system_stats(
        self, client: TestClient, auth_token: str
    ):
        """システム統計取得"""
        response = client.get(
            "/api/v1/admin/stats/system",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_users" in data
        assert "active_users" in data
        assert "inactive_users" in data
        assert "users_by_plan" in data
        assert "total_analyses" in data
        assert "total_reports" in data
        assert "total_scheduled_posts" in data
        assert "new_users_today" in data
        assert "new_users_this_week" in data
        assert "new_users_this_month" in data

    def test_get_revenue_stats(
        self, client: TestClient, auth_token: str
    ):
        """収益統計取得"""
        response = client.get(
            "/api/v1/admin/stats/revenue",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "active_subscriptions" in data
        assert "subscriptions_by_plan" in data
        assert "monthly_recurring_revenue_jpy" in data
        assert "churn_rate" in data


class TestAdminActivityLog:
    """アクティビティログAPIテスト"""

    @pytest.fixture(autouse=True)
    def setup_admin(self, db_session, test_user: User):
        """管理者としてセットアップ"""
        test_user.role = "admin"
        db_session.commit()

    def test_get_activity_log(
        self, client: TestClient, auth_token: str
    ):
        """アクティビティログ取得"""
        response = client.get(
            "/api/v1/admin/activity",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "entries" in data
        assert "total" in data
        assert isinstance(data["entries"], list)

    def test_get_activity_log_pagination(
        self, client: TestClient, auth_token: str
    ):
        """アクティビティログページネーション"""
        response = client.get(
            "/api/v1/admin/activity?page=1&per_page=10",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == status.HTTP_200_OK
