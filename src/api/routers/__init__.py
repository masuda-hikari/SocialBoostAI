"""
APIルーター
"""

from .analysis import router as analysis_router
from .auth import router as auth_router
from .health import router as health_router
from .reports import router as report_router
from .users import router as user_router

__all__ = [
    "health_router",
    "auth_router",
    "analysis_router",
    "report_router",
    "user_router",
]
