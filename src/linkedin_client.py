"""
LinkedIn APIクライアント

LinkedIn Marketing API を使用して投稿・プロフィールデータを取得するモジュール。

参考: https://learn.microsoft.com/en-us/linkedin/marketing/
"""

import json
import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Optional

import httpx
from dotenv import load_dotenv

from .models import (
    LinkedInArticle,
    LinkedInCompanyPage,
    LinkedInDemographics,
    LinkedInEngagementMetrics,
    LinkedInPost,
    LinkedInProfile,
)

load_dotenv()

logger = logging.getLogger(__name__)


class LinkedInAPIError(Exception):
    """LinkedIn API エラー"""

    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__(message)
        self.code = code


class LinkedInClient:
    """LinkedIn APIクライアント

    LinkedIn Marketing APIを使用して投稿とプロフィールデータを取得する。

    必要な環境変数:
        - LINKEDIN_ACCESS_TOKEN: LinkedInアクセストークン
        - LINKEDIN_REFRESH_TOKEN: LinkedInリフレッシュトークン（オプション）
        - LINKEDIN_CLIENT_ID: クライアントID（トークン更新用）
        - LINKEDIN_CLIENT_SECRET: クライアントシークレット（トークン更新用）
    """

    BASE_URL = "https://api.linkedin.com/v2"
    REST_URL = "https://api.linkedin.com/rest"  # v2より新しいREST API

    def __init__(self) -> None:
        """クライアントを初期化"""
        self._access_token: Optional[str] = None
        self._client: Optional[httpx.Client] = None

    def _get_access_token(self) -> str:
        """アクセストークンを取得"""
        if self._access_token is None:
            self._access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
            if not self._access_token:
                raise LinkedInAPIError(
                    "LINKEDIN_ACCESS_TOKEN環境変数が設定されていません"
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
        params: Optional[dict] = None,
        use_rest_api: bool = False,
    ) -> dict:
        """APIリクエストを実行

        Args:
            endpoint: APIエンドポイント（例: "posts"）
            params: クエリパラメータ
            use_rest_api: REST API（/rest）を使用するか

        Returns:
            dict: APIレスポンス

        Raises:
            LinkedInAPIError: APIエラー
        """
        client = self._get_client()
        base_url = self.REST_URL if use_rest_api else self.BASE_URL
        url = f"{base_url}/{endpoint}"

        if params is None:
            params = {}

        headers = {
            "Authorization": f"Bearer {self._get_access_token()}",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": "202401",  # API バージョン
        }

        try:
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            try:
                error_data = e.response.json()
                error_message = error_data.get("message", str(e))
                error_code = str(error_data.get("status"))
            except Exception:
                error_message = str(e)
                error_code = None
            logger.error(f"LinkedIn API エラー: {error_message} (code: {error_code})")
            raise LinkedInAPIError(error_message, error_code) from e

        except httpx.RequestError as e:
            logger.error(f"LinkedIn API リクエストエラー: {e}")
            raise LinkedInAPIError(f"リクエストエラー: {e}") from e

    def get_profile(self) -> LinkedInProfile:
        """認証ユーザーのプロフィールを取得

        Returns:
            LinkedInProfile: プロフィール情報
        """
        # userinfo エンドポイントで基本情報取得
        data = self._make_request("userinfo")

        return LinkedInProfile(
            id=data.get("sub", ""),
            first_name=data.get("given_name", ""),
            last_name=data.get("family_name", ""),
            profile_picture_url=data.get("picture"),
            # 追加情報は別途取得が必要
        )

    def get_profile_detail(self, person_id: Optional[str] = None) -> LinkedInProfile:
        """詳細プロフィール情報を取得

        Args:
            person_id: プロフィールID（省略時は認証ユーザー）

        Returns:
            LinkedInProfile: 詳細プロフィール情報
        """
        if person_id:
            endpoint = f"people/(id:{person_id})"
        else:
            endpoint = "me"

        params = {
            "projection": "(id,firstName,lastName,profilePicture,headline,vanityName)"
        }

        data = self._make_request(endpoint, params=params)

        # 名前のローカライズ処理
        first_name = ""
        last_name = ""
        if data.get("firstName"):
            localized = data["firstName"].get("localized", {})
            first_name = list(localized.values())[0] if localized else ""
        if data.get("lastName"):
            localized = data["lastName"].get("localized", {})
            last_name = list(localized.values())[0] if localized else ""

        return LinkedInProfile(
            id=data.get("id", ""),
            vanity_name=data.get("vanityName"),
            first_name=first_name,
            last_name=last_name,
            headline=data.get("headline"),
        )

    def get_company_page(self, organization_id: str) -> LinkedInCompanyPage:
        """企業ページ情報を取得

        Args:
            organization_id: 組織ID

        Returns:
            LinkedInCompanyPage: 企業ページ情報
        """
        params = {
            "projection": "(id,name,vanityName,description,websiteUrl,logoV2,coverPhotoV2)"
        }

        data = self._make_request(
            f"organizations/{organization_id}",
            params=params
        )

        # 名前のローカライズ処理
        name = ""
        if data.get("name"):
            localized = data["name"].get("localized", {})
            name = list(localized.values())[0] if localized else ""

        description = ""
        if data.get("description"):
            localized = data["description"].get("localized", {})
            description = list(localized.values())[0] if localized else ""

        return LinkedInCompanyPage(
            id=data.get("id", ""),
            name=name,
            vanity_name=data.get("vanityName"),
            description=description,
            website_url=data.get("websiteUrl"),
        )

    def get_posts(
        self,
        author_id: str,
        max_results: int = 50,
        start: int = 0,
    ) -> tuple[list[LinkedInPost], int]:
        """投稿リストを取得

        Args:
            author_id: 投稿者ID（個人のURN: urn:li:person:xxx または企業のURN: urn:li:organization:xxx）
            max_results: 取得件数（最大50）
            start: 開始位置

        Returns:
            tuple[list[LinkedInPost], int]:
                - 投稿リスト
                - 総件数
        """
        # URN形式かどうかチェック
        if not author_id.startswith("urn:li:"):
            author_id = f"urn:li:person:{author_id}"

        params = {
            "q": "author",
            "author": author_id,
            "count": min(max_results, 50),
            "start": start,
        }

        data = self._make_request("posts", params=params, use_rest_api=True)

        posts: list[LinkedInPost] = []
        for item in data.get("elements", []):
            post = self._parse_post(item)
            posts.append(post)

        total_count = data.get("paging", {}).get("total", len(posts))
        logger.info(f"{len(posts)}件のLinkedIn投稿を取得しました")

        return posts, total_count

    def _parse_post(self, item: dict) -> LinkedInPost:
        """API レスポンスから投稿オブジェクトを生成

        Args:
            item: LinkedIn API の投稿アイテム

        Returns:
            LinkedInPost: 投稿オブジェクト
        """
        # 作成日時の変換（ミリ秒）
        created_at = datetime.now(UTC)
        if item.get("createdAt"):
            created_at = datetime.fromtimestamp(item["createdAt"] / 1000, tz=UTC)

        # テキスト取得
        text = ""
        if item.get("commentary"):
            text = item["commentary"]
        elif item.get("specificContent", {}).get("com.linkedin.ugc.ShareContent", {}).get("shareCommentary", {}).get("text"):
            text = item["specificContent"]["com.linkedin.ugc.ShareContent"]["shareCommentary"]["text"]

        # メディアタイプ判定
        media_type = "NONE"
        media_url = None
        article_url = None
        content = item.get("content", {})
        if content.get("media"):
            media_type = "IMAGE"  # または VIDEO
        elif content.get("article"):
            media_type = "ARTICLE"
            article_url = content["article"].get("source")

        # ハッシュタグ抽出
        hashtags = self._extract_hashtags(text)

        # エンゲージメント（別途APIで取得が必要な場合もある）
        social_detail = item.get("socialDetail", {})
        likes = social_detail.get("totalShareStatistics", {}).get("likeCount", 0)
        comments = social_detail.get("totalShareStatistics", {}).get("commentCount", 0)
        shares = social_detail.get("totalShareStatistics", {}).get("shareCount", 0)

        return LinkedInPost(
            id=item.get("id", ""),
            text=text,
            created_at=created_at,
            visibility=item.get("visibility", "PUBLIC"),
            media_type=media_type,
            media_url=media_url,
            article_url=article_url,
            likes=likes,
            comments=comments,
            shares=shares,
            hashtags=hashtags,
            author_id=item.get("author"),
        )

    def get_all_posts(
        self,
        author_id: str,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> list[LinkedInPost]:
        """全投稿を取得（ページネーション対応）

        Args:
            author_id: 投稿者ID
            limit: 取得上限
            since: この日時以降の投稿のみ取得

        Returns:
            list[LinkedInPost]: 投稿リスト
        """
        all_posts: list[LinkedInPost] = []
        start = 0

        while len(all_posts) < limit:
            remaining = limit - len(all_posts)
            batch_size = min(50, remaining)

            posts, total = self.get_posts(
                author_id=author_id,
                max_results=batch_size,
                start=start,
            )

            # 日時フィルタリング
            if since:
                posts = [p for p in posts if p.created_at >= since]

            all_posts.extend(posts)
            start += batch_size

            # フィルタ後のリストが空、または全件取得済み
            if not posts or start >= total:
                break

        logger.info(f"合計{len(all_posts)}件のLinkedIn投稿を取得しました")
        return all_posts[:limit]

    def get_post_analytics(
        self,
        post_id: str,
    ) -> dict:
        """投稿の分析データを取得

        Args:
            post_id: 投稿ID

        Returns:
            dict: 分析データ
        """
        params = {
            "q": "share",
            "share": post_id,
        }

        data = self._make_request("organizationalEntityShareStatistics", params=params)

        elements = data.get("elements", [])
        if not elements:
            return {}

        stats = elements[0].get("totalShareStatistics", {})
        return {
            "impressions": stats.get("impressionCount", 0),
            "unique_impressions": stats.get("uniqueImpressionsCount", 0),
            "clicks": stats.get("clickCount", 0),
            "likes": stats.get("likeCount", 0),
            "comments": stats.get("commentCount", 0),
            "shares": stats.get("shareCount", 0),
            "engagement": stats.get("engagement", 0),
        }

    def get_follower_statistics(
        self,
        organization_id: str,
    ) -> LinkedInDemographics:
        """フォロワー統計を取得（企業ページ用）

        Args:
            organization_id: 組織ID

        Returns:
            LinkedInDemographics: フォロワー属性
        """
        params = {
            "q": "organizationalEntity",
            "organizationalEntity": f"urn:li:organization:{organization_id}",
        }

        data = self._make_request("organizationalEntityFollowerStatistics", params=params)

        elements = data.get("elements", [])
        if not elements:
            return LinkedInDemographics()

        follower_stats = elements[0].get("followerCountsByAssociationType", [])

        # 属性別集計
        by_industry = {}
        by_function = {}
        by_seniority = {}
        by_company_size = {}
        by_location = {}

        for stat in follower_stats:
            # 各属性の集計処理
            pass  # 実際のAPIレスポンス形式に合わせて実装

        return LinkedInDemographics(
            by_industry=by_industry,
            by_job_function=by_function,
            by_seniority=by_seniority,
            by_company_size=by_company_size,
            by_location=by_location,
        )

    def calculate_engagement_metrics(
        self,
        posts: list[LinkedInPost],
    ) -> LinkedInEngagementMetrics:
        """エンゲージメント指標を計算

        Args:
            posts: 投稿リスト

        Returns:
            LinkedInEngagementMetrics: エンゲージメント指標
        """
        if not posts:
            return LinkedInEngagementMetrics()

        total_impressions = sum(p.impressions or 0 for p in posts)
        total_unique_impressions = sum(p.unique_impressions or 0 for p in posts)
        total_likes = sum(p.likes for p in posts)
        total_comments = sum(p.comments for p in posts)
        total_shares = sum(p.shares for p in posts)
        total_clicks = sum(p.clicks or 0 for p in posts)

        post_count = len(posts)
        total_engagement = total_likes + total_comments + total_shares + total_clicks

        # エンゲージメント率
        engagement_rate = 0.0
        if total_impressions > 0:
            engagement_rate = (total_engagement / total_impressions) * 100

        # CTR
        ctr = 0.0
        if total_impressions > 0:
            ctr = (total_clicks / total_impressions) * 100

        # バイラリティ率
        virality_rate = 0.0
        if total_impressions > 0:
            virality_rate = (total_shares / total_impressions) * 100

        return LinkedInEngagementMetrics(
            total_impressions=total_impressions,
            total_unique_impressions=total_unique_impressions,
            total_likes=total_likes,
            total_comments=total_comments,
            total_shares=total_shares,
            total_clicks=total_clicks,
            engagement_rate=round(engagement_rate, 4),
            avg_likes_per_post=round(total_likes / post_count, 2),
            avg_comments_per_post=round(total_comments / post_count, 2),
            avg_shares_per_post=round(total_shares / post_count, 2),
            avg_clicks_per_post=round(total_clicks / post_count, 2),
            click_through_rate=round(ctr, 4),
            virality_rate=round(virality_rate, 4),
        )

    @staticmethod
    def _extract_hashtags(text: str) -> list[str]:
        """テキストからハッシュタグを抽出

        Args:
            text: 投稿テキスト

        Returns:
            list[str]: ハッシュタグリスト（#なし）
        """
        if not text:
            return []
        import re
        pattern = r"#([^\s#]+)"
        matches = re.findall(pattern, text)
        return [m.lower() for m in matches]

    def close(self) -> None:
        """HTTPクライアントをクローズ"""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self) -> "LinkedInClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


def load_sample_linkedin_posts(filepath: str) -> list[LinkedInPost]:
    """サンプルJSONファイルからLinkedIn投稿を読み込む（テスト用）

    Args:
        filepath: JSONファイルパス

    Returns:
        list[LinkedInPost]: 投稿リスト
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    posts = []
    for item in data:
        # created_atの変換
        if isinstance(item.get("created_at"), str):
            item["created_at"] = datetime.fromisoformat(
                item["created_at"].replace("Z", "+00:00")
            )
        posts.append(LinkedInPost(**item))

    return posts
