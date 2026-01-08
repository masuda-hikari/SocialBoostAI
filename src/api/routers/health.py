"""
ヘルスチェックエンドポイント
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """ヘルスチェックレスポンス"""

    status: str
    version: str
    service: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """サービスヘルスチェック"""
    return HealthResponse(
        status="healthy",
        version="0.5.0",
        service="SocialBoostAI",
    )


@router.get("/")
async def root() -> dict:
    """ルートエンドポイント"""
    return {
        "message": "SocialBoostAI API",
        "docs": "/docs",
        "redoc": "/redoc",
    }
