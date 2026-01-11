"""
管理者用APIエンドポイント

運用者向けの管理機能を提供
- ユーザー管理（一覧・詳細・更新・削除）
- システム統計（ユーザー数、プラン分布、収益）
- アクティビティログ
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from ..db.models import Analysis, Report, ScheduledPost, Subscription, User
from ..dependencies import AdminUser


router = APIRouter(prefix="/admin", tags=["admin"])


# ============================================================
# スキーマ定義
# ============================================================


class UserSummary(BaseModel):
    """ユーザーサマリー"""

    id: str
    email: str
    username: str
    role: str
    is_active: bool
    created_at: datetime
    analysis_count: int = 0
    report_count: int = 0
    scheduled_post_count: int = 0


class UserListResponse(BaseModel):
    """ユーザー一覧レスポンス"""

    users: list[UserSummary]
    total: int
    page: int
    per_page: int


class UserDetail(BaseModel):
    """ユーザー詳細"""

    id: str
    email: str
    username: str
    role: str
    is_active: bool
    stripe_customer_id: str | None
    created_at: datetime
    updated_at: datetime
    analysis_count: int = 0
    report_count: int = 0
    scheduled_post_count: int = 0
    subscription: dict | None = None


class UserUpdateRequest(BaseModel):
    """ユーザー更新リクエスト"""

    username: str | None = None
    role: str | None = Field(
        None, pattern="^(free|pro|business|enterprise|admin)$"
    )
    is_active: bool | None = None


class SystemStats(BaseModel):
    """システム統計"""

    total_users: int
    active_users: int
    inactive_users: int
    users_by_plan: dict[str, int]
    total_analyses: int
    total_reports: int
    total_scheduled_posts: int
    new_users_today: int
    new_users_this_week: int
    new_users_this_month: int


class RevenueStats(BaseModel):
    """収益統計"""

    active_subscriptions: int
    subscriptions_by_plan: dict[str, int]
    monthly_recurring_revenue_jpy: int
    churn_rate: float  # 解約率


class ActivityLogEntry(BaseModel):
    """アクティビティログエントリ"""

    type: str
    user_id: str
    username: str
    description: str
    timestamp: datetime


class ActivityLogResponse(BaseModel):
    """アクティビティログレスポンス"""

    entries: list[ActivityLogEntry]
    total: int


# ============================================================
# ユーザー管理
# ============================================================


@router.get("/users", response_model=UserListResponse)
async def list_users(
    admin: AdminUser,
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    role: str | None = Query(None),
    is_active: bool | None = Query(None),
    search: str | None = Query(None),
):
    """
    ユーザー一覧取得

    管理者のみアクセス可能
    """
    query = db.query(User)

    # フィルター
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    if search:
        query = query.filter(
            (User.email.ilike(f"%{search}%"))
            | (User.username.ilike(f"%{search}%"))
        )

    # 総数取得
    total = query.count()

    # ページネーション
    users = (
        query.order_by(User.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    # サマリー作成
    user_summaries = []
    for user in users:
        analysis_count = (
            db.query(func.count(Analysis.id))
            .filter(Analysis.user_id == user.id)
            .scalar()
            or 0
        )
        report_count = (
            db.query(func.count(Report.id))
            .filter(Report.user_id == user.id)
            .scalar()
            or 0
        )
        scheduled_count = (
            db.query(func.count(ScheduledPost.id))
            .filter(ScheduledPost.user_id == user.id)
            .scalar()
            or 0
        )

        user_summaries.append(
            UserSummary(
                id=user.id,
                email=user.email,
                username=user.username,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
                analysis_count=analysis_count,
                report_count=report_count,
                scheduled_post_count=scheduled_count,
            )
        )

    return UserListResponse(
        users=user_summaries,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/users/{user_id}", response_model=UserDetail)
async def get_user(
    user_id: str,
    admin: AdminUser,
    db: Annotated[Session, Depends(get_db)],
):
    """
    ユーザー詳細取得
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません",
        )

    # 統計取得
    analysis_count = (
        db.query(func.count(Analysis.id))
        .filter(Analysis.user_id == user.id)
        .scalar()
        or 0
    )
    report_count = (
        db.query(func.count(Report.id))
        .filter(Report.user_id == user.id)
        .scalar()
        or 0
    )
    scheduled_count = (
        db.query(func.count(ScheduledPost.id))
        .filter(ScheduledPost.user_id == user.id)
        .scalar()
        or 0
    )

    # サブスクリプション取得
    subscription = (
        db.query(Subscription)
        .filter(Subscription.user_id == user.id)
        .filter(Subscription.status == "active")
        .first()
    )
    subscription_dict = None
    if subscription:
        subscription_dict = {
            "id": subscription.id,
            "plan": subscription.plan,
            "status": subscription.status,
            "current_period_start": subscription.current_period_start.isoformat(),
            "current_period_end": subscription.current_period_end.isoformat(),
            "cancel_at_period_end": subscription.cancel_at_period_end,
        }

    return UserDetail(
        id=user.id,
        email=user.email,
        username=user.username,
        role=user.role,
        is_active=user.is_active,
        stripe_customer_id=user.stripe_customer_id,
        created_at=user.created_at,
        updated_at=user.updated_at,
        analysis_count=analysis_count,
        report_count=report_count,
        scheduled_post_count=scheduled_count,
        subscription=subscription_dict,
    )


@router.put("/users/{user_id}", response_model=UserDetail)
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    admin: AdminUser,
    db: Annotated[Session, Depends(get_db)],
):
    """
    ユーザー更新
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません",
        )

    # 更新
    if request.username is not None:
        user.username = request.username
    if request.role is not None:
        user.role = request.role
    if request.is_active is not None:
        user.is_active = request.is_active

    db.commit()
    db.refresh(user)

    # 詳細取得して返す
    return await get_user(user_id, admin, db)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin: AdminUser,
    db: Annotated[Session, Depends(get_db)],
):
    """
    ユーザー削除（論理削除）
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません",
        )

    # 自分自身は削除不可
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="自分自身を削除することはできません",
        )

    # 論理削除
    user.is_active = False
    db.commit()

    return {"message": "ユーザーを無効化しました"}


# ============================================================
# システム統計
# ============================================================


@router.get("/stats/system", response_model=SystemStats)
async def get_system_stats(
    admin: AdminUser,
    db: Annotated[Session, Depends(get_db)],
):
    """
    システム統計取得
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)

    # ユーザー統計
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = (
        db.query(func.count(User.id)).filter(User.is_active == True).scalar()
        or 0
    )
    inactive_users = total_users - active_users

    # プラン別ユーザー数
    plan_counts = (
        db.query(User.role, func.count(User.id))
        .filter(User.is_active == True)
        .group_by(User.role)
        .all()
    )
    users_by_plan = {plan: count for plan, count in plan_counts}

    # コンテンツ統計
    total_analyses = db.query(func.count(Analysis.id)).scalar() or 0
    total_reports = db.query(func.count(Report.id)).scalar() or 0
    total_scheduled = db.query(func.count(ScheduledPost.id)).scalar() or 0

    # 新規ユーザー数
    new_today = (
        db.query(func.count(User.id))
        .filter(User.created_at >= today_start)
        .scalar()
        or 0
    )
    new_week = (
        db.query(func.count(User.id))
        .filter(User.created_at >= week_start)
        .scalar()
        or 0
    )
    new_month = (
        db.query(func.count(User.id))
        .filter(User.created_at >= month_start)
        .scalar()
        or 0
    )

    return SystemStats(
        total_users=total_users,
        active_users=active_users,
        inactive_users=inactive_users,
        users_by_plan=users_by_plan,
        total_analyses=total_analyses,
        total_reports=total_reports,
        total_scheduled_posts=total_scheduled,
        new_users_today=new_today,
        new_users_this_week=new_week,
        new_users_this_month=new_month,
    )


@router.get("/stats/revenue", response_model=RevenueStats)
async def get_revenue_stats(
    admin: AdminUser,
    db: Annotated[Session, Depends(get_db)],
):
    """
    収益統計取得
    """
    # プラン別価格（円）
    plan_prices = {
        "free": 0,
        "pro": 1980,
        "business": 4980,
        "enterprise": 19800,  # 仮の値
    }

    # アクティブサブスクリプション
    active_subs = (
        db.query(Subscription)
        .filter(Subscription.status == "active")
        .all()
    )

    # プラン別カウント
    subs_by_plan: dict[str, int] = {}
    for sub in active_subs:
        plan = sub.plan.lower()
        subs_by_plan[plan] = subs_by_plan.get(plan, 0) + 1

    # MRR計算
    mrr = 0
    for plan, count in subs_by_plan.items():
        price = plan_prices.get(plan, 0)
        mrr += price * count

    # 解約率計算（過去30日）
    now = datetime.now(timezone.utc)
    month_ago = now - timedelta(days=30)

    canceled_count = (
        db.query(func.count(Subscription.id))
        .filter(Subscription.canceled_at >= month_ago)
        .scalar()
        or 0
    )

    # 解約率 = 解約数 / (アクティブ + 解約数)
    total_for_churn = len(active_subs) + canceled_count
    churn_rate = (canceled_count / total_for_churn * 100) if total_for_churn > 0 else 0.0

    return RevenueStats(
        active_subscriptions=len(active_subs),
        subscriptions_by_plan=subs_by_plan,
        monthly_recurring_revenue_jpy=mrr,
        churn_rate=round(churn_rate, 2),
    )


# ============================================================
# アクティビティログ
# ============================================================


@router.get("/activity", response_model=ActivityLogResponse)
async def get_activity_log(
    admin: AdminUser,
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
):
    """
    最近のアクティビティログ取得

    分析・レポート・スケジュール投稿の作成をログとして表示
    """
    entries: list[ActivityLogEntry] = []

    # 最近の分析
    analyses = (
        db.query(Analysis)
        .order_by(Analysis.created_at.desc())
        .limit(per_page)
        .all()
    )
    for a in analyses:
        user = db.query(User).filter(User.id == a.user_id).first()
        if user:
            entries.append(
                ActivityLogEntry(
                    type="analysis",
                    user_id=a.user_id,
                    username=user.username,
                    description=f"{a.platform}の分析を実行",
                    timestamp=a.created_at,
                )
            )

    # 最近のレポート
    reports = (
        db.query(Report)
        .order_by(Report.created_at.desc())
        .limit(per_page)
        .all()
    )
    for r in reports:
        user = db.query(User).filter(User.id == r.user_id).first()
        if user:
            entries.append(
                ActivityLogEntry(
                    type="report",
                    user_id=r.user_id,
                    username=user.username,
                    description=f"{r.report_type}レポートを生成",
                    timestamp=r.created_at,
                )
            )

    # 最近のスケジュール投稿
    scheduled = (
        db.query(ScheduledPost)
        .order_by(ScheduledPost.created_at.desc())
        .limit(per_page)
        .all()
    )
    for s in scheduled:
        user = db.query(User).filter(User.id == s.user_id).first()
        if user:
            entries.append(
                ActivityLogEntry(
                    type="scheduled_post",
                    user_id=s.user_id,
                    username=user.username,
                    description=f"{s.platform}への投稿をスケジュール",
                    timestamp=s.created_at,
                )
            )

    # 新規ユーザー
    users = (
        db.query(User)
        .order_by(User.created_at.desc())
        .limit(per_page)
        .all()
    )
    for u in users:
        entries.append(
            ActivityLogEntry(
                type="user_registration",
                user_id=u.id,
                username=u.username,
                description="アカウントを登録",
                timestamp=u.created_at,
            )
        )

    # 日時でソート
    entries.sort(key=lambda x: x.timestamp, reverse=True)

    # ページネーション
    total = len(entries)
    start = (page - 1) * per_page
    end = start + per_page
    paginated = entries[start:end]

    return ActivityLogResponse(
        entries=paginated,
        total=total,
    )


# ============================================================
# ユーティリティ
# ============================================================


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    admin: AdminUser,
    db: Annotated[Session, Depends(get_db)],
):
    """
    ユーザーパスワードをリセット（仮パスワード発行）

    実装注意: 本番ではメール送信を組み合わせる
    """
    import secrets

    from ..dependencies import hash_password

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ユーザーが見つかりません",
        )

    # 仮パスワード生成
    temp_password = secrets.token_urlsafe(12)
    user.password_hash = hash_password(temp_password)
    db.commit()

    return {
        "message": "パスワードをリセットしました",
        "temporary_password": temp_password,
        "note": "ユーザーにこのパスワードを安全に伝えてください",
    }
