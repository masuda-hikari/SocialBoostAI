"""
メール通知モジュール

メール送信サービスとテンプレート管理を提供する。
"""

from .service import EmailService, get_email_service
from .templates import EmailTemplate, EmailTemplateManager, EmailTemplateType

__all__ = [
    "EmailService",
    "get_email_service",
    "EmailTemplate",
    "EmailTemplateManager",
    "EmailTemplateType",
]
