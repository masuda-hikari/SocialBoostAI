"""
トークンリポジトリ
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..db.models import Token


class TokenRepository:
    """認証トークンCRUD操作"""

    def __init__(self, db: Session):
        """
        Args:
            db: データベースセッション
        """
        self.db = db

    def create(
        self,
        user_id: str,
        expire_hours: int = 24,
    ) -> Token:
        """
        トークン作成

        Args:
            user_id: ユーザーID
            expire_hours: 有効期間（時間）

        Returns:
            作成されたトークン
        """
        token = Token(
            token=secrets.token_urlsafe(32),
            user_id=user_id,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expire_hours),
        )
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def get_by_token(self, token_str: str) -> Optional[Token]:
        """
        トークン文字列で取得

        Args:
            token_str: トークン文字列

        Returns:
            トークン（存在しない場合None）
        """
        stmt = select(Token).where(Token.token == token_str)
        return self.db.scalar(stmt)

    def get_valid_token(self, token_str: str) -> Optional[Token]:
        """
        有効なトークンを取得

        Args:
            token_str: トークン文字列

        Returns:
            有効なトークン（期限切れ/存在しない場合None）
        """
        stmt = select(Token).where(
            Token.token == token_str,
            Token.expires_at > datetime.now(timezone.utc),
        )
        return self.db.scalar(stmt)

    def delete(self, token: Token) -> None:
        """
        トークン削除

        Args:
            token: 削除対象トークン
        """
        self.db.delete(token)
        self.db.commit()

    def delete_by_token_str(self, token_str: str) -> bool:
        """
        トークン文字列で削除

        Args:
            token_str: トークン文字列

        Returns:
            削除成功の場合True
        """
        stmt = delete(Token).where(Token.token == token_str)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount > 0

    def delete_by_user_id(self, user_id: str) -> int:
        """
        ユーザーIDで全トークン削除

        Args:
            user_id: ユーザーID

        Returns:
            削除されたトークン数
        """
        stmt = delete(Token).where(Token.user_id == user_id)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount

    def delete_expired(self) -> int:
        """
        期限切れトークンを一括削除

        Returns:
            削除されたトークン数
        """
        stmt = delete(Token).where(Token.expires_at < datetime.now(timezone.utc))
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount
