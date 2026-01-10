"""
スケジュール投稿APIルーター
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..db.base import get_db
from ..dependencies import get_current_user, require_plan
from ..db.models import User
from ..schedule.service import ScheduleService
from ..schemas import (
    BulkScheduleRequest,
    BulkScheduleResponse,
    ContentPlatformType,
    ScheduledPostCreate,
    ScheduledPostListResponse,
    ScheduledPostResponse,
    ScheduledPostStatus,
    ScheduledPostUpdate,
    ScheduleStatsResponse,
)

router = APIRouter(tags=["スケジュール投稿"])


@router.post(
    "",
    response_model=ScheduledPostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="スケジュール投稿を作成",
)
async def create_scheduled_post(
    request: ScheduledPostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_plan("pro")),  # Pro以上必須
) -> ScheduledPostResponse:
    """
    スケジュール投稿を作成します。

    - Pro以上のプランが必要です
    - 過去の時刻にはスケジュールできません
    """
    service = ScheduleService(db)
    try:
        return service.create_scheduled_post(current_user.id, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "",
    response_model=ScheduledPostListResponse,
    summary="スケジュール投稿一覧を取得",
)
async def list_scheduled_posts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    status_filter: Optional[ScheduledPostStatus] = Query(
        None, alias="status", description="ステータスでフィルタ"
    ),
    platform: Optional[ContentPlatformType] = Query(
        None, description="プラットフォームでフィルタ"
    ),
    page: int = Query(1, ge=1, description="ページ番号"),
    per_page: int = Query(20, ge=1, le=100, description="1ページあたりの件数"),
) -> ScheduledPostListResponse:
    """スケジュール投稿一覧を取得します。"""
    service = ScheduleService(db)
    status_str = status_filter.value if status_filter else None
    platform_str = platform.value if platform else None

    items, total, pages = service.list_scheduled_posts(
        user_id=current_user.id,
        status=status_str,
        platform=platform_str,
        page=page,
        per_page=per_page,
    )

    return ScheduledPostListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get(
    "/stats",
    response_model=ScheduleStatsResponse,
    summary="スケジュール統計を取得",
)
async def get_schedule_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScheduleStatsResponse:
    """スケジュール投稿の統計情報を取得します。"""
    service = ScheduleService(db)
    return service.get_stats(current_user.id)


@router.get(
    "/upcoming",
    response_model=list,
    summary="今後の投稿を取得",
)
async def get_upcoming_posts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    hours: int = Query(24, ge=1, le=168, description="何時間以内の投稿を取得するか"),
):
    """今後N時間以内にスケジュールされている投稿を取得します。"""
    service = ScheduleService(db)
    return service.get_upcoming_posts(current_user.id, hours)


@router.get(
    "/{post_id}",
    response_model=ScheduledPostResponse,
    summary="スケジュール投稿を取得",
)
async def get_scheduled_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScheduledPostResponse:
    """指定されたスケジュール投稿を取得します。"""
    service = ScheduleService(db)
    post = service.get_scheduled_post(post_id, current_user.id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="スケジュール投稿が見つかりません",
        )
    return post


@router.put(
    "/{post_id}",
    response_model=ScheduledPostResponse,
    summary="スケジュール投稿を更新",
)
async def update_scheduled_post(
    post_id: str,
    request: ScheduledPostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScheduledPostResponse:
    """
    スケジュール投稿を更新します。

    - 公開済み・キャンセル済みの投稿は更新できません
    - 過去の時刻にはスケジュールできません
    """
    service = ScheduleService(db)
    try:
        post = service.update_scheduled_post(post_id, current_user.id, request)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="スケジュール投稿が見つかりません",
            )
        return post
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{post_id}/cancel",
    response_model=ScheduledPostResponse,
    summary="スケジュール投稿をキャンセル",
)
async def cancel_scheduled_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScheduledPostResponse:
    """
    スケジュール投稿をキャンセルします。

    - 公開済み・キャンセル済みの投稿は変更できません
    """
    service = ScheduleService(db)
    try:
        post = service.cancel_scheduled_post(post_id, current_user.id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="スケジュール投稿が見つかりません",
            )
        return post
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="スケジュール投稿を削除",
)
async def delete_scheduled_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """スケジュール投稿を削除します。"""
    service = ScheduleService(db)
    if not service.delete_scheduled_post(post_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="スケジュール投稿が見つかりません",
        )


@router.post(
    "/bulk",
    response_model=BulkScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="一括スケジュール投稿を作成",
)
async def bulk_create_scheduled_posts(
    request: BulkScheduleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(require_plan("business")),  # Business以上必須
) -> BulkScheduleResponse:
    """
    複数のスケジュール投稿を一括で作成します。

    - Business以上のプランが必要です
    - 最大20件まで同時作成可能
    """
    service = ScheduleService(db)
    created, errors = service.bulk_create(current_user.id, request.posts)

    return BulkScheduleResponse(
        created=len(created),
        failed=len(errors),
        scheduled_posts=created,
        errors=errors,
    )
