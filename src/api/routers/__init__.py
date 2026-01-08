"""
APIルーター
"""

from .analysis import router as analysis_router
from .auth import router as auth_router
from .billing import router as billing_router
from .cross_platform import router as cross_platform_router
from .health import router as health_router
from .instagram_analysis import router as instagram_analysis_router
from .reports import router as report_router
from .tiktok_analysis import router as tiktok_analysis_router
from .users import router as user_router

__all__ = [
    "health_router",
    "auth_router",
    "analysis_router",
    "instagram_analysis_router",
    "tiktok_analysis_router",
    "cross_platform_router",
    "report_router",
    "user_router",
    "billing_router",
]
