"""
AIコンテンツ生成API Router - v1.6
"""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status

from ..dependencies import CurrentUser, DbSession
from ..schemas import (
    ABTestResponse,
    ABTestVariationRequest,
    ContentCalendarItemResponse,
    ContentCalendarRequest,
    ContentCalendarResponse,
    ContentGenerationRequest,
    ContentGenerationSummary,
    ContentPlatformType,
    ContentRewriteRequest,
    ContentToneEnum,
    ContentTypeEnum,
    ContentVariationResponse,
    GeneratedContentResponse,
    PaginatedResponse,
    TrendingContentRequest,
    TrendingContentResponse,
)
from ...ai_content_generator import (
    AIContentGenerator,
    ABTestRequest,
    ContentCalendarRequest as CalendarRequest,
    ContentGenerationRequest as GenRequest,
    ContentGoal,
    ContentPlatform,
    ContentRewriteRequest as RewriteRequest,
    ContentTone,
    ContentType,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# 生成履歴のインメモリストレージ（本番環境ではDBに保存）
_generation_history: dict[str, list[dict]] = {}

# プラン別制限
PLAN_LIMITS = {
    "free": {"ai_generation_enabled": True, "advanced_features_enabled": False},
    "pro": {"ai_generation_enabled": True, "advanced_features_enabled": True},
    "business": {"ai_generation_enabled": True, "advanced_features_enabled": True},
    "enterprise": {"ai_generation_enabled": True, "advanced_features_enabled": True},
}


def _check_advanced_features_access(role: str) -> None:
    """高度なAI機能へのアクセス権をチェック"""
    limits = PLAN_LIMITS.get(role, PLAN_LIMITS["free"])
    if not limits.get("advanced_features_enabled", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この機能はProプラン以上でご利用いただけます",
        )


def _convert_platform(platform: ContentPlatformType) -> ContentPlatform:
    """APIスキーマからドメインモデルに変換"""
    return ContentPlatform(platform.value)


def _convert_tone(tone: ContentToneEnum) -> ContentTone:
    """APIスキーマからドメインモデルに変換"""
    return ContentTone(tone.value)


def _convert_content_type(content_type: ContentTypeEnum) -> ContentType:
    """APIスキーマからドメインモデルに変換"""
    return ContentType(content_type.value)


def _save_generation(user_id: str, data: dict) -> None:
    """生成履歴を保存"""
    if user_id not in _generation_history:
        _generation_history[user_id] = []
    _generation_history[user_id].append(data)
    # 最新100件のみ保持
    _generation_history[user_id] = _generation_history[user_id][-100:]


@router.post(
    "/generate",
    response_model=GeneratedContentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_content(
    request: ContentGenerationRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    """コンテンツを生成

    AIを使用して指定プラットフォーム向けのコンテンツを生成します。
    """
    try:
        generator = AIContentGenerator()

        # リクエストを変換
        gen_request = GenRequest(
            platform=_convert_platform(request.platform),
            content_type=_convert_content_type(request.content_type),
            topic=request.topic,
            keywords=request.keywords,
            tone=_convert_tone(request.tone),
            goal=ContentGoal(request.goal.value),
            reference_content=request.reference_content,
            target_audience=request.target_audience,
            include_hashtags=request.include_hashtags,
            include_cta=request.include_cta,
            max_length=request.max_length,
        )

        result = generator.generate_content(gen_request)

        # 履歴保存
        _save_generation(
            current_user.id,
            {
                "id": result.id,
                "type": "generate",
                "platform": request.platform.value,
                "content_type": request.content_type.value,
                "preview": result.main_text[:100] if result.main_text else "",
                "created_at": result.created_at.isoformat(),
            },
        )

        return GeneratedContentResponse(
            id=result.id,
            platform=request.platform,
            content_type=request.content_type,
            main_text=result.main_text,
            hashtags=result.hashtags,
            call_to_action=result.call_to_action,
            media_suggestion=result.media_suggestion,
            estimated_engagement=result.estimated_engagement,
            created_at=result.created_at,
        )

    except ValueError as e:
        logger.error(f"コンテンツ生成エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"コンテンツ生成エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="コンテンツ生成に失敗しました",
        )


@router.post(
    "/rewrite",
    response_model=GeneratedContentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def rewrite_content(
    request: ContentRewriteRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    """コンテンツを別プラットフォーム向けにリライト

    既存のコンテンツを別プラットフォーム向けに最適化します。
    """
    try:
        generator = AIContentGenerator()

        rewrite_request = RewriteRequest(
            original_content=request.original_content,
            source_platform=_convert_platform(request.source_platform),
            target_platform=_convert_platform(request.target_platform),
            preserve_hashtags=request.preserve_hashtags,
            tone=_convert_tone(request.tone) if request.tone else None,
        )

        result = generator.rewrite_for_platform(rewrite_request)

        # 履歴保存
        _save_generation(
            current_user.id,
            {
                "id": result.id,
                "type": "rewrite",
                "platform": request.target_platform.value,
                "content_type": "post",
                "preview": result.main_text[:100] if result.main_text else "",
                "created_at": result.created_at.isoformat(),
            },
        )

        return GeneratedContentResponse(
            id=result.id,
            platform=request.target_platform,
            content_type=ContentTypeEnum.POST,
            main_text=result.main_text,
            hashtags=result.hashtags,
            call_to_action=result.call_to_action,
            media_suggestion=result.media_suggestion,
            estimated_engagement=result.estimated_engagement,
            created_at=result.created_at,
        )

    except ValueError as e:
        logger.error(f"リライトエラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"リライトエラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="コンテンツリライトに失敗しました",
        )


@router.post(
    "/ab-test",
    response_model=ABTestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_ab_variations(
    request: ABTestVariationRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    """A/Bテスト用バリエーションを生成

    同じトピックについて複数のバリエーションを生成します。
    Pro以上のプランが必要です。
    """
    # プランチェック
    _check_advanced_features_access(current_user.role)

    try:
        generator = AIContentGenerator()

        ab_request = ABTestRequest(
            base_topic=request.base_topic,
            platform=_convert_platform(request.platform),
            variation_count=request.variation_count,
            tone=_convert_tone(request.tone),
        )

        variations = generator.generate_ab_variations(ab_request)

        result_id = f"ab_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        # 履歴保存
        _save_generation(
            current_user.id,
            {
                "id": result_id,
                "type": "ab_test",
                "platform": request.platform.value,
                "content_type": "ab_test",
                "preview": f"A/Bテスト: {request.base_topic[:50]}",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        return ABTestResponse(
            id=result_id,
            topic=request.base_topic,
            platform=request.platform,
            variations=[
                ContentVariationResponse(
                    version=v.version,
                    text=v.text,
                    hashtags=v.hashtags,
                    focus=v.focus,
                )
                for v in variations
            ],
            created_at=datetime.now(timezone.utc),
        )

    except ValueError as e:
        logger.error(f"A/Bテスト生成エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"A/Bテスト生成エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A/Bテストバリエーション生成に失敗しました",
        )


@router.post(
    "/calendar",
    response_model=ContentCalendarResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_content_calendar(
    request: ContentCalendarRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    """コンテンツカレンダーを生成

    指定期間の投稿カレンダーを自動生成します。
    Pro以上のプランが必要です。
    """
    # プランチェック
    _check_advanced_features_access(current_user.role)

    try:
        generator = AIContentGenerator()

        calendar_request = CalendarRequest(
            platforms=[_convert_platform(p) for p in request.platforms],
            days=request.days,
            posts_per_day=request.posts_per_day,
            topics=request.topics,
            tone=_convert_tone(request.tone),
            goal=ContentGoal(request.goal.value),
        )

        items = generator.generate_content_calendar(calendar_request)

        result_id = f"cal_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        now = datetime.now(timezone.utc)

        # 履歴保存
        _save_generation(
            current_user.id,
            {
                "id": result_id,
                "type": "calendar",
                "platform": ",".join([p.value for p in request.platforms]),
                "content_type": "calendar",
                "preview": f"{request.days}日間のカレンダー（{len(items)}件）",
                "created_at": now.isoformat(),
            },
        )

        return ContentCalendarResponse(
            id=result_id,
            user_id=current_user.id,
            period_start=now,
            period_end=now + timedelta(days=request.days),
            total_items=len(items),
            items=[
                ContentCalendarItemResponse(
                    scheduled_date=item.scheduled_date,
                    platform=ContentPlatformType(item.platform.value),
                    content_type=ContentTypeEnum(item.content_type.value),
                    topic=item.topic,
                    draft_content=item.draft_content,
                    hashtags=item.hashtags,
                    optimal_time=item.optimal_time,
                    rationale=item.rationale,
                )
                for item in items
            ],
            created_at=now,
        )

    except ValueError as e:
        logger.error(f"カレンダー生成エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"カレンダー生成エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="コンテンツカレンダー生成に失敗しました",
        )


@router.post(
    "/trending",
    response_model=TrendingContentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_trending_content(
    request: TrendingContentRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    """トレンドを活用したコンテンツを生成

    指定されたトレンドキーワードを活用したコンテンツを生成します。
    Pro以上のプランが必要です。
    """
    # プランチェック
    _check_advanced_features_access(current_user.role)

    try:
        generator = AIContentGenerator()

        results = generator.generate_trending_content(
            platform=_convert_platform(request.platform),
            trend_keywords=request.trend_keywords,
            brand_context=request.brand_context,
            tone=_convert_tone(request.tone),
        )

        result_id = f"trend_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        now = datetime.now(timezone.utc)

        # 履歴保存
        _save_generation(
            current_user.id,
            {
                "id": result_id,
                "type": "trending",
                "platform": request.platform.value,
                "content_type": "trending",
                "preview": f"トレンド: {', '.join(request.trend_keywords[:3])}",
                "created_at": now.isoformat(),
            },
        )

        return TrendingContentResponse(
            id=result_id,
            platform=request.platform,
            trend_keywords=request.trend_keywords,
            contents=[
                GeneratedContentResponse(
                    id=r.id,
                    platform=request.platform,
                    content_type=ContentTypeEnum.POST,
                    main_text=r.main_text,
                    hashtags=r.hashtags,
                    call_to_action=r.call_to_action,
                    media_suggestion=r.media_suggestion,
                    estimated_engagement=r.estimated_engagement,
                    created_at=r.created_at,
                )
                for r in results
            ],
            created_at=now,
        )

    except ValueError as e:
        logger.error(f"トレンドコンテンツ生成エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"トレンドコンテンツ生成エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="トレンドコンテンツ生成に失敗しました",
        )


@router.get(
    "/history",
    response_model=PaginatedResponse,
)
async def get_generation_history(
    current_user: CurrentUser,
    db: DbSession,
    page: int = 1,
    per_page: int = 20,
):
    """コンテンツ生成履歴を取得

    ユーザーのコンテンツ生成履歴を取得します。
    """
    user_id = current_user.id
    history = _generation_history.get(user_id, [])

    # 新しい順にソート
    history = sorted(history, key=lambda x: x.get("created_at", ""), reverse=True)

    # ページネーション
    total = len(history)
    start = (page - 1) * per_page
    end = start + per_page
    items = history[start:end]

    return PaginatedResponse(
        items=[
            ContentGenerationSummary(
                id=item["id"],
                user_id=user_id,
                platform=ContentPlatformType(item["platform"].split(",")[0]),
                content_type=item["content_type"],
                preview=item["preview"],
                created_at=datetime.fromisoformat(item["created_at"]),
            )
            for item in items
        ],
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page if total > 0 else 0,
    )


@router.delete(
    "/history/{generation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_generation_history(
    generation_id: str,
    current_user: CurrentUser,
    db: DbSession,
):
    """生成履歴を削除

    指定された生成履歴を削除します。
    """
    user_id = current_user.id
    history = _generation_history.get(user_id, [])

    original_len = len(history)
    _generation_history[user_id] = [h for h in history if h["id"] != generation_id]

    if len(_generation_history[user_id]) == original_len:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="生成履歴が見つかりません",
        )

    return None
