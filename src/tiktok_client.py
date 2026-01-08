"""
TikTok APIクライアント

TikTok API for Business（Content Posting API / Research API）を使用してデータを取得するモジュール。

参考: https://developers.tiktok.com/doc/overview/
"""

import json
import logging
import os
import re
from datetime import UTC, datetime
from typing import Optional

import httpx
from dotenv import load_dotenv

from .models import (
    TikTokAccount,
    TikTokEngagementMetrics,
    TikTokVideo,
)

load_dotenv()

logger = logging.getLogger(__name__)


class TikTokAPIError(Exception):
    """TikTok API エラー"""

    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__(message)
        self.code = code


class TikTokClient:
    """TikTok APIクライアント

    TikTok API for Businessを使用してビジネスアカウントのデータを取得する。

    必要な環境変数:
        - TIKTOK_ACCESS_TOKEN: TikTokアクセストークン
        - TIKTOK_CLIENT_KEY: TikTokクライアントキー（OAuth用）
        - TIKTOK_CLIENT_SECRET: TikTokクライアントシークレット（OAuth用）

    スコープ要件:
        - user.info.basic
        - video.list
        - video.insights (ビジネスアカウントのみ)
    """

    BASE_URL = "https://open.tiktokapis.com/v2"

    def __init__(self) -> None:
        """クライアントを初期化"""
        self._access_token: Optional[str] = None
        self._client: Optional[httpx.Client] = None

    def _get_access_token(self) -> str:
        """アクセストークンを取得"""
        if self._access_token is None:
            self._access_token = os.getenv("TIKTOK_ACCESS_TOKEN")
            if not self._access_token:
                raise TikTokAPIError(
                    "TIKTOK_ACCESS_TOKEN環境変数が設定されていません"
                )
        return self._access_token

    def _get_client(self) -> httpx.Client:
        """HTTPクライアントを取得（遅延初期化）"""
        if self._client is None:
            self._client = httpx.Client(timeout=30.0)
        return self._client

    def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
    ) -> dict:
        """APIリクエストを実行

        Args:
            endpoint: APIエンドポイント（例: "user/info/"）
            method: HTTPメソッド
            params: クエリパラメータ
            json_data: リクエストボディ（JSON）

        Returns:
            dict: APIレスポンス

        Raises:
            TikTokAPIError: APIエラー
        """
        client = self._get_client()
        url = f"{self.BASE_URL}/{endpoint}"

        headers = {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Content-Type": "application/json",
        }

        try:
            if method == "GET":
                response = client.get(url, headers=headers, params=params)
            elif method == "POST":
                response = client.post(
                    url, headers=headers, params=params, json=json_data
                )
            else:
                raise ValueError(f"サポートされていないHTTPメソッド: {method}")

            response.raise_for_status()
            data = response.json()

            # TikTok APIのエラーレスポンス形式をチェック
            if "error" in data and data["error"].get("code") != "ok":
                error_info = data["error"]
                error_message = error_info.get("message", "Unknown error")
                error_code = error_info.get("code")
                raise TikTokAPIError(error_message, error_code)

            return data

        except httpx.HTTPStatusError as e:
            try:
                error_data = e.response.json().get("error", {})
                error_message = error_data.get("message", str(e))
                error_code = error_data.get("code")
            except Exception:
                error_message = str(e)
                error_code = None
            logger.error(f"TikTok API エラー: {error_message} (code: {error_code})")
            raise TikTokAPIError(error_message, error_code) from e

        except httpx.RequestError as e:
            logger.error(f"TikTok API リクエストエラー: {e}")
            raise TikTokAPIError(f"リクエストエラー: {e}") from e

    def get_user_info(self) -> TikTokAccount:
        """ユーザー情報を取得

        Returns:
            TikTokAccount: アカウント情報
        """
        # ユーザー情報取得エンドポイント
        params = {
            "fields": ",".join([
                "open_id",
                "union_id",
                "avatar_url",
                "display_name",
                "bio_description",
                "follower_count",
                "following_count",
                "likes_count",
                "video_count",
                "is_verified",
            ])
        }

        data = self._make_request("user/info/", params=params)
        user_data = data.get("data", {}).get("user", {})

        return TikTokAccount(
            id=user_data.get("open_id", ""),
            username=user_data.get("display_name", ""),  # TikTokはdisplay_nameをusernameとして使用
            display_name=user_data.get("display_name"),
            bio=user_data.get("bio_description"),
            avatar_url=user_data.get("avatar_url"),
            followers_count=user_data.get("follower_count", 0),
            following_count=user_data.get("following_count", 0),
            likes_count=user_data.get("likes_count", 0),
            video_count=user_data.get("video_count", 0),
            is_verified=user_data.get("is_verified", False),
            is_business_account=True,  # APIアクセスがある時点でビジネスアカウント
        )

    def get_videos(
        self,
        max_count: int = 20,
        cursor: Optional[int] = None,
    ) -> tuple[list[TikTokVideo], Optional[int], bool]:
        """動画リストを取得

        Args:
            max_count: 取得件数（最大20）
            cursor: ページネーション用カーソル

        Returns:
            tuple[list[TikTokVideo], Optional[int], bool]:
                - 動画リスト
                - 次ページのカーソル
                - さらにデータがあるか
        """
        params = {
            "fields": ",".join([
                "id",
                "title",
                "create_time",
                "cover_image_url",
                "share_url",
                "video_description",
                "duration",
                "like_count",
                "comment_count",
                "share_count",
                "view_count",
            ])
        }

        json_data = {
            "max_count": min(max_count, 20),
        }
        if cursor:
            json_data["cursor"] = cursor

        data = self._make_request(
            "video/list/", method="POST", params=params, json_data=json_data
        )

        videos_data = data.get("data", {}).get("videos", [])
        next_cursor = data.get("data", {}).get("cursor")
        has_more = data.get("data", {}).get("has_more", False)

        videos: list[TikTokVideo] = []
        for item in videos_data:
            # タイムスタンプをdatetimeに変換
            create_time = datetime.fromtimestamp(
                item.get("create_time", 0), tz=UTC
            )

            # 説明からハッシュタグを抽出
            description = item.get("video_description") or item.get("title") or ""
            hashtags = self._extract_hashtags(description)
            mentions = self._extract_mentions(description)

            videos.append(TikTokVideo(
                id=item.get("id", ""),
                description=description,
                create_time=create_time,
                duration=item.get("duration", 0),
                cover_image_url=item.get("cover_image_url"),
                share_url=item.get("share_url"),
                likes=item.get("like_count", 0),
                comments=item.get("comment_count", 0),
                shares=item.get("share_count", 0),
                views=item.get("view_count", 0),
                hashtags=hashtags,
                mentions=mentions,
            ))

        logger.info(f"{len(videos)}件のTikTok動画を取得しました")
        return videos, next_cursor, has_more

    def get_all_videos(
        self,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> list[TikTokVideo]:
        """全動画を取得（ページネーション対応）

        Args:
            limit: 取得上限
            since: この日時以降の動画のみ取得

        Returns:
            list[TikTokVideo]: 動画リスト
        """
        all_videos: list[TikTokVideo] = []
        cursor: Optional[int] = None
        has_more = True

        while has_more and len(all_videos) < limit:
            remaining = limit - len(all_videos)
            batch_size = min(20, remaining)

            videos, cursor, has_more = self.get_videos(
                max_count=batch_size, cursor=cursor
            )

            for video in videos:
                # sinceフィルタ
                if since and video.create_time < since:
                    has_more = False
                    break
                all_videos.append(video)

        logger.info(f"合計{len(all_videos)}件のTikTok動画を取得しました")
        return all_videos[:limit]

    def get_video_insights(self, video_id: str) -> dict:
        """動画のインサイト（詳細指標）を取得

        Args:
            video_id: 動画ID

        Returns:
            dict: インサイトデータ

        Note:
            ビジネスアカウントのみ利用可能
        """
        try:
            # インサイトエンドポイント（ビジネスアカウント限定）
            # 注: 実際のAPIエンドポイントは要確認
            params = {
                "fields": ",".join([
                    "reach",
                    "impressions",
                    "video_views",
                    "engagement_rate",
                    "average_time_watched",
                    "total_time_watched",
                ])
            }
            json_data = {"video_ids": [video_id]}

            data = self._make_request(
                "video/query/", method="POST", params=params, json_data=json_data
            )

            videos = data.get("data", {}).get("videos", [])
            if videos:
                return videos[0]
            return {}

        except TikTokAPIError as e:
            logger.warning(f"インサイト取得失敗 (video_id: {video_id}): {e}")
            return {}

    def calculate_engagement_metrics(
        self,
        videos: list[TikTokVideo],
    ) -> TikTokEngagementMetrics:
        """エンゲージメント指標を計算

        Args:
            videos: 動画リスト

        Returns:
            TikTokEngagementMetrics: エンゲージメント指標
        """
        if not videos:
            return TikTokEngagementMetrics()

        total_views = sum(v.views for v in videos)
        total_likes = sum(v.likes for v in videos)
        total_comments = sum(v.comments for v in videos)
        total_shares = sum(v.shares for v in videos)
        total_saves = sum(v.saves or 0 for v in videos)

        video_count = len(videos)
        total_engagement = total_likes + total_comments + total_shares

        # エンゲージメント率（ビューベース）
        engagement_rate = 0.0
        if total_views > 0:
            engagement_rate = (total_engagement / total_views) * 100

        # いいね率
        view_to_like_ratio = 0.0
        if total_views > 0:
            view_to_like_ratio = (total_likes / total_views) * 100

        return TikTokEngagementMetrics(
            total_views=total_views,
            total_likes=total_likes,
            total_comments=total_comments,
            total_shares=total_shares,
            total_saves=total_saves,
            engagement_rate=round(engagement_rate, 4),
            avg_views_per_video=round(total_views / video_count, 2),
            avg_likes_per_video=round(total_likes / video_count, 2),
            avg_comments_per_video=round(total_comments / video_count, 2),
            avg_shares_per_video=round(total_shares / video_count, 2),
            view_to_like_ratio=round(view_to_like_ratio, 4),
        )

    @staticmethod
    def _extract_hashtags(text: str) -> list[str]:
        """テキストからハッシュタグを抽出

        Args:
            text: テキスト

        Returns:
            list[str]: ハッシュタグリスト（#なし）
        """
        if not text:
            return []
        pattern = r"#([^\s#]+)"
        matches = re.findall(pattern, text)
        return [m.lower() for m in matches]

    @staticmethod
    def _extract_mentions(text: str) -> list[str]:
        """テキストからメンションを抽出

        Args:
            text: テキスト

        Returns:
            list[str]: メンションリスト（@なし）
        """
        if not text:
            return []
        pattern = r"@([^\s@]+)"
        matches = re.findall(pattern, text)
        return matches

    def close(self) -> None:
        """HTTPクライアントをクローズ"""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self) -> "TikTokClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


def load_sample_tiktok_videos(filepath: str) -> list[TikTokVideo]:
    """サンプルJSONファイルからTikTok動画を読み込む（テスト用）

    Args:
        filepath: JSONファイルパス

    Returns:
        list[TikTokVideo]: 動画リスト
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    videos = []
    for item in data:
        # create_timeの変換
        if isinstance(item.get("create_time"), str):
            item["create_time"] = datetime.fromisoformat(
                item["create_time"].replace("Z", "+00:00")
            )
        videos.append(TikTokVideo(**item))

    return videos
