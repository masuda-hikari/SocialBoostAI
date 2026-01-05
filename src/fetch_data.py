"""
ソーシャルメディアAPIからデータを取得するモジュール
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import tweepy
from dotenv import load_dotenv

from .models import Tweet, UserAccount

load_dotenv()

logger = logging.getLogger(__name__)


class TwitterClient:
    """Twitter API v2クライアント"""

    def __init__(self) -> None:
        """クライアントを初期化"""
        self._client: Optional[tweepy.Client] = None
        self._api: Optional[tweepy.API] = None

    def _get_client(self) -> tweepy.Client:
        """Tweepy Clientを取得（遅延初期化）"""
        if self._client is None:
            bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
            api_key = os.getenv("TWITTER_API_KEY")
            api_secret = os.getenv("TWITTER_API_SECRET")
            access_token = os.getenv("TWITTER_ACCESS_TOKEN")
            access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

            if not bearer_token:
                raise ValueError("TWITTER_BEARER_TOKEN環境変数が設定されていません")

            self._client = tweepy.Client(
                bearer_token=bearer_token,
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_token_secret,
                wait_on_rate_limit=True,
            )
        return self._client

    def get_user_info(self, username: str) -> UserAccount:
        """ユーザー情報を取得

        Args:
            username: Twitterユーザー名（@なし）

        Returns:
            UserAccount: ユーザーアカウント情報
        """
        client = self._get_client()
        user = client.get_user(
            username=username,
            user_fields=["public_metrics", "created_at"],
        )

        if user.data is None:
            raise ValueError(f"ユーザー '{username}' が見つかりません")

        metrics = user.data.public_metrics
        return UserAccount(
            id=str(user.data.id),
            platform="twitter",
            username=user.data.username,
            follower_count=metrics["followers_count"],
            following_count=metrics["following_count"],
            created_at=user.data.created_at,
        )

    def get_user_tweets(
        self,
        username: str,
        days: int = 7,
        max_results: int = 100,
    ) -> list[Tweet]:
        """ユーザーの最近のツイートを取得

        Args:
            username: Twitterユーザー名（@なし）
            days: 取得する日数
            max_results: 最大取得件数

        Returns:
            list[Tweet]: ツイートリスト
        """
        client = self._get_client()

        # ユーザーIDを取得
        user = client.get_user(username=username)
        if user.data is None:
            raise ValueError(f"ユーザー '{username}' が見つかりません")

        user_id = user.data.id
        start_time = datetime.utcnow() - timedelta(days=days)

        # ツイートを取得
        tweets_response = client.get_users_tweets(
            id=user_id,
            start_time=start_time,
            max_results=min(max_results, 100),
            tweet_fields=["created_at", "public_metrics"],
        )

        tweets: list[Tweet] = []
        if tweets_response.data:
            for tweet_data in tweets_response.data:
                metrics = tweet_data.public_metrics
                tweets.append(
                    Tweet(
                        id=str(tweet_data.id),
                        text=tweet_data.text,
                        created_at=tweet_data.created_at,
                        likes=metrics.get("like_count", 0),
                        retweets=metrics.get("retweet_count", 0),
                        replies=metrics.get("reply_count", 0),
                        impressions=metrics.get("impression_count"),
                        author_id=str(user_id),
                    )
                )

        logger.info(f"{username}から{len(tweets)}件のツイートを取得しました")
        return tweets


def load_sample_tweets(filepath: str) -> list[Tweet]:
    """サンプルJSONファイルからツイートを読み込む（テスト用）

    Args:
        filepath: JSONファイルパス

    Returns:
        list[Tweet]: ツイートリスト
    """
    import json

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    return [Tweet(**tweet) for tweet in data]
