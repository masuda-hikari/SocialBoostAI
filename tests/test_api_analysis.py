"""
分析APIテスト
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
            "email": "analysis@example.com",
            "password": "password123",
            "username": "testuser",
        },
    )
    # ログイン
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "analysis@example.com",
            "password": "password123",
        },
    )
    return login_response.json()["access_token"]


class TestAnalysisCreate:
    """分析作成テスト"""

    def test_create_analysis_success(self, auth_token):
        """正常に分析を作成できる"""
        response = client.post(
            "/api/v1/analysis/",
            json={
                "platform": "twitter",
                "period_days": 7,
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["platform"] == "twitter"
        assert "summary" in data
        assert data["summary"]["total_posts"] > 0

    def test_create_analysis_unauthorized(self):
        """未認証で分析作成エラー"""
        response = client.post(
            "/api/v1/analysis/",
            json={
                "platform": "twitter",
                "period_days": 7,
            },
        )
        # HTTPBearerは認証ヘッダーがない場合401/403を返す
        assert response.status_code in [401, 403]

    def test_create_analysis_period_limit(self, auth_token):
        """無料プランでは7日を超える期間指定でエラー"""
        response = client.post(
            "/api/v1/analysis/",
            json={
                "platform": "twitter",
                "period_days": 30,
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 403
        assert "7日まで" in response.json()["detail"]


class TestAnalysisList:
    """分析一覧テスト"""

    def test_list_analyses_empty(self, auth_token):
        """分析がない場合、空のリストを返す"""
        response = client.get(
            "/api/v1/analysis/",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_analyses_with_data(self, auth_token):
        """分析がある場合、リストを返す"""
        # 分析作成
        client.post(
            "/api/v1/analysis/",
            json={"platform": "twitter", "period_days": 7},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        client.post(
            "/api/v1/analysis/",
            json={"platform": "twitter", "period_days": 7},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        response = client.get(
            "/api/v1/analysis/",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2

    def test_list_analyses_pagination(self, auth_token):
        """ページネーションが正常に動作する"""
        # 5件の分析を作成
        for _ in range(5):
            client.post(
                "/api/v1/analysis/",
                json={"platform": "twitter", "period_days": 7},
                headers={"Authorization": f"Bearer {auth_token}"},
            )

        # 1ページ目（2件ずつ）
        response = client.get(
            "/api/v1/analysis/?page=1&per_page=2",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["pages"] == 3


class TestAnalysisGet:
    """分析詳細テスト"""

    def test_get_analysis_success(self, auth_token):
        """分析詳細を取得できる"""
        # 分析作成
        create_response = client.post(
            "/api/v1/analysis/",
            json={"platform": "twitter", "period_days": 7},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        analysis_id = create_response.json()["id"]

        # 詳細取得
        response = client.get(
            f"/api/v1/analysis/{analysis_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == analysis_id

    def test_get_analysis_not_found(self, auth_token):
        """存在しない分析でエラー"""
        response = client.get(
            "/api/v1/analysis/nonexistent-id",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404


class TestAnalysisDelete:
    """分析削除テスト"""

    def test_delete_analysis_success(self, auth_token):
        """分析を削除できる"""
        # 分析作成
        create_response = client.post(
            "/api/v1/analysis/",
            json={"platform": "twitter", "period_days": 7},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        analysis_id = create_response.json()["id"]

        # 削除
        response = client.delete(
            f"/api/v1/analysis/{analysis_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 204

        # 削除確認
        response = client.get(
            f"/api/v1/analysis/{analysis_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404

    def test_delete_analysis_not_found(self, auth_token):
        """存在しない分析の削除でエラー"""
        response = client.delete(
            "/api/v1/analysis/nonexistent-id",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 404
