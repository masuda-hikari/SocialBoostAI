"""
分析リポジトリ
"""

import json
from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db.models import Analysis


class AnalysisRepository:
    """分析CRUD操作"""

    def __init__(self, db: Session):
        """
        Args:
            db: データベースセッション
        """
        self.db = db

    def create(
        self,
        user_id: str,
        platform: str,
        period_start: datetime,
        period_end: datetime,
        total_posts: int = 0,
        total_likes: int = 0,
        total_retweets: int = 0,
        engagement_rate: float = 0.0,
        best_hour: Optional[int] = None,
        top_hashtags: list[str] | None = None,
    ) -> Analysis:
        """
        分析作成

        Args:
            user_id: ユーザーID
            platform: プラットフォーム
            period_start: 分析期間開始
            period_end: 分析期間終了
            total_posts: 投稿数
            total_likes: いいね数
            total_retweets: リツイート数
            engagement_rate: エンゲージメント率
            best_hour: 最適投稿時間
            top_hashtags: トップハッシュタグ

        Returns:
            作成された分析
        """
        analysis = Analysis(
            user_id=user_id,
            platform=platform,
            period_start=period_start,
            period_end=period_end,
            total_posts=total_posts,
            total_likes=total_likes,
            total_retweets=total_retweets,
            engagement_rate=engagement_rate,
            best_hour=best_hour,
            top_hashtags=json.dumps(top_hashtags or []),
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def get_by_id(self, analysis_id: str) -> Optional[Analysis]:
        """
        IDで分析取得

        Args:
            analysis_id: 分析ID

        Returns:
            分析（存在しない場合None）
        """
        return self.db.get(Analysis, analysis_id)

    def get_by_user_id(
        self,
        user_id: str,
        platform: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Analysis]:
        """
        ユーザーIDで分析一覧取得

        Args:
            user_id: ユーザーID
            platform: プラットフォーム（絞り込み用）
            limit: 取得件数
            offset: オフセット

        Returns:
            分析リスト
        """
        stmt = select(Analysis).where(Analysis.user_id == user_id)

        if platform:
            stmt = stmt.where(Analysis.platform == platform)

        stmt = stmt.order_by(Analysis.created_at.desc()).limit(limit).offset(offset)

        return list(self.db.scalars(stmt).all())

    def count_by_user_id(
        self,
        user_id: str,
        platform: Optional[str] = None,
    ) -> int:
        """
        ユーザーIDで分析数取得

        Args:
            user_id: ユーザーID
            platform: プラットフォーム（絞り込み用）

        Returns:
            分析数
        """
        stmt = (
            select(func.count())
            .select_from(Analysis)
            .where(Analysis.user_id == user_id)
        )

        if platform:
            stmt = stmt.where(Analysis.platform == platform)

        return self.db.scalar(stmt) or 0

    def delete(self, analysis: Analysis) -> None:
        """
        分析削除

        Args:
            analysis: 削除対象分析
        """
        self.db.delete(analysis)
        self.db.commit()

    def get_hashtags(self, analysis: Analysis) -> list[str]:
        """
        ハッシュタグリスト取得

        Args:
            analysis: 分析

        Returns:
            ハッシュタグリスト
        """
        return json.loads(analysis.top_hashtags)

    def get_by_user_id_and_platform(
        self,
        user_id: str,
        platform: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Analysis]:
        """
        ユーザーIDとプラットフォームで分析一覧取得

        Args:
            user_id: ユーザーID
            platform: プラットフォーム
            limit: 取得件数
            offset: オフセット

        Returns:
            分析リスト
        """
        stmt = (
            select(Analysis)
            .where(Analysis.user_id == user_id)
            .where(Analysis.platform == platform)
            .order_by(Analysis.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        return list(self.db.scalars(stmt).all())

    def count_by_user_id_and_platform(
        self,
        user_id: str,
        platform: str,
    ) -> int:
        """
        ユーザーIDとプラットフォームで分析数取得

        Args:
            user_id: ユーザーID
            platform: プラットフォーム

        Returns:
            分析数
        """
        stmt = (
            select(func.count())
            .select_from(Analysis)
            .where(Analysis.user_id == user_id)
            .where(Analysis.platform == platform)
        )

        return self.db.scalar(stmt) or 0
