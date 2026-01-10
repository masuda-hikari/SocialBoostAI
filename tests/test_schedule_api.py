"""
スケジュール投稿APIのテスト
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


class TestScheduleAPI:
    """スケジュール投稿APIのテスト"""

    def test_create_scheduled_post_requires_pro_plan(
        self, client: TestClient, auth_headers_free
    ):
        """Pro以上のプランが必要"""
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        response = client.post(
            "/api/v1/schedule",
            json={
                "platform": "twitter",
                "content": "テスト投稿",
                "scheduled_at": future,
            },
            headers=auth_headers_free,
        )
        assert response.status_code == 403

    def test_create_scheduled_post_success(
        self, client: TestClient, auth_headers_pro
    ):
        """Pro以上でスケジュール投稿を作成できる"""
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        response = client.post(
            "/api/v1/schedule",
            json={
                "platform": "twitter",
                "content": "テスト投稿",
                "hashtags": ["テスト"],
                "scheduled_at": future,
            },
            headers=auth_headers_pro,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "テスト投稿"
        assert data["hashtags"] == ["テスト"]
        assert data["status"] == "pending"

    def test_create_scheduled_post_past_time(
        self, client: TestClient, auth_headers_pro
    ):
        """過去の時刻にはスケジュールできない"""
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        response = client.post(
            "/api/v1/schedule",
            json={
                "platform": "twitter",
                "content": "テスト投稿",
                "scheduled_at": past,
            },
            headers=auth_headers_pro,
        )
        assert response.status_code == 400
        assert "過去" in response.json()["detail"]

    def test_list_scheduled_posts(
        self, client: TestClient, auth_headers_pro
    ):
        """スケジュール投稿一覧を取得できる"""
        # 投稿作成
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        client.post(
            "/api/v1/schedule",
            json={
                "platform": "twitter",
                "content": "テスト1",
                "scheduled_at": future,
            },
            headers=auth_headers_pro,
        )
        client.post(
            "/api/v1/schedule",
            json={
                "platform": "twitter",
                "content": "テスト2",
                "scheduled_at": future,
            },
            headers=auth_headers_pro,
        )

        # 一覧取得
        response = client.get("/api/v1/schedule", headers=auth_headers_pro)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2
        assert len(data["items"]) >= 2

    def test_list_scheduled_posts_with_filters(
        self, client: TestClient, auth_headers_pro
    ):
        """フィルタ付きで一覧を取得できる"""
        # 投稿作成
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        client.post(
            "/api/v1/schedule",
            json={
                "platform": "twitter",
                "content": "Twitter投稿",
                "scheduled_at": future,
            },
            headers=auth_headers_pro,
        )

        # プラットフォームでフィルタ
        response = client.get(
            "/api/v1/schedule?platform=twitter",
            headers=auth_headers_pro,
        )
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["platform"] == "twitter"

    def test_get_scheduled_post(
        self, client: TestClient, auth_headers_pro
    ):
        """スケジュール投稿を取得できる"""
        # 投稿作成
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        create_response = client.post(
            "/api/v1/schedule",
            json={
                "platform": "twitter",
                "content": "テスト投稿",
                "scheduled_at": future,
            },
            headers=auth_headers_pro,
        )
        post_id = create_response.json()["id"]

        # 取得
        response = client.get(
            f"/api/v1/schedule/{post_id}",
            headers=auth_headers_pro,
        )
        assert response.status_code == 200
        assert response.json()["id"] == post_id

    def test_get_scheduled_post_not_found(
        self, client: TestClient, auth_headers_pro
    ):
        """存在しない投稿は404"""
        response = client.get(
            "/api/v1/schedule/nonexistent",
            headers=auth_headers_pro,
        )
        assert response.status_code == 404

    def test_update_scheduled_post(
        self, client: TestClient, auth_headers_pro
    ):
        """スケジュール投稿を更新できる"""
        # 投稿作成
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        create_response = client.post(
            "/api/v1/schedule",
            json={
                "platform": "twitter",
                "content": "元のコンテンツ",
                "scheduled_at": future,
            },
            headers=auth_headers_pro,
        )
        post_id = create_response.json()["id"]

        # 更新
        response = client.put(
            f"/api/v1/schedule/{post_id}",
            json={
                "content": "更新後のコンテンツ",
            },
            headers=auth_headers_pro,
        )
        assert response.status_code == 200
        assert response.json()["content"] == "更新後のコンテンツ"

    def test_cancel_scheduled_post(
        self, client: TestClient, auth_headers_pro
    ):
        """スケジュール投稿をキャンセルできる"""
        # 投稿作成
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        create_response = client.post(
            "/api/v1/schedule",
            json={
                "platform": "twitter",
                "content": "テスト",
                "scheduled_at": future,
            },
            headers=auth_headers_pro,
        )
        post_id = create_response.json()["id"]

        # キャンセル
        response = client.post(
            f"/api/v1/schedule/{post_id}/cancel",
            headers=auth_headers_pro,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

    def test_delete_scheduled_post(
        self, client: TestClient, auth_headers_pro
    ):
        """スケジュール投稿を削除できる"""
        # 投稿作成
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        create_response = client.post(
            "/api/v1/schedule",
            json={
                "platform": "twitter",
                "content": "テスト",
                "scheduled_at": future,
            },
            headers=auth_headers_pro,
        )
        post_id = create_response.json()["id"]

        # 削除
        response = client.delete(
            f"/api/v1/schedule/{post_id}",
            headers=auth_headers_pro,
        )
        assert response.status_code == 204

        # 確認
        response = client.get(
            f"/api/v1/schedule/{post_id}",
            headers=auth_headers_pro,
        )
        assert response.status_code == 404

    def test_get_schedule_stats(
        self, client: TestClient, auth_headers_pro
    ):
        """スケジュール統計を取得できる"""
        # 投稿作成
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        client.post(
            "/api/v1/schedule",
            json={
                "platform": "twitter",
                "content": "テスト",
                "scheduled_at": future,
            },
            headers=auth_headers_pro,
        )

        # 統計取得
        response = client.get(
            "/api/v1/schedule/stats",
            headers=auth_headers_pro,
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_scheduled" in data
        assert "pending" in data
        assert "by_platform" in data

    def test_get_upcoming_posts(
        self, client: TestClient, auth_headers_pro
    ):
        """今後の投稿を取得できる"""
        # 投稿作成
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        client.post(
            "/api/v1/schedule",
            json={
                "platform": "twitter",
                "content": "1時間後",
                "scheduled_at": future,
            },
            headers=auth_headers_pro,
        )

        # 今後の投稿取得
        response = client.get(
            "/api/v1/schedule/upcoming?hours=24",
            headers=auth_headers_pro,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_bulk_create_requires_business_plan(
        self, client: TestClient, auth_headers_pro
    ):
        """一括作成はBusiness以上が必要"""
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        response = client.post(
            "/api/v1/schedule/bulk",
            json={
                "posts": [
                    {
                        "platform": "twitter",
                        "content": "テスト1",
                        "scheduled_at": future,
                    },
                    {
                        "platform": "twitter",
                        "content": "テスト2",
                        "scheduled_at": future,
                    },
                ]
            },
            headers=auth_headers_pro,
        )
        assert response.status_code == 403

    def test_bulk_create_success(
        self, client: TestClient, auth_headers_business
    ):
        """Business以上で一括作成できる"""
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        response = client.post(
            "/api/v1/schedule/bulk",
            json={
                "posts": [
                    {
                        "platform": "twitter",
                        "content": "テスト1",
                        "scheduled_at": future,
                    },
                    {
                        "platform": "twitter",
                        "content": "テスト2",
                        "scheduled_at": future,
                    },
                ]
            },
            headers=auth_headers_business,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["created"] == 2
        assert data["failed"] == 0
        assert len(data["scheduled_posts"]) == 2
