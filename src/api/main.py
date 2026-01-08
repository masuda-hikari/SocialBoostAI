"""
FastAPI メインアプリケーション
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import routers


def create_app() -> FastAPI:
    """FastAPIアプリケーション生成"""
    app = FastAPI(
        title="SocialBoostAI API",
        description="AI駆動のソーシャルメディア成長アシスタント",
        version="0.5.0",
        docs_url="/docs",
        redoc_url="/redoc",
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
        routers.report_router, prefix="/api/v1/reports", tags=["レポート"]
    )
    app.include_router(routers.user_router, prefix="/api/v1/users", tags=["ユーザー"])

    return app


app = create_app()
