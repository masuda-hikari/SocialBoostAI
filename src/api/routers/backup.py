"""
データベースバックアップAPIエンドポイント

管理者用のバックアップ管理機能を提供
- バックアップ作成・一覧・詳細・削除
- リストア機能
- ユーザーデータエクスポート（GDPR対応）
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..backup.service import BackupService
from ..db import get_db
from ..dependencies import AdminUser


router = APIRouter(prefix="/backup", tags=["backup"])


# ============================================================
# スキーマ定義
# ============================================================


class CreateBackupRequest(BaseModel):
    """バックアップ作成リクエスト"""

    include_tokens: bool = Field(
        default=False,
        description="認証トークンを含めるか",
    )
    include_logs: bool = Field(
        default=True,
        description="通知ログを含めるか",
    )


class RestoreRequest(BaseModel):
    """リストアリクエスト"""

    filename: str = Field(..., description="リストアするバックアップファイル名")
    dry_run: bool = Field(
        default=True,
        description="Trueの場合、実際にはリストアせずシミュレーションのみ",
    )
    clear_existing: bool = Field(
        default=False,
        description="Trueの場合、既存データを削除してからリストア",
    )


class UserDataExportRequest(BaseModel):
    """ユーザーデータエクスポートリクエスト"""

    user_id: str = Field(..., description="エクスポートするユーザーID")


class UserDataDeleteRequest(BaseModel):
    """ユーザーデータ削除リクエスト"""

    user_id: str = Field(..., description="削除するユーザーID")
    dry_run: bool = Field(
        default=True,
        description="Trueの場合、削除せずカウントのみ",
    )


# ============================================================
# バックアップ管理API
# ============================================================


@router.post("/create")
async def create_backup(
    request: CreateBackupRequest,
    admin: AdminUser,
    db: Annotated[Session, Depends(get_db)],
):
    """
    データベースバックアップを作成

    管理者のみアクセス可能
    """
    service = BackupService(db)
    result = service.create_backup(
        include_tokens=request.include_tokens,
        include_logs=request.include_logs,
    )

    return result


@router.get("/list")
async def list_backups(
    admin: AdminUser,
    db: Annotated[Session, Depends(get_db)],
):
    """
    バックアップファイル一覧を取得

    管理者のみアクセス可能
    """
    service = BackupService(db)
    backups = service.list_backups()

    return {
        "backups": backups,
        "total": len(backups),
    }


@router.get("/info/{filename}")
async def get_backup_info(
    filename: str,
    admin: AdminUser,
    db: Annotated[Session, Depends(get_db)],
):
    """
    バックアップファイルの詳細情報を取得

    管理者のみアクセス可能
    """
    service = BackupService(db)
    info = service.get_backup_info(filename)

    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="バックアップファイルが見つかりません",
        )

    if "error" in info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=info["error"],
        )

    return info


@router.delete("/{filename}")
async def delete_backup(
    filename: str,
    admin: AdminUser,
    db: Annotated[Session, Depends(get_db)],
):
    """
    バックアップファイルを削除

    管理者のみアクセス可能
    """
    service = BackupService(db)
    result = service.delete_backup(filename)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"],
        )

    return result


@router.post("/cleanup")
async def cleanup_old_backups(
    admin: AdminUser,
    db: Annotated[Session, Depends(get_db)],
):
    """
    古いバックアップを削除

    設定された保持期間を超えたバックアップを削除
    管理者のみアクセス可能
    """
    service = BackupService(db)
    result = service.cleanup_old_backups()

    return result


@router.post("/restore")
async def restore_backup(
    request: RestoreRequest,
    admin: AdminUser,
    db: Annotated[Session, Depends(get_db)],
):
    """
    バックアップからリストア

    注意: clear_existing=Trueの場合、既存データが削除されます
    管理者のみアクセス可能
    """
    service = BackupService(db)
    result = service.restore_backup(
        filename=request.filename,
        dry_run=request.dry_run,
        clear_existing=request.clear_existing,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"],
        )

    return result


@router.get("/stats")
async def get_database_stats(
    admin: AdminUser,
    db: Annotated[Session, Depends(get_db)],
):
    """
    データベース統計を取得

    管理者のみアクセス可能
    """
    service = BackupService(db)
    stats = service.get_database_stats()

    return stats


# ============================================================
# ユーザーデータ管理API（GDPR対応）
# ============================================================


@router.post("/export-user-data")
async def export_user_data(
    request: UserDataExportRequest,
    admin: AdminUser,
    db: Annotated[Session, Depends(get_db)],
):
    """
    特定ユーザーのデータをエクスポート（GDPR対応）

    管理者のみアクセス可能
    """
    service = BackupService(db)
    result = service.export_user_data(request.user_id)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"],
        )

    return result


@router.post("/delete-user-data")
async def delete_user_data(
    request: UserDataDeleteRequest,
    admin: AdminUser,
    db: Annotated[Session, Depends(get_db)],
):
    """
    特定ユーザーのデータを完全削除（GDPR対応）

    注意: dry_run=Falseの場合、データが完全に削除されます
    管理者のみアクセス可能
    """
    service = BackupService(db)
    result = service.delete_user_data(
        user_id=request.user_id,
        dry_run=request.dry_run,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
            if "見つかりません" in result.get("error", "")
            else status.HTTP_400_BAD_REQUEST,
            detail=result["error"],
        )

    return result
