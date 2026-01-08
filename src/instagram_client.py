"""
Instagram Graph APIクライアント

Instagram Graph API（ビジネス/クリエイターアカウント用）を使用してデータを取得するモジュール。
個人アカウントはBasic Display APIを使用（機能制限あり）。

参考: https://developers.facebook.com/docs/instagram-api
"""

import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Optional

import httpx
from dotenv import load_dotenv

from .models import (
    InstagramAccount,
    InstagramEngagementMetrics,
    InstagramPost,
    InstagramReel,
    InstagramStory,
)

load_dotenv()

logger = logging.getLogger(__name__)


class InstagramAPIError(Exception):
    """Instagram API エラー"""

    def __init__(self, message: str, code: Optional[int] = None):
        super().__init__(message)
        self.code = code


class InstagramClient:
    """Instagram Graph APIクライアント

    Instagram Graph APIを使用してビジネス/クリエイターアカウントのデータを取得する。

    必要な環境変数:
        - INSTAGRAM_ACCESS_TOKEN: Facebookページアクセストークン
        - INSTAGRAM_BUSINESS_ID: InstagramビジネスアカウントID

    スコープ要件:
        - instagram_basic
        - instagram_content_publish (オプション)
        - instagram_manage_insights
        - pages_show_list
        - pages_read_engagement
    """

    BASE_URL = "https://graph.facebook.com/v18.0"

    def __init__(self) -> None:
        """クライアントを初期化"""
        self._access_token: Optional[str] = None
        self._business_id: Optional[str] = None
        self._client: Optional[httpx.Client] = None

    def _get_access_token(self) -> str:
        """アクセストークンを取得"""
        if self._access_token is None:
            self._access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
            if not self._access_token:
                raise InstagramAPIError(
                    "INSTAGRAM_ACCESS_TOKEN環境変数が設定されていません"
                )
        return self._access_token

    def _get_business_id(self) -> str:
        """ビジネスアカウントIDを取得"""
        if self._business_id is None:
            self._business_id = os.getenv("INSTAGRAM_BUSINESS_ID")
            if not self._business_id:
                raise InstagramAPIError(
                    "INSTAGRAM_BUSINESS_ID環境変数が設定されていません"
                )
        return self._business_id

    def _get_client(self) -> httpx.Client:
        """HTTPクライアントを取得（遅延初期化）"""
        if self._client is None:
            self._client = httpx.Client(timeout=30.0)
        return self._client

    def _make_request(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        method: str = "GET",
    ) -> dict:
        """APIリクエストを実行

        Args:
            endpoint: APIエンドポイント（例: "me/media"）
            params: クエリパラメータ
            method: HTTPメソッド

        Returns:
            dict: APIレスポンス

        Raises:
            InstagramAPIError: APIエラー
        """
        client = self._get_client()
        url = f"{self.BASE_URL}/{endpoint}"

        if params is None:
            params = {}
        params["access_token"] = self._get_access_token()

        try:
            if method == "GET":
                response = client.get(url, params=params)
            elif method == "POST":
                response = client.post(url, params=params)
            else:
                raise ValueError(f"サポートされていないHTTPメソッド: {method}")

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            error_data = e.response.json().get("error", {})
            error_message = error_data.get("message", str(e))
            error_code = error_data.get("code")
            logger.error(f"Instagram API エラー: {error_message} (code: {error_code})")
            raise InstagramAPIError(error_message, error_code) from e

        except httpx.RequestError as e:
            logger.error(f"Instagram API リクエストエラー: {e}")
            raise InstagramAPIError(f"リクエストエラー: {e}") from e

    def get_account_info(self) -> InstagramAccount:
        """アカウント情報を取得

        Returns:
            InstagramAccount: アカウント情報
        """
        business_id = self._get_business_id()
        fields = ",".join([
            "id",
            "username",
            "name",
            "biography",
            "profile_picture_url",
            "website",
            "followers_count",
            "follows_count",
            "media_count",
        ])

        data = self._make_request(business_id, {"fields": fields})

        return InstagramAccount(
            id=data["id"],
            username=data.get("username", ""),
            name=data.get("name"),
            biography=data.get("biography"),
            profile_picture_url=data.get("profile_picture_url"),
            website=data.get("website"),
            followers_count=data.get("followers_count", 0),
            following_count=data.get("follows_count", 0),
            media_count=data.get("media_count", 0),
            is_business_account=True,
        )

    def get_media(
        self,
        limit: int = 25,
        since: Optional[datetime] = None,
    ) -> list[InstagramPost]:
        """投稿一覧を取得

        Args:
            limit: 取得件数（最大100）
            since: この日時以降の投稿のみ取得

        Returns:
            list[InstagramPost]: 投稿リスト
        """
        business_id = self._get_business_id()
        fields = ",".join([
            "id",
            "caption",
            "media_type",
            "media_url",
            "thumbnail_url",
            "permalink",
            "timestamp",
            "like_count",
            "comments_count",
        ])

        params = {
            "fields": fields,
            "limit": min(limit, 100),
        }

        data = self._make_request(f"{business_id}/media", params)
        posts: list[InstagramPost] = []

        for item in data.get("data", []):
            created_at = datetime.fromisoformat(
                item["timestamp"].replace("Z", "+00:00")
            )

            # sinceフィルタ
            if since and created_at < since:
                continue

            # リールは別モデルなのでスキップ
            if item.get("media_type") == "REELS":
                continue

            posts.append(InstagramPost(
                id=item["id"],
                caption=item.get("caption"),
                media_type=item.get("media_type", "IMAGE"),
                media_url=item.get("media_url"),
                thumbnail_url=item.get("thumbnail_url"),
                permalink=item.get("permalink"),
                created_at=created_at,
                likes=item.get("like_count", 0),
                comments=item.get("comments_count", 0),
                author_id=business_id,
            ))

        logger.info(f"{len(posts)}件のInstagram投稿を取得しました")
        return posts

    def get_media_insights(self, media_id: str) -> dict:
        """投稿のインサイト（詳細指標）を取得

        Args:
            media_id: メディアID

        Returns:
            dict: インサイトデータ

        Note:
            ビジネス/クリエイターアカウントのみ利用可能
        """
        # メディアタイプによってmetricが異なる
        metrics = ",".join([
            "impressions",
            "reach",
            "saved",
            "engagement",
        ])

        try:
            data = self._make_request(
                f"{media_id}/insights",
                {"metric": metrics}
            )

            result = {}
            for item in data.get("data", []):
                result[item["name"]] = item["values"][0]["value"]
            return result

        except InstagramAPIError as e:
            logger.warning(f"インサイト取得失敗 (media_id: {media_id}): {e}")
            return {}

    def get_reels(self, limit: int = 25) -> list[InstagramReel]:
        """リール一覧を取得

        Args:
            limit: 取得件数

        Returns:
            list[InstagramReel]: リールリスト
        """
        business_id = self._get_business_id()
        fields = ",".join([
            "id",
            "caption",
            "media_type",
            "media_url",
            "thumbnail_url",
            "permalink",
            "timestamp",
            "like_count",
            "comments_count",
        ])

        params = {
            "fields": fields,
            "limit": min(limit, 100),
        }

        data = self._make_request(f"{business_id}/media", params)
        reels: list[InstagramReel] = []

        for item in data.get("data", []):
            # リールのみ抽出
            if item.get("media_type") != "REELS":
                continue

            created_at = datetime.fromisoformat(
                item["timestamp"].replace("Z", "+00:00")
            )

            reels.append(InstagramReel(
                id=item["id"],
                caption=item.get("caption"),
                media_url=item.get("media_url"),
                thumbnail_url=item.get("thumbnail_url"),
                permalink=item.get("permalink"),
                created_at=created_at,
                likes=item.get("like_count", 0),
                comments=item.get("comments_count", 0),
                author_id=business_id,
            ))

        logger.info(f"{len(reels)}件のInstagramリールを取得しました")
        return reels

    def get_stories(self) -> list[InstagramStory]:
        """現在のストーリー一覧を取得

        Returns:
            list[InstagramStory]: ストーリーリスト（24時間以内のもの）

        Note:
            ストーリーは24時間で消えるため、アクティブなもののみ取得可能
        """
        business_id = self._get_business_id()
        fields = ",".join([
            "id",
            "media_type",
            "media_url",
            "timestamp",
        ])

        data = self._make_request(f"{business_id}/stories", {"fields": fields})
        stories: list[InstagramStory] = []

        for item in data.get("data", []):
            created_at = datetime.fromisoformat(
                item["timestamp"].replace("Z", "+00:00")
            )
            expires_at = created_at + timedelta(hours=24)

            stories.append(InstagramStory(
                id=item["id"],
                media_type=item.get("media_type", "IMAGE"),
                media_url=item.get("media_url"),
                created_at=created_at,
                expires_at=expires_at,
            ))

        logger.info(f"{len(stories)}件のInstagramストーリーを取得しました")
        return stories

    def get_account_insights(
        self,
        period: str = "day",
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> dict:
        """アカウントインサイトを取得

        Args:
            period: 期間（"day", "week", "days_28"）
            since: 開始日時
            until: 終了日時

        Returns:
            dict: インサイトデータ

        Note:
            ビジネス/クリエイターアカウントのみ利用可能
        """
        business_id = self._get_business_id()
        metrics = ",".join([
            "impressions",
            "reach",
            "profile_views",
            "follower_count",
        ])

        params = {
            "metric": metrics,
            "period": period,
        }

        if since:
            params["since"] = int(since.timestamp())
        if until:
            params["until"] = int(until.timestamp())

        data = self._make_request(f"{business_id}/insights", params)

        result = {}
        for item in data.get("data", []):
            result[item["name"]] = item["values"]
        return result

    def calculate_engagement_metrics(
        self,
        posts: list[InstagramPost],
        follower_count: int = 0,
    ) -> InstagramEngagementMetrics:
        """エンゲージメント指標を計算

        Args:
            posts: 投稿リスト
            follower_count: フォロワー数（エンゲージメント率計算用）

        Returns:
            InstagramEngagementMetrics: エンゲージメント指標
        """
        if not posts:
            return InstagramEngagementMetrics()

        total_likes = sum(p.likes for p in posts)
        total_comments = sum(p.comments for p in posts)
        total_saves = sum(p.saves or 0 for p in posts)
        total_shares = sum(p.shares or 0 for p in posts)
        total_impressions = sum(p.impressions or 0 for p in posts)
        total_reach = sum(p.reach or 0 for p in posts)

        post_count = len(posts)
        total_engagement = total_likes + total_comments + total_saves

        # エンゲージメント率（フォロワーベース）
        engagement_rate = 0.0
        if follower_count > 0:
            engagement_rate = (total_engagement / post_count / follower_count) * 100

        return InstagramEngagementMetrics(
            total_likes=total_likes,
            total_comments=total_comments,
            total_saves=total_saves,
            total_shares=total_shares,
            total_impressions=total_impressions,
            total_reach=total_reach,
            engagement_rate=engagement_rate,
            avg_likes_per_post=total_likes / post_count,
            avg_comments_per_post=total_comments / post_count,
            avg_saves_per_post=total_saves / post_count,
        )

    def close(self) -> None:
        """HTTPクライアントをクローズ"""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self) -> "InstagramClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


def load_sample_instagram_posts(filepath: str) -> list[InstagramPost]:
    """サンプルJSONファイルからInstagram投稿を読み込む（テスト用）

    Args:
        filepath: JSONファイルパス

    Returns:
        list[InstagramPost]: 投稿リスト
    """
    import json

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    return [InstagramPost(**post) for post in data]
