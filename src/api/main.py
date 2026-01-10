"""
FastAPI メインアプリケーション
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import routers
from .db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理"""
    # 起動時: データベース初期化
    init_db()
    yield
    # シャットダウン時: クリーンアップ処理（必要に応じて）


def create_app() -> FastAPI:
    """FastAPIアプリケーション生成"""
    app = FastAPI(
        title="SocialBoostAI API",
        description="AI駆動のソーシャルメディア成長アシスタント",
        version="1.6.0",  # AIコンテンツ生成強化
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

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

    return app


app = create_app()
