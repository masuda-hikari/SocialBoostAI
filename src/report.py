"""
レポート生成モジュール
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .models import AnalysisResult, MonthlySummary, PeriodComparison, WeeklySummary

logger = logging.getLogger(__name__)

# HTMLテンプレート
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SocialBoostAI レポート - {{ username }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .header h1 {
            margin: 0;
            font-size: 2em;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
        }
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .card h2 {
            color: #667eea;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
            margin-top: 0;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }
        .metric {
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .metric-label {
            color: #666;
            font-size: 0.9em;
        }
        .hourly-chart {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-top: 15px;
        }
        .hour-bar {
            flex: 1;
            min-width: 30px;
            text-align: center;
        }
        .hour-bar .bar {
            background: #667eea;
            border-radius: 4px 4px 0 0;
            margin-bottom: 5px;
        }
        .hour-bar .label {
            font-size: 0.7em;
            color: #666;
        }
        .recommendation-box {
            background: #e8f4f8;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 10px 0;
        }
        .best-hours {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .hour-badge {
            background: #667eea;
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            font-weight: bold;
        }
        .top-post {
            border-left: 3px solid #ccc;
            padding-left: 15px;
            margin: 15px 0;
        }
        .top-post .text {
            font-style: italic;
        }
        .top-post .stats {
            font-size: 0.85em;
            color: #666;
            margin-top: 5px;
        }
        .content-idea {
            background: #f0f7ff;
            padding: 10px 15px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .hashtag {
            display: inline-block;
            background: #e0e7ff;
            color: #4c51bf;
            padding: 5px 10px;
            border-radius: 15px;
            margin: 5px 5px 5px 0;
            font-size: 0.9em;
        }
        .footer {
            text-align: center;
            color: #999;
            margin-top: 30px;
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>SocialBoostAI レポート</h1>
        <p>@{{ username }} | {{ period_start }} - {{ period_end }}</p>
    </div>

    <div class="card">
        <h2>概要</h2>
        <div class="metrics-grid">
            <div class="metric">
                <div class="metric-value">{{ result.total_posts }}</div>
                <div class="metric-label">投稿数</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ result.metrics.total_likes }}</div>
                <div class="metric-label">総いいね数</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ result.metrics.total_retweets }}</div>
                <div class="metric-label">総リツイート数</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ result.metrics.avg_likes_per_post }}</div>
                <div class="metric-label">平均いいね/投稿</div>
            </div>
        </div>
    </div>

    <div class="card">
        <h2>時間帯別エンゲージメント</h2>
        <div class="hourly-chart">
            {% for hour in result.hourly_breakdown %}
            <div class="hour-bar">
                <div class="bar" style="height: {{ (hour.total_engagement / max_engagement * 100) | int }}px;"></div>
                <div class="label">{{ hour.hour }}時</div>
            </div>
            {% endfor %}
        </div>
    </div>

    <div class="card">
        <h2>レコメンデーション</h2>
        {% if result.recommendations %}
        <div class="recommendation-box">
            <h3>最適な投稿時間</h3>
            <div class="best-hours">
                {% for hour in result.recommendations.best_hours %}
                <span class="hour-badge">{{ hour }}:00</span>
                {% endfor %}
            </div>
        </div>
        <p>{{ result.recommendations.reasoning }}</p>

        {% if result.recommendations.suggested_hashtags %}
        <h3>おすすめハッシュタグ</h3>
        <div>
            {% for tag in result.recommendations.suggested_hashtags %}
            <span class="hashtag">#{{ tag }}</span>
            {% endfor %}
        </div>
        {% endif %}

        {% if result.recommendations.content_ideas %}
        <h3>コンテンツアイデア</h3>
        {% for idea in result.recommendations.content_ideas %}
        <div class="content-idea">{{ idea }}</div>
        {% endfor %}
        {% endif %}
        {% endif %}
    </div>

    <div class="card">
        <h2>トップパフォーマンス投稿</h2>
        {% for post in result.top_performing_posts[:5] %}
        <div class="top-post">
            <div class="text">"{{ post.text[:200] }}{% if post.text|length > 200 %}...{% endif %}"</div>
            <div class="stats">
                ❤️ {{ post.likes }} | 🔁 {{ post.retweets }} | 💬 {{ post.replies }} | {{ post.created_at.strftime('%Y-%m-%d %H:%M') }}
            </div>
        </div>
        {% endfor %}
    </div>

    <div class="footer">
        <p>Generated by SocialBoostAI | {{ generated_at }}</p>
    </div>
</body>
</html>
"""


def generate_console_report(
    result: AnalysisResult,
    username: str,
) -> str:
    """コンソール用テキストレポートを生成

    Args:
        result: 分析結果
        username: ユーザー名

    Returns:
        str: レポートテキスト
    """
    lines = [
        "=" * 60,
        f"  SocialBoostAI レポート - @{username}",
        "=" * 60,
        "",
        f"期間: {result.period_start.strftime('%Y-%m-%d')} - {result.period_end.strftime('%Y-%m-%d')}",
        "",
        "【概要】",
        f"  投稿数: {result.total_posts}",
        f"  総いいね: {result.metrics.total_likes}",
        f"  総リツイート: {result.metrics.total_retweets}",
        f"  平均いいね/投稿: {result.metrics.avg_likes_per_post}",
        "",
    ]

    if result.recommendations:
        lines.extend(
            [
                "【レコメンデーション】",
                f"  最適な投稿時間: {', '.join(f'{h}:00' for h in result.recommendations.best_hours)}",
                "",
                f"  {result.recommendations.reasoning}",
                "",
            ]
        )

        if result.recommendations.suggested_hashtags:
            lines.append("  おすすめハッシュタグ:")
            for tag in result.recommendations.suggested_hashtags:
                lines.append(f"    #{tag}")
            lines.append("")

        if result.recommendations.content_ideas:
            lines.append("  コンテンツアイデア:")
            for i, idea in enumerate(result.recommendations.content_ideas, 1):
                lines.append(f"    {i}. {idea[:80]}...")
            lines.append("")

    lines.extend(
        [
            "【トップパフォーマンス投稿】",
        ]
    )

    for i, post in enumerate(result.top_performing_posts[:3], 1):
        text_preview = post.text[:60].replace("\n", " ")
        lines.append(f'  {i}. "{text_preview}..."')
        lines.append(f"     ❤️{post.likes} 🔁{post.retweets} 💬{post.replies}")
        lines.append("")

    lines.extend(
        [
            "=" * 60,
            "Generated by SocialBoostAI",
            "=" * 60,
        ]
    )

    return "\n".join(lines)


def generate_html_report(
    result: AnalysisResult,
    username: str,
    output_path: Optional[str] = None,
) -> str:
    """HTMLレポートを生成

    Args:
        result: 分析結果
        username: ユーザー名
        output_path: 出力パス（指定なしの場合はreports/ディレクトリ）

    Returns:
        str: 生成されたファイルのパス
    """
    from jinja2 import Template

    # 最大エンゲージメントを計算（グラフ表示用）
    max_engagement = max(
        (h.total_engagement for h in result.hourly_breakdown),
        default=1,
    )
    if max_engagement == 0:
        max_engagement = 1

    template = Template(HTML_TEMPLATE)
    html_content = template.render(
        result=result,
        username=username,
        period_start=result.period_start.strftime("%Y-%m-%d"),
        period_end=result.period_end.strftime("%Y-%m-%d"),
        max_engagement=max_engagement,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    # 出力先を決定
    if output_path is None:
        reports_dir = os.getenv("REPORTS_DIR", "./reports")
        Path(reports_dir).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(reports_dir, f"report_{username}_{timestamp}.html")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info(f"HTMLレポートを生成しました: {output_path}")
    return output_path


# 週次サマリーHTMLテンプレート
WEEKLY_SUMMARY_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>週次サマリー - {{ username }} - 第{{ summary.week_number }}週</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .header {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .header h1 { margin: 0; font-size: 1.8em; }
        .header p { margin: 10px 0 0 0; opacity: 0.9; }
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .card h2 {
            color: #4facfe;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
            margin-top: 0;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }
        .metric {
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .metric-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #4facfe;
        }
        .metric-label { color: #666; font-size: 0.85em; }
        .comparison-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            border-bottom: 1px solid #eee;
        }
        .trend-up { color: #28a745; }
        .trend-down { color: #dc3545; }
        .trend-stable { color: #6c757d; }
        .insight-box {
            background: #e8f4f8;
            border-left: 4px solid #4facfe;
            padding: 12px 15px;
            margin: 10px 0;
            border-radius: 0 5px 5px 0;
        }
        .top-post {
            border-left: 3px solid #ccc;
            padding-left: 15px;
            margin: 15px 0;
        }
        .top-post .text { font-style: italic; }
        .top-post .stats { font-size: 0.85em; color: #666; margin-top: 5px; }
        .footer {
            text-align: center;
            color: #999;
            margin-top: 30px;
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>週次サマリー</h1>
        <p>@{{ username }} | {{ summary.year }}年 第{{ summary.week_number }}週</p>
        <p style="font-size: 0.9em;">{{ summary.period_start.strftime('%Y-%m-%d') }} - {{ summary.period_end.strftime('%Y-%m-%d') }}</p>
    </div>

    <div class="card">
        <h2>📊 週間メトリクス</h2>
        <div class="metrics-grid">
            <div class="metric">
                <div class="metric-value">{{ summary.total_posts }}</div>
                <div class="metric-label">投稿数</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ summary.metrics.total_likes }}</div>
                <div class="metric-label">総いいね</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ summary.metrics.total_retweets }}</div>
                <div class="metric-label">総RT</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ summary.metrics.avg_likes_per_post }}</div>
                <div class="metric-label">平均いいね</div>
            </div>
        </div>
    </div>

    {% if summary.comparison %}
    <div class="card">
        <h2>📈 前週との比較</h2>
        {% for comp in summary.comparison %}
        <div class="comparison-item">
            <span>{{ comp.metric_name }}</span>
            <span class="trend-{{ comp.trend }}">
                {% if comp.trend == 'up' %}↑{% elif comp.trend == 'down' %}↓{% else %}→{% endif %}
                {{ comp.change_percent }}%
            </span>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <div class="card">
        <h2>💡 インサイト</h2>
        {% for insight in summary.insights %}
        <div class="insight-box">{{ insight }}</div>
        {% endfor %}
        <p><strong>ベストパフォーマンス日:</strong> {{ summary.best_performing_day }}</p>
    </div>

    {% if summary.top_post %}
    <div class="card">
        <h2>🏆 トップ投稿</h2>
        <div class="top-post">
            <div class="text">"{{ summary.top_post.text[:200] }}{% if summary.top_post.text|length > 200 %}...{% endif %}"</div>
            <div class="stats">
                ❤️ {{ summary.top_post.likes }} | 🔁 {{ summary.top_post.retweets }} | 💬 {{ summary.top_post.replies }}
            </div>
        </div>
    </div>
    {% endif %}

    <div class="footer">
        <p>Generated by SocialBoostAI | {{ generated_at }}</p>
    </div>
</body>
</html>
"""

# 月次サマリーHTMLテンプレート
MONTHLY_SUMMARY_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>月次サマリー - {{ username }} - {{ summary.year }}年{{ summary.month }}月</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .header h1 { margin: 0; font-size: 2em; }
        .header p { margin: 10px 0 0 0; opacity: 0.9; }
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .card h2 {
            color: #667eea;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
            margin-top: 0;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
        }
        .metric {
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .metric-label { color: #666; font-size: 0.9em; }
        .growth-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            margin-top: 10px;
        }
        .growth-positive { background: #d4edda; color: #155724; }
        .growth-negative { background: #f8d7da; color: #721c24; }
        .growth-neutral { background: #e2e3e5; color: #383d41; }
        .comparison-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px;
            border-bottom: 1px solid #eee;
        }
        .trend-up { color: #28a745; }
        .trend-down { color: #dc3545; }
        .trend-stable { color: #6c757d; }
        .insight-box {
            background: #e8f4f8;
            border-left: 4px solid #667eea;
            padding: 12px 15px;
            margin: 10px 0;
            border-radius: 0 5px 5px 0;
        }
        .weekly-summary {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
        .weekly-summary h4 { margin: 0 0 10px 0; color: #667eea; }
        .weekly-stats { font-size: 0.9em; color: #666; }
        .top-post {
            border-left: 3px solid #ccc;
            padding-left: 15px;
            margin: 15px 0;
        }
        .top-post .text { font-style: italic; }
        .top-post .stats { font-size: 0.85em; color: #666; margin-top: 5px; }
        .footer {
            text-align: center;
            color: #999;
            margin-top: 30px;
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>月次サマリー</h1>
        <p>@{{ username }} | {{ summary.year }}年{{ summary.month }}月</p>
        {% if summary.growth_rate is not none %}
        <span class="growth-badge {% if summary.growth_rate > 0 %}growth-positive{% elif summary.growth_rate < 0 %}growth-negative{% else %}growth-neutral{% endif %}">
            {% if summary.growth_rate > 0 %}↑{% elif summary.growth_rate < 0 %}↓{% else %}→{% endif %}
            {{ summary.growth_rate }}% 前月比
        </span>
        {% endif %}
    </div>

    <div class="card">
        <h2>📊 月間メトリクス</h2>
        <div class="metrics-grid">
            <div class="metric">
                <div class="metric-value">{{ summary.total_posts }}</div>
                <div class="metric-label">投稿数</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ summary.metrics.total_likes }}</div>
                <div class="metric-label">総いいね</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ summary.metrics.total_retweets }}</div>
                <div class="metric-label">総RT</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ summary.metrics.avg_likes_per_post }}</div>
                <div class="metric-label">平均いいね/投稿</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ summary.metrics.engagement_rate }}%</div>
                <div class="metric-label">エンゲージメント率</div>
            </div>
        </div>
    </div>

    {% if summary.comparison %}
    <div class="card">
        <h2>📈 前月との比較</h2>
        {% for comp in summary.comparison %}
        <div class="comparison-item">
            <span>{{ comp.metric_name }}</span>
            <span>{{ comp.current_value }} / {{ comp.previous_value }}</span>
            <span class="trend-{{ comp.trend }}">
                {% if comp.trend == 'up' %}↑{% elif comp.trend == 'down' %}↓{% else %}→{% endif %}
                {{ comp.change_percent }}%
            </span>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <div class="card">
        <h2>💡 インサイト</h2>
        {% for insight in summary.insights %}
        <div class="insight-box">{{ insight }}</div>
        {% endfor %}
        {% if summary.best_performing_week %}
        <p><strong>ベストパフォーマンス週:</strong> 第{{ summary.best_performing_week }}週</p>
        {% endif %}
    </div>

    {% if summary.weekly_summaries %}
    <div class="card">
        <h2>📅 週別サマリー</h2>
        {% for week in summary.weekly_summaries %}
        <div class="weekly-summary">
            <h4>第{{ week.week_number }}週 ({{ week.period_start.strftime('%m/%d') }} - {{ week.period_end.strftime('%m/%d') }})</h4>
            <div class="weekly-stats">
                投稿: {{ week.total_posts }} | いいね: {{ week.metrics.total_likes }} | RT: {{ week.metrics.total_retweets }} | ベスト日: {{ week.best_performing_day }}
            </div>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    {% if summary.top_posts %}
    <div class="card">
        <h2>🏆 トップ投稿（上位5件）</h2>
        {% for post in summary.top_posts %}
        <div class="top-post">
            <div class="text">"{{ post.text[:150] }}{% if post.text|length > 150 %}...{% endif %}"</div>
            <div class="stats">
                ❤️ {{ post.likes }} | 🔁 {{ post.retweets }} | 💬 {{ post.replies }} | {{ post.created_at.strftime('%Y-%m-%d') }}
            </div>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <div class="footer">
        <p>Generated by SocialBoostAI | {{ generated_at }}</p>
    </div>
</body>
</html>
"""


def generate_weekly_summary_report(
    summary: WeeklySummary,
    username: str,
    output_path: Optional[str] = None,
) -> str:
    """週次サマリーHTMLレポートを生成

    Args:
        summary: 週次サマリー
        username: ユーザー名
        output_path: 出力パス（指定なしの場合はreports/ディレクトリ）

    Returns:
        str: 生成されたファイルのパス
    """
    from jinja2 import Template

    template = Template(WEEKLY_SUMMARY_TEMPLATE)
    html_content = template.render(
        summary=summary,
        username=username,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    if output_path is None:
        reports_dir = os.getenv("REPORTS_DIR", "./reports")
        Path(reports_dir).mkdir(parents=True, exist_ok=True)
        output_path = os.path.join(
            reports_dir,
            f"weekly_{username}_{summary.year}_w{summary.week_number}.html",
        )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info(f"週次サマリーを生成しました: {output_path}")
    return output_path


def generate_monthly_summary_report(
    summary: MonthlySummary,
    username: str,
    output_path: Optional[str] = None,
) -> str:
    """月次サマリーHTMLレポートを生成

    Args:
        summary: 月次サマリー
        username: ユーザー名
        output_path: 出力パス（指定なしの場合はreports/ディレクトリ）

    Returns:
        str: 生成されたファイルのパス
    """
    from jinja2 import Template

    template = Template(MONTHLY_SUMMARY_TEMPLATE)
    html_content = template.render(
        summary=summary,
        username=username,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    if output_path is None:
        reports_dir = os.getenv("REPORTS_DIR", "./reports")
        Path(reports_dir).mkdir(parents=True, exist_ok=True)
        output_path = os.path.join(
            reports_dir,
            f"monthly_{username}_{summary.year}_{summary.month:02d}.html",
        )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info(f"月次サマリーを生成しました: {output_path}")
    return output_path


def generate_weekly_console_report(
    summary: WeeklySummary,
    username: str,
) -> str:
    """週次サマリーコンソールレポートを生成

    Args:
        summary: 週次サマリー
        username: ユーザー名

    Returns:
        str: レポートテキスト
    """
    lines = [
        "=" * 60,
        f"  週次サマリー - @{username}",
        f"  {summary.year}年 第{summary.week_number}週",
        "=" * 60,
        "",
        f"期間: {summary.period_start.strftime('%Y-%m-%d')} - {summary.period_end.strftime('%Y-%m-%d')}",
        "",
        "【週間メトリクス】",
        f"  投稿数: {summary.total_posts}",
        f"  総いいね: {summary.metrics.total_likes}",
        f"  総リツイート: {summary.metrics.total_retweets}",
        f"  平均いいね/投稿: {summary.metrics.avg_likes_per_post}",
        "",
        f"【ベストパフォーマンス日】 {summary.best_performing_day}",
        "",
    ]

    if summary.comparison:
        lines.append("【前週との比較】")
        for comp in summary.comparison:
            trend_symbol = (
                "↑" if comp.trend == "up" else "↓" if comp.trend == "down" else "→"
            )
            lines.append(f"  {comp.metric_name}: {trend_symbol} {comp.change_percent}%")
        lines.append("")

    if summary.insights:
        lines.append("【インサイト】")
        for insight in summary.insights:
            lines.append(f"  • {insight}")
        lines.append("")

    if summary.top_post:
        lines.extend(
            [
                "【トップ投稿】",
                f'  "{summary.top_post.text[:60]}..."',
                f"  ❤️{summary.top_post.likes} 🔁{summary.top_post.retweets} 💬{summary.top_post.replies}",
                "",
            ]
        )

    lines.extend(
        [
            "=" * 60,
            "Generated by SocialBoostAI",
            "=" * 60,
        ]
    )

    return "\n".join(lines)


def generate_monthly_console_report(
    summary: MonthlySummary,
    username: str,
) -> str:
    """月次サマリーコンソールレポートを生成

    Args:
        summary: 月次サマリー
        username: ユーザー名

    Returns:
        str: レポートテキスト
    """
    lines = [
        "=" * 60,
        f"  月次サマリー - @{username}",
        f"  {summary.year}年{summary.month}月",
        "=" * 60,
        "",
        f"期間: {summary.period_start.strftime('%Y-%m-%d')} - {summary.period_end.strftime('%Y-%m-%d')}",
        "",
    ]

    if summary.growth_rate is not None:
        trend = (
            "↑" if summary.growth_rate > 0 else "↓" if summary.growth_rate < 0 else "→"
        )
        lines.append(f"【成長率】 {trend} {summary.growth_rate}% (前月比)")
        lines.append("")

    lines.extend(
        [
            "【月間メトリクス】",
            f"  投稿数: {summary.total_posts}",
            f"  総いいね: {summary.metrics.total_likes}",
            f"  総リツイート: {summary.metrics.total_retweets}",
            f"  平均いいね/投稿: {summary.metrics.avg_likes_per_post}",
            f"  エンゲージメント率: {summary.metrics.engagement_rate}%",
            "",
        ]
    )

    if summary.best_performing_week:
        lines.append(f"【ベストパフォーマンス週】 第{summary.best_performing_week}週")
        lines.append("")

    if summary.comparison:
        lines.append("【前月との比較】")
        for comp in summary.comparison:
            trend_symbol = (
                "↑" if comp.trend == "up" else "↓" if comp.trend == "down" else "→"
            )
            lines.append(f"  {comp.metric_name}: {trend_symbol} {comp.change_percent}%")
        lines.append("")

    if summary.insights:
        lines.append("【インサイト】")
        for insight in summary.insights:
            lines.append(f"  • {insight}")
        lines.append("")

    if summary.weekly_summaries:
        lines.append("【週別サマリー】")
        for week in summary.weekly_summaries:
            lines.append(
                f"  第{week.week_number}週: 投稿{week.total_posts} / いいね{week.metrics.total_likes} / ベスト日:{week.best_performing_day}"
            )
        lines.append("")

    if summary.top_posts:
        lines.append("【トップ投稿（上位3件）】")
        for i, post in enumerate(summary.top_posts[:3], 1):
            lines.append(f'  {i}. "{post.text[:50]}..."')
            lines.append(f"     ❤️{post.likes} 🔁{post.retweets} 💬{post.replies}")
        lines.append("")

    lines.extend(
        [
            "=" * 60,
            "Generated by SocialBoostAI",
            "=" * 60,
        ]
    )

    return "\n".join(lines)
