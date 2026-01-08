"""
YouTube APIクライアント

YouTube Data API v3を使用して動画・チャンネルデータを取得するモジュール。

参考: https://developers.google.com/youtube/v3/docs
"""

import json
import logging
import os
import re
from datetime import UTC, datetime, timedelta
from typing import Optional

import httpx
from dotenv import load_dotenv

from .models import (
    YouTubeChannel,
    YouTubeEngagementMetrics,
    YouTubeShort,
    YouTubeVideo,
)

load_dotenv()

logger = logging.getLogger(__name__)


class YouTubeAPIError(Exception):
    """YouTube API エラー"""

    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__(message)
        self.code = code


class YouTubeClient:
    """YouTube APIクライアント

    YouTube Data API v3を使用してチャンネルと動画のデータを取得する。

    必要な環境変数:
        - YOUTUBE_API_KEY: YouTube Data API キー

    または OAuth2認証の場合:
        - YOUTUBE_ACCESS_TOKEN: YouTubeアクセストークン
        - YOUTUBE_REFRESH_TOKEN: YouTubeリフレッシュトークン
        - YOUTUBE_CLIENT_ID: クライアントID
        - YOUTUBE_CLIENT_SECRET: クライアントシークレット
    """

    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(self) -> None:
        """クライアントを初期化"""
        self._api_key: Optional[str] = None
        self._access_token: Optional[str] = None
        self._client: Optional[httpx.Client] = None

    def _get_api_key(self) -> str:
        """APIキーを取得"""
        if self._api_key is None:
            self._api_key = os.getenv("YOUTUBE_API_KEY")
            if not self._api_key:
                raise YouTubeAPIError(
                    "YOUTUBE_API_KEY環境変数が設定されていません"
                )
        return self._api_key

    def _get_access_token(self) -> Optional[str]:
        """アクセストークンを取得（OAuth2用）"""
        if self._access_token is None:
            self._access_token = os.getenv("YOUTUBE_ACCESS_TOKEN")
        return self._access_token

    def _get_client(self) -> httpx.Client:
        """HTTPクライアントを取得（遅延初期化）"""
        if self._client is None:
            self._client = httpx.Client(timeout=30.0)
        return self._client

    def _make_request(
        self,
        endpoint: str,
        params: Optional[dict] = None,
    ) -> dict:
        """APIリクエストを実行

        Args:
            endpoint: APIエンドポイント（例: "videos"）
            params: クエリパラメータ

        Returns:
            dict: APIレスポンス

        Raises:
            YouTubeAPIError: APIエラー
        """
        client = self._get_client()
        url = f"{self.BASE_URL}/{endpoint}"

        if params is None:
            params = {}

        # 認証: OAuth2トークンがあればそちらを使用、なければAPIキー
        access_token = self._get_access_token()
        headers = {}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        else:
            params["key"] = self._get_api_key()

        try:
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            try:
                error_data = e.response.json().get("error", {})
                error_message = error_data.get("message", str(e))
                error_code = str(error_data.get("code"))
            except Exception:
                error_message = str(e)
                error_code = None
            logger.error(f"YouTube API エラー: {error_message} (code: {error_code})")
            raise YouTubeAPIError(error_message, error_code) from e

        except httpx.RequestError as e:
            logger.error(f"YouTube API リクエストエラー: {e}")
            raise YouTubeAPIError(f"リクエストエラー: {e}") from e

    def get_channel_info(self, channel_id: Optional[str] = None) -> YouTubeChannel:
        """チャンネル情報を取得

        Args:
            channel_id: チャンネルID（省略時は認証ユーザーのチャンネル）

        Returns:
            YouTubeChannel: チャンネル情報
        """
        params = {
            "part": "snippet,statistics,brandingSettings",
        }

        if channel_id:
            params["id"] = channel_id
        else:
            params["mine"] = "true"

        data = self._make_request("channels", params=params)
        items = data.get("items", [])

        if not items:
            raise YouTubeAPIError("チャンネルが見つかりません")

        item = items[0]
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        branding = item.get("brandingSettings", {}).get("channel", {})

        # 公開日時の変換
        published_at = None
        if snippet.get("publishedAt"):
            published_at = datetime.fromisoformat(
                snippet["publishedAt"].replace("Z", "+00:00")
            )

        return YouTubeChannel(
            id=item.get("id", ""),
            title=snippet.get("title", ""),
            description=snippet.get("description"),
            custom_url=snippet.get("customUrl"),
            thumbnail_url=snippet.get("thumbnails", {}).get("default", {}).get("url"),
            banner_url=branding.get("image", {}).get("bannerExternalUrl"),
            country=snippet.get("country"),
            published_at=published_at,
            subscribers_count=int(statistics.get("subscriberCount", 0)),
            video_count=int(statistics.get("videoCount", 0)),
            view_count=int(statistics.get("viewCount", 0)),
            is_verified=False,  # APIでは直接取得できない
        )

    def get_videos(
        self,
        channel_id: str,
        max_results: int = 50,
        page_token: Optional[str] = None,
        published_after: Optional[datetime] = None,
    ) -> tuple[list[YouTubeVideo], Optional[str]]:
        """チャンネルの動画リストを取得

        Args:
            channel_id: チャンネルID
            max_results: 取得件数（最大50）
            page_token: ページネーション用トークン
            published_after: この日時以降の動画のみ取得

        Returns:
            tuple[list[YouTubeVideo], Optional[str]]:
                - 動画リスト
                - 次ページのトークン
        """
        # まず検索APIで動画IDを取得
        search_params = {
            "part": "id",
            "channelId": channel_id,
            "type": "video",
            "order": "date",
            "maxResults": min(max_results, 50),
        }

        if page_token:
            search_params["pageToken"] = page_token

        if published_after:
            search_params["publishedAfter"] = published_after.isoformat() + "Z"

        search_data = self._make_request("search", params=search_params)

        video_ids = [
            item["id"]["videoId"]
            for item in search_data.get("items", [])
            if item.get("id", {}).get("videoId")
        ]

        if not video_ids:
            return [], None

        # 動画詳細を取得
        videos_params = {
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(video_ids),
        }

        videos_data = self._make_request("videos", params=videos_params)

        videos: list[YouTubeVideo] = []
        for item in videos_data.get("items", []):
            video = self._parse_video(item)
            videos.append(video)

        next_page_token = search_data.get("nextPageToken")
        logger.info(f"{len(videos)}件のYouTube動画を取得しました")

        return videos, next_page_token

    def _parse_video(self, item: dict) -> YouTubeVideo:
        """API レスポンスから動画オブジェクトを生成

        Args:
            item: YouTube API の動画アイテム

        Returns:
            YouTubeVideo: 動画オブジェクト
        """
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        content_details = item.get("contentDetails", {})

        # 公開日時の変換
        published_at = datetime.now(UTC)
        if snippet.get("publishedAt"):
            published_at = datetime.fromisoformat(
                snippet["publishedAt"].replace("Z", "+00:00")
            )

        # 動画の長さをISO 8601形式から秒に変換
        duration = self._parse_duration(content_details.get("duration", "PT0S"))

        # 動画タイプを判定（Shortsは60秒以下で縦向き）
        video_type = "video"
        if duration <= 60:
            # Shorts判定（本来はアスペクト比も必要だが、長さで簡易判定）
            video_type = "short"

        # タグを取得
        tags = snippet.get("tags", [])

        return YouTubeVideo(
            id=item.get("id", ""),
            title=snippet.get("title", ""),
            description=snippet.get("description"),
            published_at=published_at,
            thumbnail_url=snippet.get("thumbnails", {}).get("medium", {}).get("url"),
            duration=duration,
            views=int(statistics.get("viewCount", 0)),
            likes=int(statistics.get("likeCount", 0)),
            dislikes=0,  # 非公開化されている
            comments=int(statistics.get("commentCount", 0)),
            video_type=video_type,
            category_id=snippet.get("categoryId"),
            tags=tags,
            channel_id=snippet.get("channelId"),
            channel_title=snippet.get("channelTitle"),
            video_url=f"https://www.youtube.com/watch?v={item.get('id', '')}",
        )

    def get_all_videos(
        self,
        channel_id: str,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> list[YouTubeVideo]:
        """全動画を取得（ページネーション対応）

        Args:
            channel_id: チャンネルID
            limit: 取得上限
            since: この日時以降の動画のみ取得

        Returns:
            list[YouTubeVideo]: 動画リスト
        """
        all_videos: list[YouTubeVideo] = []
        page_token: Optional[str] = None

        while len(all_videos) < limit:
            remaining = limit - len(all_videos)
            batch_size = min(50, remaining)

            videos, page_token = self.get_videos(
                channel_id=channel_id,
                max_results=batch_size,
                page_token=page_token,
                published_after=since,
            )

            all_videos.extend(videos)

            if not page_token or not videos:
                break

        logger.info(f"合計{len(all_videos)}件のYouTube動画を取得しました")
        return all_videos[:limit]

    def get_video_by_id(self, video_id: str) -> Optional[YouTubeVideo]:
        """動画IDで動画を取得

        Args:
            video_id: 動画ID

        Returns:
            Optional[YouTubeVideo]: 動画（見つからない場合はNone）
        """
        params = {
            "part": "snippet,statistics,contentDetails",
            "id": video_id,
        }

        data = self._make_request("videos", params=params)
        items = data.get("items", [])

        if not items:
            return None

        return self._parse_video(items[0])

    def calculate_engagement_metrics(
        self,
        videos: list[YouTubeVideo],
    ) -> YouTubeEngagementMetrics:
        """エンゲージメント指標を計算

        Args:
            videos: 動画リスト

        Returns:
            YouTubeEngagementMetrics: エンゲージメント指標
        """
        if not videos:
            return YouTubeEngagementMetrics()

        total_views = sum(v.views for v in videos)
        total_likes = sum(v.likes for v in videos)
        total_comments = sum(v.comments for v in videos)
        total_shares = sum(v.shares or 0 for v in videos)

        video_count = len(videos)
        total_engagement = total_likes + total_comments

        # エンゲージメント率（ビューベース）
        engagement_rate = 0.0
        if total_views > 0:
            engagement_rate = (total_engagement / total_views) * 100

        # いいね率
        view_to_like_ratio = 0.0
        if total_views > 0:
            view_to_like_ratio = (total_likes / total_views) * 100

        # 視聴時間関連
        total_watch_time = sum(v.watch_time_minutes or 0 for v in videos)
        avg_duration = sum(v.avg_view_duration or 0 for v in videos) / video_count if video_count else 0
        avg_percentage = sum(v.avg_view_percentage or 0 for v in videos) / video_count if video_count else 0

        # Shorts視聴比率
        shorts_views = sum(v.views for v in videos if v.video_type == "short")
        shorts_rate = (shorts_views / total_views * 100) if total_views > 0 else 0

        return YouTubeEngagementMetrics(
            total_views=total_views,
            total_likes=total_likes,
            total_comments=total_comments,
            total_shares=total_shares,
            engagement_rate=round(engagement_rate, 4),
            avg_views_per_video=round(total_views / video_count, 2),
            avg_likes_per_video=round(total_likes / video_count, 2),
            avg_comments_per_video=round(total_comments / video_count, 2),
            view_to_like_ratio=round(view_to_like_ratio, 4),
            total_watch_time_hours=round(total_watch_time / 60, 2),
            avg_view_duration_seconds=round(avg_duration, 2),
            avg_view_percentage=round(avg_percentage, 2),
            shorts_view_rate=round(shorts_rate, 2),
        )

    @staticmethod
    def _parse_duration(duration_str: str) -> int:
        """ISO 8601形式の長さを秒に変換

        Args:
            duration_str: ISO 8601形式の長さ（例: "PT1H2M30S"）

        Returns:
            int: 秒数
        """
        if not duration_str:
            return 0

        # パターン: PT1H2M30S
        pattern = r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"
        match = re.match(pattern, duration_str)

        if not match:
            return 0

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)

        return hours * 3600 + minutes * 60 + seconds

    @staticmethod
    def _extract_tags(description: str) -> list[str]:
        """説明からハッシュタグを抽出

        Args:
            description: 動画説明テキスト

        Returns:
            list[str]: ハッシュタグリスト（#なし）
        """
        if not description:
            return []
        pattern = r"#([^\s#]+)"
        matches = re.findall(pattern, description)
        return [m.lower() for m in matches]

    def close(self) -> None:
        """HTTPクライアントをクローズ"""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self) -> "YouTubeClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


def load_sample_youtube_videos(filepath: str) -> list[YouTubeVideo]:
    """サンプルJSONファイルからYouTube動画を読み込む（テスト用）

    Args:
        filepath: JSONファイルパス

    Returns:
        list[YouTubeVideo]: 動画リスト
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    videos = []
    for item in data:
        # published_atの変換
        if isinstance(item.get("published_at"), str):
            item["published_at"] = datetime.fromisoformat(
                item["published_at"].replace("Z", "+00:00")
            )
        videos.append(YouTubeVideo(**item))

    return videos
