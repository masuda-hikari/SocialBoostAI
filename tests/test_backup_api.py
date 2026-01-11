"""
バックアップAPI テスト
"""

import json
import gzip
from datetime import datetime, timedelta, timezone
from pathlib import Path
import secrets
import shutil
import tempfile

import pytest
from fastapi.testclient import TestClient

from src.api.backup.service import BackupService
from src.api.db.models import Analysis, Report, User
from src.api.main import app


class TestBackupAPIAuth:
    """バックアップAPI認証テスト"""

    def test_create_backup_unauthorized(self, client):
        """未認証ではバックアップ作成不可"""
        response = client.post("/api/v1/backup/create", json={})
        assert response.status_code == 401

    def test_create_backup_non_admin(self, client, auth_headers_free):
        """非管理者ではバックアップ作成不可"""
        response = client.post(
            "/api/v1/backup/create",
            json={},
            headers=auth_headers_free,
        )
        assert response.status_code == 403

    def test_list_backups_unauthorized(self, client):
        """未認証ではバックアップ一覧取得不可"""
        response = client.get("/api/v1/backup/list")
        assert response.status_code == 401

    def test_get_database_stats_unauthorized(self, client):
        """未認証ではデータベース統計取得不可"""
        response = client.get("/api/v1/backup/stats")
        assert response.status_code == 401


class TestBackupService:
    """バックアップサービステスト"""

    @pytest.fixture
    def temp_backup_dir(self):
        """一時バックアップディレクトリ"""
        temp_dir = Path(tempfile.mkdtemp())
        original_dir = BackupService.BACKUP_DIR
        BackupService.BACKUP_DIR = temp_dir
        yield temp_dir
        BackupService.BACKUP_DIR = original_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_create_backup(self, db_session, test_user, temp_backup_dir):
        """バックアップ作成テスト"""
        service = BackupService(db_session)
        result = service.create_backup()

        assert result["success"] is True
        assert "filename" in result
        assert "filepath" in result
        assert result["total_records"] >= 1  # 少なくともテストユーザーが存在

        # ファイルが存在するか確認
        filepath = Path(result["filepath"])
        assert filepath.exists()

        # 圧縮ファイルが読めるか確認
        with gzip.open(filepath, "rt", encoding="utf-8") as f:
            data = json.load(f)

        assert "version" in data
        assert "tables" in data
        assert "users" in data["tables"]

    def test_create_backup_exclude_tokens(self, db_session, test_user, temp_backup_dir):
        """トークン除外バックアップテスト"""
        from src.api.db.models import Token

        # テストトークン作成
        token = Token(
            token=secrets.token_hex(32),
            user_id=test_user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db_session.add(token)
        db_session.commit()

        service = BackupService(db_session)

        # トークン除外
        result = service.create_backup(include_tokens=False)
        assert result["success"] is True
        assert "tokens" not in result["record_counts"]

        # トークン含む
        result_with_tokens = service.create_backup(include_tokens=True)
        assert result_with_tokens["success"] is True
        assert result_with_tokens["record_counts"].get("tokens", 0) >= 1

    def test_list_backups(self, db_session, temp_backup_dir):
        """バックアップ一覧テスト"""
        import time

        service = BackupService(db_session)

        # バックアップを複数作成（タイムスタンプが異なるよう1秒以上待つ）
        result1 = service.create_backup()
        time.sleep(1.1)  # ファイル名のタイムスタンプが異なるように（秒単位）
        result2 = service.create_backup()

        # ファイル名が異なることを確認
        assert result1["filename"] != result2["filename"]

        backups = service.list_backups()
        assert len(backups) >= 2

        # 新しい順にソートされているか
        for i in range(len(backups) - 1):
            assert backups[i]["created_at"] >= backups[i + 1]["created_at"]

    def test_get_backup_info(self, db_session, test_user, temp_backup_dir):
        """バックアップ詳細取得テスト"""
        service = BackupService(db_session)
        result = service.create_backup()

        info = service.get_backup_info(result["filename"])
        assert info is not None
        assert info["filename"] == result["filename"]
        assert "tables" in info
        assert "total_records" in info

    def test_get_backup_info_not_found(self, db_session, temp_backup_dir):
        """存在しないバックアップテスト"""
        service = BackupService(db_session)
        info = service.get_backup_info("nonexistent.json.gz")
        assert info is None

    def test_delete_backup(self, db_session, temp_backup_dir):
        """バックアップ削除テスト"""
        service = BackupService(db_session)
        result = service.create_backup()

        # 削除
        delete_result = service.delete_backup(result["filename"])
        assert delete_result["success"] is True

        # 削除後に取得できないことを確認
        info = service.get_backup_info(result["filename"])
        assert info is None

    def test_delete_backup_not_found(self, db_session, temp_backup_dir):
        """存在しないバックアップ削除テスト"""
        service = BackupService(db_session)
        result = service.delete_backup("nonexistent.json.gz")
        assert result["success"] is False
        assert "見つかりません" in result["error"]

    def test_get_database_stats(self, db_session, test_user, temp_backup_dir):
        """データベース統計テスト"""
        service = BackupService(db_session)
        stats = service.get_database_stats()

        assert "tables" in stats
        assert "total_records" in stats
        assert stats["tables"]["users"] >= 1

    def test_cleanup_old_backups(self, db_session, temp_backup_dir):
        """古いバックアップクリーンアップテスト"""
        import os
        import time as time_module

        # 保持期間を短くしてテスト
        original_retention = BackupService.RETENTION_DAYS
        BackupService.RETENTION_DAYS = 1  # 1日に設定

        try:
            service = BackupService(db_session)

            # 古いバックアップを作成（ファイルの更新時刻を変更）
            result = service.create_backup()
            filepath = Path(result["filepath"])

            # ファイルの更新時刻を2日前に設定
            old_time = time_module.time() - (2 * 24 * 60 * 60)
            os.utime(filepath, (old_time, old_time))

            # 新しいバックアップも作成（ファイル名が異なるよう待つ）
            time_module.sleep(1.1)
            new_result = service.create_backup()

            # ファイルが別々であることを確認
            assert result["filename"] != new_result["filename"]

            # クリーンアップ実行（新しいserviceインスタンスで実行）
            cleanup_service = BackupService(db_session)
            cleanup_result = cleanup_service.cleanup_old_backups()
            assert cleanup_result["success"] is True
            assert cleanup_result["deleted_count"] >= 1

            # 古いファイルが削除されているか
            assert not filepath.exists()

            # 新しいファイルは残っているか
            assert Path(new_result["filepath"]).exists()
        finally:
            BackupService.RETENTION_DAYS = original_retention


class TestRestoreBackup:
    """リストアテスト"""

    @pytest.fixture
    def temp_backup_dir(self):
        """一時バックアップディレクトリ"""
        temp_dir = Path(tempfile.mkdtemp())
        original_dir = BackupService.BACKUP_DIR
        BackupService.BACKUP_DIR = temp_dir
        yield temp_dir
        BackupService.BACKUP_DIR = original_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_restore_dry_run(self, db_session, test_user, temp_backup_dir):
        """リストアドライランテスト"""
        service = BackupService(db_session)

        # バックアップ作成
        backup = service.create_backup()

        # ドライラン
        result = service.restore_backup(backup["filename"], dry_run=True)
        assert result["success"] is True
        assert result["dry_run"] is True
        assert "plan" in result

    def test_restore_not_found(self, db_session, temp_backup_dir):
        """存在しないバックアップリストアテスト"""
        service = BackupService(db_session)
        result = service.restore_backup("nonexistent.json.gz")
        assert result["success"] is False
        assert "見つかりません" in result["error"]


class TestUserDataManagement:
    """ユーザーデータ管理テスト（GDPR対応）"""

    @pytest.fixture
    def temp_backup_dir(self):
        """一時バックアップディレクトリ"""
        temp_dir = Path(tempfile.mkdtemp())
        original_dir = BackupService.BACKUP_DIR
        BackupService.BACKUP_DIR = temp_dir
        yield temp_dir
        BackupService.BACKUP_DIR = original_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_export_user_data(self, db_session, test_user, temp_backup_dir):
        """ユーザーデータエクスポートテスト"""
        # 分析データを追加
        analysis = Analysis(
            user_id=test_user.id,
            platform="twitter",
            period_start=datetime.now(timezone.utc) - timedelta(days=7),
            period_end=datetime.now(timezone.utc),
            total_posts=10,
        )
        db_session.add(analysis)
        db_session.commit()

        service = BackupService(db_session)
        result = service.export_user_data(test_user.id)

        assert result["success"] is True
        assert "data" in result
        assert result["data"]["user"]["email"] == test_user.email
        assert len(result["data"]["analyses"]) >= 1
        # パスワードハッシュが除外されているか
        assert "password_hash" not in result["data"]["user"]

    def test_export_user_data_not_found(self, db_session, temp_backup_dir):
        """存在しないユーザーデータエクスポートテスト"""
        service = BackupService(db_session)
        result = service.export_user_data("nonexistent_user_id")
        assert result["success"] is False
        assert "見つかりません" in result["error"]

    def test_delete_user_data_dry_run(self, db_session, test_user, temp_backup_dir):
        """ユーザーデータ削除ドライランテスト"""
        service = BackupService(db_session)
        result = service.delete_user_data(test_user.id, dry_run=True)

        assert result["success"] is True
        assert result["dry_run"] is True
        assert "will_delete" in result

        # ユーザーがまだ存在するか確認
        user = db_session.query(User).filter(User.id == test_user.id).first()
        assert user is not None

    def test_delete_user_data_not_found(self, db_session, temp_backup_dir):
        """存在しないユーザーデータ削除テスト"""
        service = BackupService(db_session)
        result = service.delete_user_data("nonexistent_user_id", dry_run=False)
        assert result["success"] is False
        assert "見つかりません" in result["error"]


class TestBackupAPIEndpoints:
    """バックアップAPIエンドポイントテスト"""

    @pytest.fixture
    def temp_backup_dir(self):
        """一時バックアップディレクトリ"""
        temp_dir = Path(tempfile.mkdtemp())
        original_dir = BackupService.BACKUP_DIR
        BackupService.BACKUP_DIR = temp_dir
        yield temp_dir
        BackupService.BACKUP_DIR = original_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_create_backup_endpoint(
        self, client, admin_headers, temp_backup_dir
    ):
        """バックアップ作成エンドポイントテスト"""
        response = client.post(
            "/api/v1/backup/create",
            json={"include_tokens": False, "include_logs": True},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "filename" in data

    def test_list_backups_endpoint(
        self, client, admin_headers, temp_backup_dir
    ):
        """バックアップ一覧エンドポイントテスト"""
        # まずバックアップを作成
        client.post(
            "/api/v1/backup/create",
            json={},
            headers=admin_headers,
        )

        response = client.get(
            "/api/v1/backup/list",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "backups" in data
        assert "total" in data

    def test_get_database_stats_endpoint(self, client, admin_headers):
        """データベース統計エンドポイントテスト"""
        response = client.get(
            "/api/v1/backup/stats",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "tables" in data
        assert "total_records" in data

    def test_export_user_data_endpoint(
        self, client, admin_headers, admin_user
    ):
        """ユーザーデータエクスポートエンドポイントテスト"""
        response = client.post(
            "/api/v1/backup/export-user-data",
            json={"user_id": admin_user.id},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_delete_user_data_endpoint_dry_run(
        self, client, admin_headers, test_user
    ):
        """ユーザーデータ削除エンドポイントテスト（ドライラン）"""
        response = client.post(
            "/api/v1/backup/delete-user-data",
            json={"user_id": test_user.id, "dry_run": True},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["dry_run"] is True
