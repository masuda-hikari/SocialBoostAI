"""
FastAPI メインアプリケーション
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import routers
from .db import init_db
from .logging_config import get_logger, setup_logging
from .middleware import (
    CacheMiddleware,
    CSRFMiddleware,
    PerformanceMiddleware,
    RateLimitMiddleware,
)
from .tasks import get_task_service

# ログ設定初期化
setup_logging()
logger = get_logger(__name__)


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
        version="2.9.0",  # PWA対応追加
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CSRF保護ミドルウェア（状態変更リクエスト保護）
    csrf_enabled = os.getenv("CSRF_ENABLED", "true").lower() in ("true", "1", "yes")
    if csrf_enabled:
        app.add_middleware(CSRFMiddleware)
        logger.info("CSRF保護ミドルウェア有効化")

    # レート制限ミドルウェア（DDoS/API濫用防止）
    app.add_middleware(RateLimitMiddleware)
    logger.info("レート制限ミドルウェア有効化")

    # パフォーマンスモニタリングミドルウェア
    app.add_middleware(PerformanceMiddleware)

    # キャッシュミドルウェア（Redis利用可能時のみ有効）
    if os.getenv("REDIS_URL"):
        app.add_middleware(CacheMiddleware)
        logger.info("Redisキャッシュミドルウェア有効化")

    # CORS設定
    # 本番環境では ALLOWED_ORIGINS 環境変数で制限する
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
    if allowed_origins == "*":
        # 開発環境: 全オリジン許可
        origins = ["*"]
    else:
        # 本番環境: 指定オリジンのみ許可
        origins = [origin.strip() for origin in allowed_origins.split(",")]
        logger.info(f"CORS許可オリジン: {origins}")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
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
    app.include_router(
        routers.email_router, prefix="/api/v1/email", tags=["メール通知"]
    )
    app.include_router(
        routers.schedule_router, prefix="/api/v1/schedule", tags=["スケジュール投稿"]
    )
    app.include_router(
        routers.admin_router, prefix="/api/v1", tags=["管理者"]
    )
    app.include_router(
        routers.onboarding_router, prefix="/api/v1/onboarding", tags=["オンボーディング"]
    )

    return app


app = create_app()
