"""
構造化ログ設定テスト
"""

import json
import logging

import pytest

from src.api.logging_config import (
    LoggerAdapter,
    RequestContextFilter,
    StructuredFormatter,
    get_logger,
    get_request_logger,
)


class TestStructuredFormatter:
    """構造化ログフォーマッターテスト"""

    def test_json_format(self):
        """JSON形式でフォーマットされる"""
        formatter = StructuredFormatter(json_format=True)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="テストメッセージ",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)

        assert data["level"] == "INFO"
        assert data["message"] == "テストメッセージ"
        assert data["logger"] == "test"
        assert data["line"] == 10
        assert "timestamp" in data

    def test_text_format(self):
        """テキスト形式でフォーマットされる"""
        formatter = StructuredFormatter(json_format=False)
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=20,
            msg="警告メッセージ",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)

        assert "WARNING" in output
        assert "警告メッセージ" in output
        assert "test" in output

    def test_exception_logging_json(self):
        """例外情報がJSON形式で含まれる"""
        formatter = StructuredFormatter(json_format=True)

        try:
            raise ValueError("テストエラー")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=30,
            msg="エラー発生",
            args=(),
            exc_info=exc_info,
        )
        output = formatter.format(record)
        data = json.loads(output)

        assert "exception" in data
        assert data["exception"]["type"] == "ValueError"
        assert "テストエラー" in data["exception"]["message"]

    def test_extra_fields_in_context(self):
        """追加フィールドがcontextに含まれる"""
        formatter = StructuredFormatter(json_format=True)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=40,
            msg="追加情報付き",
            args=(),
            exc_info=None,
        )
        record.request_id = "req-123"
        record.user_id = "user-456"

        output = formatter.format(record)
        data = json.loads(output)

        assert "context" in data
        assert data["context"]["request_id"] == "req-123"
        assert data["context"]["user_id"] == "user-456"


class TestRequestContextFilter:
    """リクエストコンテキストフィルターテスト"""

    def test_filter_adds_defaults(self):
        """デフォルト値が追加される"""
        filter = RequestContextFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=50,
            msg="テスト",
            args=(),
            exc_info=None,
        )
        result = filter.filter(record)

        assert result is True
        assert record.request_id == "-"
        assert record.user_id == "-"

    def test_filter_preserves_existing_values(self):
        """既存の値は保持される"""
        filter = RequestContextFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=60,
            msg="テスト",
            args=(),
            exc_info=None,
        )
        record.request_id = "existing-id"
        record.user_id = "existing-user"

        result = filter.filter(record)

        assert result is True
        assert record.request_id == "existing-id"
        assert record.user_id == "existing-user"


class TestGetLogger:
    """ロガー取得テスト"""

    def test_get_logger_returns_logger(self):
        """ロガーが取得できる"""
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"

    def test_get_logger_same_instance(self):
        """同じ名前で同じインスタンスが返る"""
        logger1 = get_logger("test.same")
        logger2 = get_logger("test.same")
        assert logger1 is logger2


class TestGetRequestLogger:
    """リクエストロガー取得テスト"""

    def test_get_request_logger_with_context(self):
        """コンテキスト付きロガーが取得できる"""
        logger = get_request_logger(
            "test.request",
            request_id="req-789",
            user_id="user-012"
        )
        assert isinstance(logger, LoggerAdapter)
        assert logger.extra["request_id"] == "req-789"
        assert logger.extra["user_id"] == "user-012"

    def test_get_request_logger_default_values(self):
        """デフォルト値でロガーが取得できる"""
        logger = get_request_logger("test.default")
        assert logger.extra["request_id"] == "-"
        assert logger.extra["user_id"] == "-"


class TestLoggerAdapter:
    """ロガーアダプターテスト"""

    def test_adapter_adds_extra(self):
        """追加情報がextraに含まれる"""
        base_logger = get_logger("test.adapter")
        adapter = LoggerAdapter(base_logger, {"custom_field": "custom_value"})

        # processメソッドをテスト
        msg, kwargs = adapter.process("テスト", {})
        assert kwargs["extra"]["custom_field"] == "custom_value"

    def test_adapter_merges_extra(self):
        """既存のextraとマージされる"""
        base_logger = get_logger("test.merge")
        adapter = LoggerAdapter(base_logger, {"field1": "value1"})

        msg, kwargs = adapter.process("テスト", {"extra": {"field2": "value2"}})
        assert kwargs["extra"]["field1"] == "value1"
        assert kwargs["extra"]["field2"] == "value2"
