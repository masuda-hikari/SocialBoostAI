# -*- coding: utf-8 -*-
"""
週次/月次サマリーレポート生成のテスト

v0.4: レポート機能拡張
"""

import os
import tempfile
from datetime import datetime

import pytest

from src.models import (
    EngagementMetrics,
    MonthlySummary,
    PeriodComparison,
    Tweet,
    WeeklySummary,
)
from src.report import (
    generate_monthly_console_report,
    generate_monthly_summary_report,
    generate_weekly_console_report,
    generate_weekly_summary_report,
)


# テストデータ生成用ヘルパー
def create_test_weekly_summary() -> WeeklySummary:
    """テスト用週次サマリーを生成"""
    return WeeklySummary(
        week_number=2,
        year=2026,
        period_start=datetime(2026, 1, 5),
        period_end=datetime(2026, 1, 11),
        total_posts=10,
        metrics=EngagementMetrics(
            total_likes=500,
            total_retweets=200,
            total_replies=50,
            avg_likes_per_post=50.0,
            avg_retweets_per_post=20.0,
        ),
        best_performing_day="水曜日",
        top_post=Tweet(
            id="1",
            text="これがトップ投稿です！素晴らしいコンテンツ",
            created_at=datetime(2026, 1, 7, 10, 0),
            likes=150,
            retweets=80,
            replies=20,
        ),
        comparison=[
            PeriodComparison(
                metric_name="総いいね数",
                current_value=500,
                previous_value=400,
                change_percent=25.0,
                trend="up",
            ),
            PeriodComparison(
                metric_name="総リツイート数",
                current_value=200,
                previous_value=250,
                change_percent=-20.0,
                trend="down",
            ),
        ],
        insights=[
            "今週は10件の投稿を達成しました。",
            "水曜日が最もエンゲージメントの高い日でした。",
            "いいね数が前週比25.0%増加しました！",
        ],
    )


def create_test_monthly_summary() -> MonthlySummary:
    """テスト用月次サマリーを生成"""
    weekly_summaries = [
        WeeklySummary(
            week_number=1,
            year=2026,
            period_start=datetime(2025, 12, 29),
            period_end=datetime(2026, 1, 4),
            total_posts=5,
            metrics=EngagementMetrics(total_likes=200),
            best_performing_day="火曜日",
        ),
        WeeklySummary(
            week_number=2,
            year=2026,
            period_start=datetime(2026, 1, 5),
            period_end=datetime(2026, 1, 11),
            total_posts=8,
            metrics=EngagementMetrics(total_likes=400),
            best_performing_day="水曜日",
        ),
    ]

    return MonthlySummary(
        month=1,
        year=2026,
        period_start=datetime(2026, 1, 1),
        period_end=datetime(2026, 1, 31),
        total_posts=25,
        metrics=EngagementMetrics(
            total_likes=1200,
            total_retweets=500,
            total_replies=150,
            engagement_rate=3.5,
            avg_likes_per_post=48.0,
            avg_retweets_per_post=20.0,
        ),
        weekly_summaries=weekly_summaries,
        best_performing_week=2,
        top_posts=[
            Tweet(
                id="1",
                text="トップ投稿1 - これが最も人気の投稿です",
                created_at=datetime(2026, 1, 10, 10, 0),
                likes=200,
                retweets=100,
                replies=30,
            ),
            Tweet(
                id="2",
                text="トップ投稿2 - 2番目に人気の投稿",
                created_at=datetime(2026, 1, 15, 10, 0),
                likes=150,
                retweets=80,
                replies=25,
            ),
        ],
        comparison=[
            PeriodComparison(
                metric_name="総いいね数",
                current_value=1200,
                previous_value=900,
                change_percent=33.3,
                trend="up",
            ),
        ],
        insights=[
            "今月の投稿数は25件（週平均6.3件）でした。",
            "第2週が最もパフォーマンスが良好でした。",
            "前月比33.3%の成長を達成しました！",
        ],
        growth_rate=33.3,
    )


class TestGenerateWeeklySummaryReport:
    """週次サマリーHTMLレポート生成のテスト"""

    def test_generates_html_file(self):
        """HTMLファイルが生成されること"""
        summary = create_test_weekly_summary()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "weekly_test.html")
            result = generate_weekly_summary_report(summary, "testuser", output_path)

            assert os.path.exists(result)
            assert result.endswith(".html")

    def test_html_contains_required_content(self):
        """HTMLに必要なコンテンツが含まれること"""
        summary = create_test_weekly_summary()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "weekly_test.html")
            generate_weekly_summary_report(summary, "testuser", output_path)

            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()

            assert "testuser" in content
            assert "第2週" in content
            assert "500" in content  # total_likes
            assert "水曜日" in content  # best_performing_day

    def test_default_output_path(self):
        """デフォルト出力パスの場合"""
        summary = create_test_weekly_summary()

        # 環境変数を設定してテスト
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["REPORTS_DIR"] = tmpdir
            try:
                result = generate_weekly_summary_report(summary, "testuser")
                assert os.path.exists(result)
                assert "weekly_testuser" in result
            finally:
                del os.environ["REPORTS_DIR"]


class TestGenerateMonthlySummaryReport:
    """月次サマリーHTMLレポート生成のテスト"""

    def test_generates_html_file(self):
        """HTMLファイルが生成されること"""
        summary = create_test_monthly_summary()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "monthly_test.html")
            result = generate_monthly_summary_report(summary, "testuser", output_path)

            assert os.path.exists(result)
            assert result.endswith(".html")

    def test_html_contains_required_content(self):
        """HTMLに必要なコンテンツが含まれること"""
        summary = create_test_monthly_summary()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "monthly_test.html")
            generate_monthly_summary_report(summary, "testuser", output_path)

            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()

            assert "testuser" in content
            assert "2026年1月" in content
            assert "1200" in content  # total_likes
            assert "33.3" in content  # growth_rate
            assert "週別サマリー" in content


class TestGenerateWeeklyConsoleReport:
    """週次サマリーコンソールレポート生成のテスト"""

    def test_generates_text(self):
        """テキストが生成されること"""
        summary = create_test_weekly_summary()
        result = generate_weekly_console_report(summary, "testuser")

        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_required_sections(self):
        """必要なセクションが含まれること"""
        summary = create_test_weekly_summary()
        result = generate_weekly_console_report(summary, "testuser")

        assert "週次サマリー" in result
        assert "@testuser" in result
        assert "週間メトリクス" in result
        assert "投稿数: 10" in result
        assert "総いいね: 500" in result
        assert "ベストパフォーマンス日" in result
        assert "水曜日" in result

    def test_includes_comparison(self):
        """比較データが含まれること"""
        summary = create_test_weekly_summary()
        result = generate_weekly_console_report(summary, "testuser")

        assert "前週との比較" in result
        assert "↑" in result  # up trend
        assert "↓" in result  # down trend

    def test_includes_insights(self):
        """インサイトが含まれること"""
        summary = create_test_weekly_summary()
        result = generate_weekly_console_report(summary, "testuser")

        assert "インサイト" in result


class TestGenerateMonthlyConsoleReport:
    """月次サマリーコンソールレポート生成のテスト"""

    def test_generates_text(self):
        """テキストが生成されること"""
        summary = create_test_monthly_summary()
        result = generate_monthly_console_report(summary, "testuser")

        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_required_sections(self):
        """必要なセクションが含まれること"""
        summary = create_test_monthly_summary()
        result = generate_monthly_console_report(summary, "testuser")

        assert "月次サマリー" in result
        assert "@testuser" in result
        assert "2026年1月" in result
        assert "月間メトリクス" in result
        assert "投稿数: 25" in result
        assert "エンゲージメント率: 3.5%" in result

    def test_includes_growth_rate(self):
        """成長率が含まれること"""
        summary = create_test_monthly_summary()
        result = generate_monthly_console_report(summary, "testuser")

        assert "成長率" in result
        assert "33.3%" in result

    def test_includes_weekly_summaries(self):
        """週別サマリーが含まれること"""
        summary = create_test_monthly_summary()
        result = generate_monthly_console_report(summary, "testuser")

        assert "週別サマリー" in result

    def test_includes_top_posts(self):
        """トップ投稿が含まれること"""
        summary = create_test_monthly_summary()
        result = generate_monthly_console_report(summary, "testuser")

        assert "トップ投稿" in result


class TestReportWithMinimalData:
    """最小データでのレポート生成テスト"""

    def test_weekly_minimal(self):
        """最小データの週次レポート"""
        summary = WeeklySummary(
            week_number=1,
            year=2026,
            period_start=datetime(2026, 1, 1),
            period_end=datetime(2026, 1, 7),
            total_posts=0,
            metrics=EngagementMetrics(),
            best_performing_day="データなし",
        )

        result = generate_weekly_console_report(summary, "testuser")
        assert "投稿数: 0" in result

    def test_monthly_minimal(self):
        """最小データの月次レポート"""
        summary = MonthlySummary(
            month=1,
            year=2026,
            period_start=datetime(2026, 1, 1),
            period_end=datetime(2026, 1, 31),
            total_posts=0,
            metrics=EngagementMetrics(),
        )

        result = generate_monthly_console_report(summary, "testuser")
        assert "投稿数: 0" in result
