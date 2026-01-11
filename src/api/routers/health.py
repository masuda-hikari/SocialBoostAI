"""
ヘルスチェックエンドポイント

サービス、データベース、Redis、ディスクの状態を確認。
"""

import logging
import os
import shutil
import time
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


class ComponentHealth(BaseModel):
    """コンポーネント健全性"""
    status: str  # "healthy", "degraded", "unhealthy"
    message: Optional[str] = None
    latency_ms: Optional[float] = None


class HealthResponse(BaseModel):
    """ヘルスチェックレスポンス"""
    status: str
    version: str
    service: str
    timestamp: str
    uptime_seconds: Optional[float] = None
    components: Optional[dict[str, ComponentHealth]] = None


class DetailedHealthResponse(HealthResponse):
    """詳細ヘルスチェックレスポンス"""
    environment: Optional[str] = None
    disk: Optional[dict[str, Any]] = None
    memory: Optional[dict[str, Any]] = None


# アプリケーション起動時刻
_startup_time: Optional[float] = None


def get_startup_time() -> float:
    """起動時刻を取得（初回呼び出し時に記録）"""
    global _startup_time
    if _startup_time is None:
        _startup_time = time.time()
    return _startup_time


def check_database_health(db: Session) -> ComponentHealth:
    """
    データベース健全性チェック

    Args:
        db: データベースセッション

    Returns:
        データベース健全性
    """
    start = time.time()
    try:
        db.execute(text("SELECT 1"))
        latency = (time.time() - start) * 1000

        if latency > 1000:  # 1秒以上は劣化
            return ComponentHealth(
                status="degraded",
                message=f"レスポンス遅延: {latency:.0f}ms",
                latency_ms=latency
            )

        return ComponentHealth(
            status="healthy",
            message="正常",
            latency_ms=latency
        )
    except Exception as e:
        logger.error(f"データベースヘルスチェック失敗: {e}")
        return ComponentHealth(
            status="unhealthy",
            message=str(e),
            latency_ms=(time.time() - start) * 1000
        )


def check_redis_health() -> ComponentHealth:
    """
    Redis健全性チェック

    Returns:
        Redis健全性
    """
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        return ComponentHealth(
            status="healthy",
            message="Redis未設定（キャッシュ無効）"
        )

    start = time.time()
    try:
        import redis
        client = redis.from_url(redis_url, socket_timeout=2)
        client.ping()
        latency = (time.time() - start) * 1000

        if latency > 100:  # 100ms以上は劣化
            return ComponentHealth(
                status="degraded",
                message=f"レスポンス遅延: {latency:.0f}ms",
                latency_ms=latency
            )

        return ComponentHealth(
            status="healthy",
            message="正常",
            latency_ms=latency
        )
    except ImportError:
        return ComponentHealth(
            status="healthy",
            message="redisライブラリ未インストール"
        )
    except Exception as e:
        logger.error(f"Redisヘルスチェック失敗: {e}")
        return ComponentHealth(
            status="unhealthy",
            message=str(e),
            latency_ms=(time.time() - start) * 1000
        )


def check_disk_health() -> tuple[ComponentHealth, dict[str, Any]]:
    """
    ディスク健全性チェック

    Returns:
        ディスク健全性とディスク情報
    """
    try:
        usage = shutil.disk_usage("/")
        total_gb = usage.total / (1024 ** 3)
        used_gb = usage.used / (1024 ** 3)
        free_gb = usage.free / (1024 ** 3)
        percent = (usage.used / usage.total) * 100

        disk_info = {
            "total_gb": round(total_gb, 2),
            "used_gb": round(used_gb, 2),
            "free_gb": round(free_gb, 2),
            "percent_used": round(percent, 1)
        }

        if percent > 95:
            return ComponentHealth(
                status="unhealthy",
                message=f"ディスク残量危険: {percent:.1f}%使用中"
            ), disk_info
        elif percent > 85:
            return ComponentHealth(
                status="degraded",
                message=f"ディスク残量警告: {percent:.1f}%使用中"
            ), disk_info
        else:
            return ComponentHealth(
                status="healthy",
                message=f"正常: {percent:.1f}%使用中"
            ), disk_info
    except Exception as e:
        logger.error(f"ディスクヘルスチェック失敗: {e}")
        return ComponentHealth(
            status="unhealthy",
            message=str(e)
        ), {}


def get_overall_status(components: dict[str, ComponentHealth]) -> str:
    """
    全体ステータス判定

    Args:
        components: コンポーネント健全性辞書

    Returns:
        全体ステータス
    """
    statuses = [c.status for c in components.values()]

    if any(s == "unhealthy" for s in statuses):
        return "unhealthy"
    elif any(s == "degraded" for s in statuses):
        return "degraded"
    else:
        return "healthy"


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    基本ヘルスチェック

    軽量なヘルスチェック。ロードバランサーやコンテナオーケストレーター向け。
    """
    get_startup_time()  # 初回呼び出し時に記録
    return HealthResponse(
        status="healthy",
        version="2.6.0",
        service="SocialBoostAI",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check(
    db: Session = Depends(get_db)
) -> DetailedHealthResponse:
    """
    詳細ヘルスチェック

    データベース、Redis、ディスクの状態を含む詳細なヘルスチェック。
    監視システムやダッシュボード向け。
    """
    startup = get_startup_time()
    uptime = time.time() - startup

    # 各コンポーネントのヘルスチェック
    components = {}
    components["database"] = check_database_health(db)
    components["redis"] = check_redis_health()
    disk_health, disk_info = check_disk_health()
    components["disk"] = disk_health

    # 全体ステータス
    overall_status = get_overall_status(components)

    return DetailedHealthResponse(
        status=overall_status,
        version="2.6.0",
        service="SocialBoostAI",
        timestamp=datetime.now(timezone.utc).isoformat(),
        uptime_seconds=round(uptime, 2),
        components=components,
        environment=os.getenv("ENVIRONMENT", "development"),
        disk=disk_info if disk_info else None,
    )


@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)) -> dict:
    """
    Readiness Probe

    Kubernetes readiness probe向け。
    サービスがリクエストを受け付け可能かチェック。
    """
    db_health = check_database_health(db)

    if db_health.status == "unhealthy":
        # データベース異常時は503を返す
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable"
        )

    return {"status": "ready"}


@router.get("/health/live")
async def liveness_check() -> dict:
    """
    Liveness Probe

    Kubernetes liveness probe向け。
    プロセスが生きているかの最小チェック。
    """
    return {"status": "alive"}


@router.get("/")
async def root() -> dict:
    """ルートエンドポイント"""
    return {
        "message": "SocialBoostAI API",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "health_detailed": "/health/detailed",
    }
