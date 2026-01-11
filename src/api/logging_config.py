"""
構造化ログ設定

JSON形式の構造化ログを提供し、運用監視を強化する。
"""

import json
import logging
import os
import sys
import traceback
from datetime import datetime, timezone
from typing import Any, Optional


class StructuredFormatter(logging.Formatter):
    """
    構造化ログフォーマッター（JSON形式）

    本番環境ではJSON形式、開発環境では読みやすいテキスト形式を出力。
    """

    def __init__(self, json_format: Optional[bool] = None):
        """
        初期化

        Args:
            json_format: JSON形式で出力するか（None時は環境変数参照）
        """
        super().__init__()
        if json_format is not None:
            self.json_format = json_format
        else:
            env = os.getenv("ENVIRONMENT", "development")
            log_format = os.getenv("LOG_FORMAT", "auto")
            if log_format == "json":
                self.json_format = True
            elif log_format == "text":
                self.json_format = False
            else:
                # auto: 本番はJSON、開発はテキスト
                self.json_format = env == "production"

    def format(self, record: logging.LogRecord) -> str:
        """
        ログレコードをフォーマット

        Args:
            record: ログレコード

        Returns:
            フォーマット済み文字列
        """
        log_data = self._build_log_data(record)

        if self.json_format:
            return json.dumps(log_data, ensure_ascii=False, default=str)
        else:
            return self._format_text(log_data)

    def _build_log_data(self, record: logging.LogRecord) -> dict[str, Any]:
        """
        ログデータ構築

        Args:
            record: ログレコード

        Returns:
            ログデータ辞書
        """
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # プロセス/スレッド情報
        log_data["process_id"] = record.process
        log_data["thread_id"] = record.thread

        # 例外情報
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info) if record.exc_info[2] else None,
            }

        # 追加コンテキスト（extra属性）
        extra_fields = {
            k: v for k, v in record.__dict__.items()
            if k not in (
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "exc_info", "exc_text", "thread", "threadName",
                "message", "asctime",
            )
        }
        if extra_fields:
            log_data["context"] = extra_fields

        return log_data

    def _format_text(self, log_data: dict[str, Any]) -> str:
        """
        テキスト形式でフォーマット（開発用）

        Args:
            log_data: ログデータ

        Returns:
            テキスト形式の文字列
        """
        timestamp = log_data["timestamp"][:19].replace("T", " ")
        level = log_data["level"]
        logger = log_data["logger"]
        message = log_data["message"]
        module = log_data["module"]
        line = log_data["line"]

        text = f"[{timestamp}] {level:8s} {logger} ({module}:{line}) - {message}"

        if "exception" in log_data:
            exc = log_data["exception"]
            text += f"\n  Exception: {exc['type']}: {exc['message']}"
            if exc.get("traceback"):
                text += "\n  " + "\n  ".join(exc["traceback"])

        if "context" in log_data:
            text += f"\n  Context: {log_data['context']}"

        return text


class RequestContextFilter(logging.Filter):
    """
    リクエストコンテキストフィルター

    リクエストIDなどのコンテキスト情報をログに付与。
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        フィルター処理

        Args:
            record: ログレコード

        Returns:
            常にTrue（全レコード通過）
        """
        # request_idがない場合はデフォルト値を設定
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        if not hasattr(record, "user_id"):
            record.user_id = "-"
        return True


def setup_logging(
    level: Optional[str] = None,
    json_format: Optional[bool] = None,
) -> None:
    """
    ログ設定をセットアップ

    Args:
        level: ログレベル（DEBUG/INFO/WARNING/ERROR/CRITICAL）
        json_format: JSON形式で出力するか
    """
    # ログレベル決定
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO")

    log_level = getattr(logging, level.upper(), logging.INFO)

    # ルートロガー設定
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 既存のハンドラをクリア
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # コンソールハンドラ追加
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(StructuredFormatter(json_format))
    console_handler.addFilter(RequestContextFilter())
    root_logger.addHandler(console_handler)

    # uvicornとfastapiのログレベルも調整
    logging.getLogger("uvicorn").setLevel(log_level)
    logging.getLogger("uvicorn.error").setLevel(log_level)
    logging.getLogger("uvicorn.access").setLevel(log_level)
    logging.getLogger("fastapi").setLevel(log_level)

    # SQLAlchemyは警告以上のみ
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    名前付きロガーを取得

    Args:
        name: ロガー名

    Returns:
        ロガー
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """
    コンテキスト付きロガーアダプター

    リクエストIDやユーザーIDなどのコンテキストを自動付与。
    """

    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        """
        ログメッセージを処理

        Args:
            msg: メッセージ
            kwargs: キーワード引数

        Returns:
            処理済みメッセージとkwargs
        """
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs


def get_request_logger(
    name: str,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> LoggerAdapter:
    """
    リクエストコンテキスト付きロガーを取得

    Args:
        name: ロガー名
        request_id: リクエストID
        user_id: ユーザーID

    Returns:
        コンテキスト付きロガー
    """
    logger = get_logger(name)
    return LoggerAdapter(logger, {
        "request_id": request_id or "-",
        "user_id": user_id or "-",
    })
