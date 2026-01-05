"""
SocialBoostAI メインエントリポイント
"""

import argparse
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

from .analysis import analyze_tweets
from .fetch_data import TwitterClient, load_sample_tweets
from .report import generate_console_report, generate_html_report

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    """メイン処理

    Returns:
        int: 終了コード
    """
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="SocialBoostAI - AI駆動のソーシャルメディア成長アシスタント"
    )
    parser.add_argument(
        "--username",
        "-u",
        type=str,
        help="分析するTwitterユーザー名（@なし）",
    )
    parser.add_argument(
        "--days",
        "-d",
        type=int,
        default=7,
        help="分析する日数（デフォルト: 7）",
    )
    parser.add_argument(
        "--sample",
        "-s",
        type=str,
        help="サンプルJSONファイルを使用（テスト用）",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="HTMLレポートを生成",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="出力ファイルパス",
    )
    parser.add_argument(
        "--ai",
        action="store_true",
        help="AI提案機能を有効化",
    )

    args = parser.parse_args()

    try:
        # データ取得
        if args.sample:
            logger.info(f"サンプルデータを読み込み中: {args.sample}")
            tweets = load_sample_tweets(args.sample)
            username = "sample_user"
        elif args.username:
            logger.info(f"@{args.username}のツイートを取得中...")
            client = TwitterClient()
            tweets = client.get_user_tweets(args.username, days=args.days)
            username = args.username
        else:
            logger.error("--username または --sample オプションが必要です")
            parser.print_help()
            return 1

        # 分析実行
        logger.info("分析を実行中...")
        result = analyze_tweets(tweets)

        # AI提案を追加
        if args.ai:
            try:
                from .ai_suggest import AIContentSuggester

                logger.info("AI提案を生成中...")
                suggester = AIContentSuggester()
                result.recommendations = suggester.enhance_recommendations(result)
            except Exception as e:
                logger.warning(f"AI提案の生成に失敗しました: {e}")

        # レポート生成
        if args.html:
            output_path = generate_html_report(result, username, args.output)
            print(f"\nHTMLレポートを生成しました: {output_path}")
        else:
            report = generate_console_report(result, username)
            print(report)

        return 0

    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
