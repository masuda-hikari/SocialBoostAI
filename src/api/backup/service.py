"""
データベースバックアップサービス

本番運用に必須のデータ保護機能を提供
- 自動バックアップ
- 手動バックアップ
- リストア機能
- バックアップ履歴管理
"""

import gzip
import json
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from ..db.models import (
    Analysis,
    CrossPlatformComparison,
    PushNotificationLog,
    PushSubscription,
    Report,
    ScheduledPost,
    Subscription,
    Token,
    User,
)


class BackupService:
    """データベースバックアップサービス"""

    # バックアップディレクトリ
    BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "backups"))

    # バックアップ保持期間（日数）
    RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))

    # バックアップ対象テーブル（依存関係順）
    TABLES = [
        User,
        Token,
        Analysis,
        Report,
        Subscription,
        ScheduledPost,
        PushSubscription,
        PushNotificationLog,
        CrossPlatformComparison,
    ]

    def __init__(self, db: Session):
        """
        初期化

        Args:
            db: SQLAlchemyセッション
        """
        self.db = db
        self._ensure_backup_dir()

    def _ensure_backup_dir(self) -> None:
        """バックアップディレクトリを作成"""
        self.BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    def _get_backup_filename(self, prefix: str = "backup") -> str:
        """バックアップファイル名を生成"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.json.gz"

    def _serialize_model(self, obj: Any) -> dict:
        """SQLAlchemyモデルをdictに変換"""
        result = {}
        inspector = inspect(obj.__class__)
        for column in inspector.columns:
            value = getattr(obj, column.key)
            if isinstance(value, datetime):
                result[column.key] = value.isoformat()
            else:
                result[column.key] = value
        return result

    def _deserialize_datetime(self, data: dict, fields: list[str]) -> dict:
        """datetimeフィールドをパース"""
        for field in fields:
            if field in data and data[field]:
                try:
                    data[field] = datetime.fromisoformat(data[field])
                except (ValueError, TypeError):
                    pass
        return data

    def create_backup(
        self,
        include_tokens: bool = False,
        include_logs: bool = True,
    ) -> dict:
        """
        データベースバックアップを作成

        Args:
            include_tokens: 認証トークンを含めるか
            include_logs: 通知ログを含めるか

        Returns:
            バックアップ結果（ファイルパス、サイズ、レコード数）
        """
        backup_data = {
            "version": "1.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "tables": {},
            "metadata": {
                "include_tokens": include_tokens,
                "include_logs": include_logs,
            },
        }

        record_counts = {}

        for model in self.TABLES:
            table_name = model.__tablename__

            # トークンをスキップする場合
            if table_name == "tokens" and not include_tokens:
                continue

            # 通知ログをスキップする場合
            if table_name == "push_notification_logs" and not include_logs:
                continue

            # データを取得
            records = self.db.query(model).all()
            backup_data["tables"][table_name] = [
                self._serialize_model(record) for record in records
            ]
            record_counts[table_name] = len(records)

        # ファイルに保存（gzip圧縮）
        filename = self._get_backup_filename()
        filepath = self.BACKUP_DIR / filename

        with gzip.open(filepath, "wt", encoding="utf-8") as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=None)

        # ファイルサイズ取得
        file_size = filepath.stat().st_size

        return {
            "success": True,
            "filename": filename,
            "filepath": str(filepath),
            "file_size_bytes": file_size,
            "file_size_human": self._format_file_size(file_size),
            "record_counts": record_counts,
            "total_records": sum(record_counts.values()),
            "created_at": backup_data["created_at"],
        }

    def _format_file_size(self, size_bytes: int) -> str:
        """ファイルサイズを人間が読みやすい形式に変換"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def list_backups(self) -> list[dict]:
        """
        バックアップファイル一覧を取得

        Returns:
            バックアップファイル情報のリスト
        """
        backups = []

        for filepath in self.BACKUP_DIR.glob("*.json.gz"):
            stat = filepath.stat()
            backups.append({
                "filename": filepath.name,
                "filepath": str(filepath),
                "file_size_bytes": stat.st_size,
                "file_size_human": self._format_file_size(stat.st_size),
                "created_at": datetime.fromtimestamp(
                    stat.st_mtime, tz=timezone.utc
                ).isoformat(),
            })

        # 作成日時でソート（新しい順）
        backups.sort(key=lambda x: x["created_at"], reverse=True)

        return backups

    def get_backup_info(self, filename: str) -> dict | None:
        """
        バックアップファイルの詳細情報を取得

        Args:
            filename: バックアップファイル名

        Returns:
            バックアップ情報（メタデータ、レコード数等）
        """
        filepath = self.BACKUP_DIR / filename

        if not filepath.exists():
            return None

        try:
            with gzip.open(filepath, "rt", encoding="utf-8") as f:
                data = json.load(f)

            stat = filepath.stat()

            return {
                "filename": filename,
                "filepath": str(filepath),
                "file_size_bytes": stat.st_size,
                "file_size_human": self._format_file_size(stat.st_size),
                "version": data.get("version", "unknown"),
                "created_at": data.get("created_at"),
                "metadata": data.get("metadata", {}),
                "tables": {
                    table: len(records)
                    for table, records in data.get("tables", {}).items()
                },
                "total_records": sum(
                    len(records)
                    for records in data.get("tables", {}).values()
                ),
            }
        except (json.JSONDecodeError, gzip.BadGzipFile) as e:
            return {
                "filename": filename,
                "filepath": str(filepath),
                "error": f"ファイルの読み込みに失敗: {str(e)}",
            }

    def delete_backup(self, filename: str) -> dict:
        """
        バックアップファイルを削除

        Args:
            filename: バックアップファイル名

        Returns:
            削除結果
        """
        filepath = self.BACKUP_DIR / filename

        if not filepath.exists():
            return {
                "success": False,
                "error": "ファイルが見つかりません",
            }

        try:
            filepath.unlink()
            return {
                "success": True,
                "message": f"バックアップを削除しました: {filename}",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"削除に失敗: {str(e)}",
            }

    def cleanup_old_backups(self) -> dict:
        """
        古いバックアップを削除

        Returns:
            削除結果（削除数、解放サイズ）
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.RETENTION_DAYS)
        deleted_count = 0
        freed_bytes = 0

        for filepath in self.BACKUP_DIR.glob("*.json.gz"):
            stat = filepath.stat()
            created = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)

            if created < cutoff:
                freed_bytes += stat.st_size
                filepath.unlink()
                deleted_count += 1

        return {
            "success": True,
            "deleted_count": deleted_count,
            "freed_bytes": freed_bytes,
            "freed_human": self._format_file_size(freed_bytes),
            "retention_days": self.RETENTION_DAYS,
        }

    def restore_backup(
        self,
        filename: str,
        dry_run: bool = True,
        clear_existing: bool = False,
    ) -> dict:
        """
        バックアップからリストア

        Args:
            filename: バックアップファイル名
            dry_run: Trueの場合、実際には復元せずシミュレーションのみ
            clear_existing: Trueの場合、既存データを削除してからリストア

        Returns:
            リストア結果
        """
        filepath = self.BACKUP_DIR / filename

        if not filepath.exists():
            return {
                "success": False,
                "error": "バックアップファイルが見つかりません",
            }

        try:
            with gzip.open(filepath, "rt", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, gzip.BadGzipFile) as e:
            return {
                "success": False,
                "error": f"バックアップファイルの読み込みに失敗: {str(e)}",
            }

        # バージョンチェック
        version = data.get("version", "unknown")
        if version != "1.0":
            return {
                "success": False,
                "error": f"サポートされていないバックアップバージョン: {version}",
            }

        # リストア計画
        plan = {
            "tables": {},
            "total_records": 0,
        }

        tables_data = data.get("tables", {})

        for model in self.TABLES:
            table_name = model.__tablename__
            if table_name in tables_data:
                count = len(tables_data[table_name])
                plan["tables"][table_name] = count
                plan["total_records"] += count

        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "message": "リストア計画（実行されていません）",
                "plan": plan,
                "backup_created_at": data.get("created_at"),
            }

        # 実際のリストア
        try:
            restored_counts = {}

            if clear_existing:
                # 逆順で削除（依存関係を考慮）
                for model in reversed(self.TABLES):
                    table_name = model.__tablename__
                    if table_name in tables_data:
                        self.db.query(model).delete()
                self.db.commit()

            # 順番にリストア
            for model in self.TABLES:
                table_name = model.__tablename__
                if table_name not in tables_data:
                    continue

                records = tables_data[table_name]
                restored_count = 0

                for record_data in records:
                    # datetimeフィールドを変換
                    datetime_fields = [
                        "created_at", "updated_at", "expires_at",
                        "period_start", "period_end",
                        "current_period_start", "current_period_end",
                        "canceled_at", "scheduled_at", "published_at",
                        "last_used_at", "sent_at", "clicked_at",
                        "onboarding_started_at", "onboarding_completed_at",
                    ]
                    record_data = self._deserialize_datetime(
                        record_data, datetime_fields
                    )

                    # 既存レコードをスキップ（clear_existingでない場合）
                    if not clear_existing:
                        primary_key = record_data.get("id")
                        if primary_key:
                            existing = self.db.query(model).get(primary_key)
                            if existing:
                                continue

                    # レコード作成
                    obj = model(**record_data)
                    self.db.add(obj)
                    restored_count += 1

                restored_counts[table_name] = restored_count

            self.db.commit()

            return {
                "success": True,
                "dry_run": False,
                "message": "リストアが完了しました",
                "restored_counts": restored_counts,
                "total_restored": sum(restored_counts.values()),
                "clear_existing": clear_existing,
            }

        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": f"リストアに失敗: {str(e)}",
            }

    def get_database_stats(self) -> dict:
        """
        データベース統計を取得

        Returns:
            テーブル別レコード数、総レコード数
        """
        stats = {}
        total = 0

        for model in self.TABLES:
            count = self.db.query(model).count()
            stats[model.__tablename__] = count
            total += count

        return {
            "tables": stats,
            "total_records": total,
        }

    def export_user_data(self, user_id: str) -> dict:
        """
        特定ユーザーのデータをエクスポート（GDPR対応）

        Args:
            user_id: ユーザーID

        Returns:
            ユーザーデータ
        """
        user = self.db.query(User).filter(User.id == user_id).first()

        if not user:
            return {
                "success": False,
                "error": "ユーザーが見つかりません",
            }

        export_data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "user": self._serialize_model(user),
            "analyses": [
                self._serialize_model(a)
                for a in self.db.query(Analysis).filter(
                    Analysis.user_id == user_id
                ).all()
            ],
            "reports": [
                self._serialize_model(r)
                for r in self.db.query(Report).filter(
                    Report.user_id == user_id
                ).all()
            ],
            "scheduled_posts": [
                self._serialize_model(s)
                for s in self.db.query(ScheduledPost).filter(
                    ScheduledPost.user_id == user_id
                ).all()
            ],
            "subscriptions": [
                self._serialize_model(s)
                for s in self.db.query(Subscription).filter(
                    Subscription.user_id == user_id
                ).all()
            ],
            "push_subscriptions": [
                self._serialize_model(p)
                for p in self.db.query(PushSubscription).filter(
                    PushSubscription.user_id == user_id
                ).all()
            ],
        }

        # パスワードハッシュを除外
        if "password_hash" in export_data["user"]:
            del export_data["user"]["password_hash"]

        return {
            "success": True,
            "data": export_data,
        }

    def delete_user_data(
        self,
        user_id: str,
        dry_run: bool = True,
    ) -> dict:
        """
        特定ユーザーのデータを完全削除（GDPR対応、データポータビリティ）

        Args:
            user_id: ユーザーID
            dry_run: Trueの場合、削除せずカウントのみ

        Returns:
            削除結果
        """
        user = self.db.query(User).filter(User.id == user_id).first()

        if not user:
            return {
                "success": False,
                "error": "ユーザーが見つかりません",
            }

        # 削除対象をカウント
        counts = {
            "analyses": self.db.query(Analysis).filter(
                Analysis.user_id == user_id
            ).count(),
            "reports": self.db.query(Report).filter(
                Report.user_id == user_id
            ).count(),
            "scheduled_posts": self.db.query(ScheduledPost).filter(
                ScheduledPost.user_id == user_id
            ).count(),
            "subscriptions": self.db.query(Subscription).filter(
                Subscription.user_id == user_id
            ).count(),
            "tokens": self.db.query(Token).filter(
                Token.user_id == user_id
            ).count(),
            "push_subscriptions": self.db.query(PushSubscription).filter(
                PushSubscription.user_id == user_id
            ).count(),
            "push_notification_logs": self.db.query(PushNotificationLog).filter(
                PushNotificationLog.user_id == user_id
            ).count(),
        }

        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "user_email": user.email,
                "will_delete": counts,
                "total_records": sum(counts.values()) + 1,  # +1 for user
            }

        try:
            # cascade deleteにより関連データも削除される
            self.db.delete(user)
            self.db.commit()

            return {
                "success": True,
                "dry_run": False,
                "message": "ユーザーデータを完全に削除しました",
                "deleted": counts,
                "total_deleted": sum(counts.values()) + 1,
            }
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": f"削除に失敗: {str(e)}",
            }
