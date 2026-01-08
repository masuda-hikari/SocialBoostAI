"""
ユーザーリポジトリ
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import User


class UserRepository:
    """ユーザーCRUD操作"""

    def __init__(self, db: Session):
        """
        Args:
            db: データベースセッション
        """
        self.db = db

    def create(
        self,
        email: str,
        username: str,
        password_hash: str,
        role: str = "free",
    ) -> User:
        """
        ユーザー作成

        Args:
            email: メールアドレス
            username: ユーザー名
            password_hash: パスワードハッシュ
            role: ロール（デフォルト: free）

        Returns:
            作成されたユーザー
        """
        user = User(
            email=email,
            username=username,
            password_hash=password_hash,
            role=role,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_id(self, user_id: str) -> Optional[User]:
        """
        IDでユーザー取得

        Args:
            user_id: ユーザーID

        Returns:
            ユーザー（存在しない場合None）
        """
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        """
        メールアドレスでユーザー取得

        Args:
            email: メールアドレス

        Returns:
            ユーザー（存在しない場合None）
        """
        stmt = select(User).where(User.email == email)
        return self.db.scalar(stmt)

    def update(
        self,
        user: User,
        username: Optional[str] = None,
        email: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> User:
        """
        ユーザー更新

        Args:
            user: 更新対象ユーザー
            username: 新ユーザー名
            email: 新メールアドレス
            role: 新ロール
            is_active: アクティブ状態

        Returns:
            更新されたユーザー
        """
        if username is not None:
            user.username = username
        if email is not None:
            user.email = email
        if role is not None:
            user.role = role
        if is_active is not None:
            user.is_active = is_active

        user.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_password(self, user: User, password_hash: str) -> User:
        """
        パスワード更新

        Args:
            user: 対象ユーザー
            password_hash: 新パスワードハッシュ

        Returns:
            更新されたユーザー
        """
        user.password_hash = password_hash
        user.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user: User) -> None:
        """
        ユーザー削除

        Args:
            user: 削除対象ユーザー
        """
        self.db.delete(user)
        self.db.commit()

    def deactivate(self, user: User) -> User:
        """
        ユーザー無効化

        Args:
            user: 対象ユーザー

        Returns:
            無効化されたユーザー
        """
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(user)
        return user
