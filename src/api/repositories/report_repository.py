"""
レポートリポジトリ
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db.models import Report


class ReportRepository:
    """レポートCRUD操作"""

    def __init__(self, db: Session):
        """
        Args:
            db: データベースセッション
        """
        self.db = db

    def create(
        self,
        user_id: str,
        report_type: str,
        platform: str,
        period_start: datetime,
        period_end: datetime,
        html_url: Optional[str] = None,
    ) -> Report:
        """
        レポート作成

        Args:
            user_id: ユーザーID
            report_type: レポートタイプ（weekly, monthly, custom）
            platform: プラットフォーム
            period_start: 期間開始
            period_end: 期間終了
            html_url: HTMLレポートURL

        Returns:
            作成されたレポート
        """
        report = Report(
            user_id=user_id,
            report_type=report_type,
            platform=platform,
            period_start=period_start,
            period_end=period_end,
            html_url=html_url,
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_by_id(self, report_id: str) -> Optional[Report]:
        """
        IDでレポート取得

        Args:
            report_id: レポートID

        Returns:
            レポート（存在しない場合None）
        """
        return self.db.get(Report, report_id)

    def get_by_user_id(
        self,
        user_id: str,
        report_type: Optional[str] = None,
        platform: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Report]:
        """
        ユーザーIDでレポート一覧取得

        Args:
            user_id: ユーザーID
            report_type: レポートタイプ（絞り込み用）
            platform: プラットフォーム（絞り込み用）
            limit: 取得件数
            offset: オフセット

        Returns:
            レポートリスト
        """
        stmt = select(Report).where(Report.user_id == user_id)

        if report_type:
            stmt = stmt.where(Report.report_type == report_type)
        if platform:
            stmt = stmt.where(Report.platform == platform)

        stmt = stmt.order_by(Report.created_at.desc()).limit(limit).offset(offset)

        return list(self.db.scalars(stmt).all())

    def count_by_user_id(
        self,
        user_id: str,
        report_type: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> int:
        """
        ユーザーIDでレポート数取得

        Args:
            user_id: ユーザーID
            report_type: レポートタイプ（絞り込み用）
            platform: プラットフォーム（絞り込み用）

        Returns:
            レポート数
        """
        stmt = select(func.count()).select_from(Report).where(Report.user_id == user_id)

        if report_type:
            stmt = stmt.where(Report.report_type == report_type)
        if platform:
            stmt = stmt.where(Report.platform == platform)

        return self.db.scalar(stmt) or 0

    def update_html_url(self, report: Report, html_url: str) -> Report:
        """
        HTMLレポートURL更新

        Args:
            report: 対象レポート
            html_url: 新URL

        Returns:
            更新されたレポート
        """
        report.html_url = html_url
        self.db.commit()
        self.db.refresh(report)
        return report

    def delete(self, report: Report) -> None:
        """
        レポート削除

        Args:
            report: 削除対象レポート
        """
        self.db.delete(report)
        self.db.commit()
