"""
クロスプラットフォーム比較リポジトリ
"""

import json
from datetime import datetime
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..db.models import CrossPlatformComparison as ComparisonModel


class CrossPlatformComparisonRepository:
    """クロスプラットフォーム比較リポジトリ"""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: str,
        period_start: datetime,
        period_end: datetime,
        platforms_analyzed: list[str],
        twitter_analysis_id: Optional[str] = None,
        instagram_analysis_id: Optional[str] = None,
        twitter_performance: Optional[dict] = None,
        instagram_performance: Optional[dict] = None,
        comparison_items: list[dict] = [],
        overall_winner: Optional[str] = None,
        cross_platform_insights: list[str] = [],
        strategic_recommendations: list[str] = [],
        synergy_opportunities: list[str] = [],
    ) -> ComparisonModel:
        """比較結果を作成"""
        comparison = ComparisonModel(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            platforms_analyzed=json.dumps(platforms_analyzed),
            twitter_analysis_id=twitter_analysis_id,
            instagram_analysis_id=instagram_analysis_id,
            twitter_performance=(
                json.dumps(twitter_performance) if twitter_performance else None
            ),
            instagram_performance=(
                json.dumps(instagram_performance) if instagram_performance else None
            ),
            comparison_items=json.dumps(comparison_items),
            overall_winner=overall_winner,
            cross_platform_insights=json.dumps(cross_platform_insights),
            strategic_recommendations=json.dumps(strategic_recommendations),
            synergy_opportunities=json.dumps(synergy_opportunities),
        )
        self.db.add(comparison)
        self.db.commit()
        self.db.refresh(comparison)
        return comparison

    def get_by_id(self, comparison_id: str) -> Optional[ComparisonModel]:
        """IDで取得"""
        return (
            self.db.query(ComparisonModel)
            .filter(ComparisonModel.id == comparison_id)
            .first()
        )

    def get_by_user_id(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ComparisonModel]:
        """ユーザーIDで一覧取得"""
        return (
            self.db.query(ComparisonModel)
            .filter(ComparisonModel.user_id == user_id)
            .order_by(desc(ComparisonModel.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

    def count_by_user_id(self, user_id: str) -> int:
        """ユーザーIDで件数取得"""
        return (
            self.db.query(ComparisonModel)
            .filter(ComparisonModel.user_id == user_id)
            .count()
        )

    def delete(self, comparison_id: str) -> bool:
        """削除"""
        comparison = self.get_by_id(comparison_id)
        if not comparison:
            return False
        self.db.delete(comparison)
        self.db.commit()
        return True
