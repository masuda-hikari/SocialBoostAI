"""
レポート生成モジュール
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .models import AnalysisResult

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
