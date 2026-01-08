"""
SocialBoostAI - AI駆動のソーシャルメディア成長アシスタント
"""

__version__ = "0.4.0"
__author__ = "SocialBoostAI Team"

# v0.3 AI拡張機能
from .ai_advanced import (
    AdvancedAISuggester,
    OptimalTimingAnalyzer,
    PersonalizedRecommender,
    ReplyGenerator,
    TrendAnalyzer,
)
from .report import (
    generate_monthly_console_report,
    generate_monthly_summary_report,
    generate_weekly_console_report,
    generate_weekly_summary_report,
)

# v0.4 サマリー機能
from .summary import (
    calculate_comparison,
    generate_monthly_summary,
    generate_period_report,
    generate_weekly_summary,
)
