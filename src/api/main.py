"""
FastAPI メインアプリケーション
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import routers
from .db import init_db
from .middleware import CacheMiddleware, PerformanceMiddleware
from .tasks import get_task_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理"""
    # 起動時: データベース初期化
    init_db()
    logger.info("SocialBoostAI API起動完了")
    yield
    # シャットダウン時: バックグラウンドタスクサービス停止
    task_service = get_task_service()
    task_service.shutdown(wait=True)
    logger.info("SocialBoostAI APIシャットダウン完了")


def create_app() -> FastAPI:
    """FastAPIアプリケーション生成"""
    app = FastAPI(
        title="SocialBoostAI API",
        description="AI駆動のソーシャルメディア成長アシスタント",
        version="1.8.0",  # WebSocket通知・リアルタイムダッシュボード
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # パフォーマンスモニタリングミドルウェア
    app.add_middleware(PerformanceMiddleware)

    # キャッシュミドルウェア（Redis利用可能時のみ有効）
    if os.getenv("REDIS_URL"):
        app.add_middleware(CacheMiddleware)
        logger.info("Redisキャッシュミドルウェア有効化")

    # CORS設定
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 本番環境では制限する
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ルーター登録
    app.include_router(routers.health_router, tags=["ヘルスチェック"])
    app.include_router(routers.auth_router, prefix="/api/v1/auth", tags=["認証"])
    app.include_router(
        routers.analysis_router, prefix="/api/v1/analysis", tags=["分析"]
    )
    app.include_router(
        routers.instagram_analysis_router,
        prefix="/api/v1/instagram/analysis",
        tags=["Instagram分析"],
    )
    app.include_router(
        routers.tiktok_analysis_router,
        prefix="/api/v1/tiktok/analysis",
        tags=["TikTok分析"],
    )
    app.include_router(
        routers.youtube_analysis_router,
        prefix="/api/v1/youtube/analysis",
        tags=["YouTube分析"],
    )
    app.include_router(
        routers.linkedin_analysis_router,
        prefix="/api/v1/linkedin/analysis",
        tags=["LinkedIn分析"],
    )
    app.include_router(
        routers.cross_platform_router,
        prefix="/api/v1/cross-platform",
        tags=["クロスプラットフォーム比較"],
    )
    app.include_router(
        routers.content_generation_router,
        prefix="/api/v1/content",
        tags=["AIコンテンツ生成"],
    )
    app.include_router(
        routers.report_router, prefix="/api/v1/reports", tags=["レポート"]
    )
    app.include_router(routers.user_router, prefix="/api/v1/users", tags=["ユーザー"])
    app.include_router(
        routers.billing_router, prefix="/api/v1", tags=["課金"]
    )
    app.include_router(
        routers.websocket_router, tags=["WebSocket"]
    )
    app.include_router(
        routers.realtime_router, prefix="/api/v1/realtime", tags=["リアルタイム"]
    )

    return app


app = create_app()
