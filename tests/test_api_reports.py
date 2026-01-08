"""
レポートAPIテスト
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.routers.auth import _tokens_db, _users_db
from src.api.routers.reports import _reports_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_db():
    """各テスト前にDBをクリア"""
    _users_db.clear()
    _tokens_db.clear()
    _reports_db.clear()
    yield
    _users_db.clear()
    _tokens_db.clear()
    _reports_db.clear()


@pytest.fixture
def auth_token():
    """認証トークン取得用フィクスチャ"""
    # 登録
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
            "username": "testuser",
        },
    )
    # ログイン
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123",
        },
    )
    return login_response.json()["access_token"]


class TestReportCreate:
    """レポート作成テスト"""

    def test_create_weekly_report_success(self, auth_token):
        """週次レポートを作成できる"""
        response = client.post(
            "/api/v1/reports/",
            json={
                "report_type": "weekly",
                "platform": "twitter",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["report_type"] == "weekly"
        assert data["platform"] == "twitter"
        assert "html_url" in data

    def test_create_monthly_report_forbidden_free(self, auth_token):
        """無料プランでは月次レポート作成不可"""
        response = client.post(
            "/api/v1/reports/",
            json={
                "report_type": "monthly",
                "platform": "twitter",
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 403
        assert "利用できません" in response.json()["detail"]

    def test_create_report_unauthorized(self):
        """未認証でレポート作成エラー"""
        response = client.post(
            "/api/v1/reports/",
            json={
                "report_type": "weekly",
                "platform": "twitter",
            },
        )
        # HTTPBearerは認証ヘッダーがない場合401を返す
        assert response.status_code == 401


class TestReportList:
    """レポート一覧テスト"""

    def test_list_reports_empty(self, auth_token):
        """レポートがない場合、空のリストを返す"""
        response = client.get(
            "/api/v1/reports/",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_reports_with_data(self, auth_token):
        """レポートがある場合、リストを返す"""
        # レポート作成
        client.post(
            "/api/v1/reports/",
            json={"report_type": "weekly", "platform": "twitter"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        client.post(
            "/api/v1/reports/",
            json={"report_type": "weekly", "platform": "twitter"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        response = client.get(
            "/api/v1/reports/",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2

    def test_list_reports_filter_by_type(self, auth_token):
        """レポートタイプでフィルタできる"""
        # レポート作成
        client.post(
            "/api/v1/reports/",
            json={"report_type": "weekly", "platform": "twitter"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        response = client.get(
            "/api/v1/reports/?report_type=weekly",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1

        response = client.get(
            "/api/v1/reports/?report_type=monthly",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0


class TestReportGet:
    """レポート詳細テスト"""

    def test_get_report_success(self, auth_token):
        """レポート詳細を取得できる"""
        # レポート作成
        create_response = client.post(
            "/api/v1/reports/",
            json={"report_type": "weekly", "platform": "twitter"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        report_id = create_response.json()["id"]

        # 詳細取得
        response = client.get(
            f"/api/v1/reports/{report_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == report_id

    def test_get_report_not_found(self, auth_token):
        """存在しないレポートでエラー"""
        response = client.get(
            "/api/v1/reports/nonexistent-id",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404


class TestReportDelete:
    """レポート削除テスト"""

    def test_delete_report_success(self, auth_token):
        """レポートを削除できる"""
        # レポート作成
        create_response = client.post(
            "/api/v1/reports/",
            json={"report_type": "weekly", "platform": "twitter"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        report_id = create_response.json()["id"]

        # 削除
        response = client.delete(
            f"/api/v1/reports/{report_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 204

        # 削除確認
        response = client.get(
            f"/api/v1/reports/{report_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404

    def test_delete_report_not_found(self, auth_token):
        """存在しないレポートの削除でエラー"""
        response = client.delete(
            "/api/v1/reports/nonexistent-id",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404
