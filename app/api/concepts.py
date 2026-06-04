from datetime import UTC, datetime
from difflib import ndiff
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_optional_current_user
from app.db.session import get_db
from app.models import Concept, Insight, User
from app.schemas import (
    CalendarDay,
    ConceptCreate,
    ConceptRead,
    ConceptUpdate,
    DiffResponse,
    InsightCreate,
    InsightRead,
    InsightUpdate,
    InsightWithPrevious,
    SharePosterPayload,
    UserRead,
    UserUpdate,
)
from app.services.content_safety import ContentSafetyService

router = APIRouter(prefix="/api", tags=["mindring"])
DbDep = Annotated[Session, Depends(get_db)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
OptionalCurrentUserDep = Annotated[User | None, Depends(get_optional_current_user)]


def _split_tags(tags: str | None) -> list[str]:
    if not tags:
        return []
    return [tag for tag in tags.split(",") if tag]


def _insight_to_read(insight: Insight, db: Session) -> InsightRead:
    author = db.get(User, insight.author_id)
    return InsightRead(
        id=insight.id,
        concept_id=insight.concept_id,
        author_id=insight.author_id,
        author_nickname=author.nickname if author else None,
        author_avatar_url=author.avatar_url if author else None,
        content=insight.content,
        mood=insight.mood,
        tags=_split_tags(insight.tags),
        is_shared=insight.is_shared,
        previous_insight_id=insight.previous_insight_id,
        occurred_at=insight.occurred_at,
        created_at=insight.created_at,
        updated_at=insight.updated_at,
    )


def _can_access_insight(insight: Insight, user: User | None) -> bool:
    if user is None:
        return insight.is_shared
    return insight.is_shared or insight.author_id == user.id


def _get_insight_or_404(db: Session, insight_id: int) -> Insight:
    insight = db.get(Insight, insight_id)
    if insight is None:
        raise HTTPException(status_code=404, detail="Insight not found")
    return insight


def _assert_insight_owner(insight: Insight, user: User) -> None:
    if insight.author_id != user.id:
        raise HTTPException(status_code=403, detail="Only the insight author can modify it")


def _get_concept_or_404(db: Session, concept_id: int) -> Concept:
    concept = db.get(Concept, concept_id)
    if concept is None:
        raise HTTPException(status_code=404, detail="Concept not found")
    return concept


def _assert_concept_owner(concept: Concept, user: User) -> None:
    if concept.creator_id != user.id:
        raise HTTPException(status_code=403, detail="Only the concept creator can update it")


@router.get("/users/me", response_model=UserRead)
def get_current_user_info(current_user: CurrentUserDep) -> User:
    return current_user


@router.patch("/users/me", response_model=UserRead)
def update_current_user(
    payload: UserUpdate, 
    db: DbDep, 
    current_user: CurrentUserDep
) -> User:
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "birth_date" and isinstance(value, str):
            from datetime import datetime
            try:
                value = datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                try:
                    value = datetime.strptime(value, "%Y-%m").date()
                except ValueError:
                    try:
                        value = datetime.strptime(value, "%Y").date()
                    except ValueError:
                        raise HTTPException(
                            status_code=422, 
                            detail="Invalid date format. Use YYYY-MM-DD, YYYY-MM, or YYYY"
                        )
        setattr(current_user, key, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/concepts", response_model=ConceptRead, status_code=status.HTTP_201_CREATED)
def create_concept(payload: ConceptCreate, db: DbDep, current_user: CurrentUserDep) -> Concept:
    # 检查概念名称是否已存在
    existing_concept = db.execute(
        select(Concept).where(Concept.name == payload.name.strip())
    ).scalar_one_or_none()
    if existing_concept:
        raise HTTPException(status_code=409, detail="该概念已存在")
    
    concept = Concept(
        name=payload.name.strip(),
        description=payload.description,
        creator_id=current_user.id,
    )
    db.add(concept)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="该概念已存在"
        ) from exc
    db.refresh(concept)
    return concept


@router.get("/concepts", response_model=list[ConceptRead])
def search_concepts(
    db: DbDep,
    current_user: CurrentUserDep,
    q: str | None = Query(default=None, description="Search by concept name or description"),
    creator_id: int | None = Query(default=None, description="Optional owner filter"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[Concept]:
    statement = select(Concept)
    if q:
        like = f"%{q}%"
        statement = statement.where(or_(Concept.name.like(like), Concept.description.like(like)))
    if creator_id:
        statement = statement.where(Concept.creator_id == creator_id)
    else:
        # 默认只看自己的
        statement = statement.where(Concept.creator_id == current_user.id)
    statement = (
        statement.order_by(Concept.is_pinned.desc(), Concept.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(statement))


@router.get("/concepts/all", response_model=list[ConceptRead])
def get_all_concepts(
    db: DbDep,
    current_user: OptionalCurrentUserDep,
    q: str | None = Query(default=None, description="Search by concept name or description"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[Concept]:
    # 广场页面，显示所有概念
    statement = select(Concept)
    if q:
        like = f"%{q}%"
        statement = statement.where(or_(Concept.name.like(like), Concept.description.like(like)))
    statement = (
        statement.order_by(Concept.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(statement))


@router.get("/concepts/{concept_id}", response_model=ConceptRead)
def get_concept(concept_id: int, db: DbDep, current_user: OptionalCurrentUserDep) -> Concept:
    return _get_concept_or_404(db, concept_id)


@router.patch("/concepts/{concept_id}", response_model=ConceptRead)
def update_concept(
    concept_id: int, payload: ConceptUpdate, db: DbDep, current_user: CurrentUserDep
) -> Concept:
    concept = _get_concept_or_404(db, concept_id)
    _assert_concept_owner(concept, current_user)
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(concept, key, value)
    db.commit()
    db.refresh(concept)
    return concept


@router.post("/insights", response_model=InsightWithPrevious, status_code=status.HTTP_201_CREATED)
def create_insight(
    payload: InsightCreate, db: DbDep, current_user: CurrentUserDep
) -> InsightWithPrevious:
    concept = _get_concept_or_404(db, payload.concept_id)

    safety = ContentSafetyService().check_text(payload.content)
    if not safety.allowed:
        raise HTTPException(status_code=422, detail=f"Content safety check failed: {safety.reason}")

    previous_id = payload.previous_insight_id
    if previous_id is None:
        previous_id = db.scalar(
            select(Insight.id)
            .where(Insight.concept_id == payload.concept_id, Insight.author_id == current_user.id)
            .order_by(Insight.occurred_at.desc(), Insight.id.desc())
            .limit(1)
        )
    else:
        previous = db.get(Insight, previous_id)
        if previous is None or previous.author_id != current_user.id:
            raise HTTPException(status_code=404, detail="Previous insight not found")

    insight = Insight(
        concept_id=payload.concept_id,
        author_id=current_user.id,
        content=payload.content,
        mood=payload.mood,
        tags=",".join(tag.strip() for tag in payload.tags if tag.strip()) or None,
        is_shared=payload.is_shared,
        previous_insight_id=previous_id,
        occurred_at=payload.occurred_at or datetime.now(UTC),
    )
    db.add(insight)
    concept.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(insight)
    previous = db.get(Insight, previous_id) if previous_id else None
    return InsightWithPrevious(
        **_insight_to_read(insight, db).model_dump(),
        previous_insight=_insight_to_read(previous, db) if previous else None,
    )


@router.get("/concepts/{concept_id}/insights", response_model=list[InsightRead])
def list_concept_insights(
    concept_id: int,
    db: DbDep,
    current_user: OptionalCurrentUserDep,
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    author_id: int | None = None,
    tag: str | None = None,
    only_mine: bool = Query(default=True, description="Only show insights from current viewer"),
) -> list[InsightRead]:
    _get_concept_or_404(db, concept_id)
    statement = select(Insight).where(Insight.concept_id == concept_id)
    
    # 应用过滤逻辑
    if only_mine:
        if current_user is None:
            # 未登录用户只看共享的
            statement = statement.where(Insight.is_shared == True)
        else:
            # 已登录用户只看自己的
            statement = statement.where(Insight.author_id == current_user.id)
    else:
        if current_user is None:
            # 未登录用户只看共享的
            statement = statement.where(Insight.is_shared == True)
        else:
            # 已登录用户显示自己的 + 其他人共享的
            access_filter = (Insight.author_id == current_user.id) | (Insight.is_shared == True)
            statement = statement.where(access_filter)
            if author_id:
                statement = statement.where(Insight.author_id == author_id)
    
    if tag:
        statement = statement.where(Insight.tags.like(f"%{tag}%"))
    ordering = Insight.occurred_at.asc() if order == "asc" else Insight.occurred_at.desc()
    statement = statement.order_by(ordering)
    return [_insight_to_read(insight, db) for insight in db.scalars(statement)]


@router.get("/concepts/{concept_id}/timeline", response_model=list[InsightRead])
def get_timeline(
    concept_id: int,
    db: DbDep,
    current_user: OptionalCurrentUserDep,
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
    only_mine: bool = Query(default=True, description="Only show insights from current viewer"),
) -> list[InsightRead]:
    return list_concept_insights(
        concept_id=concept_id, order=order, db=db, current_user=current_user, only_mine=only_mine
    )


@router.get("/insights/{insight_id}", response_model=InsightRead)
def get_insight(
    insight_id: int,
    db: DbDep,
    current_user: OptionalCurrentUserDep,
) -> InsightRead:
    insight = _get_insight_or_404(db, insight_id)
    if not _can_access_insight(insight, current_user):
        raise HTTPException(status_code=403, detail="No access to this insight")
    return _insight_to_read(insight, db)


@router.patch("/insights/{insight_id}", response_model=InsightRead)
def update_insight(
    insight_id: int,
    payload: InsightUpdate,
    db: DbDep,
    current_user: CurrentUserDep,
) -> InsightRead:
    insight = _get_insight_or_404(db, insight_id)
    _assert_insight_owner(insight, current_user)
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "tags":
            # tags 需要转换为逗号分隔的字符串
            setattr(insight, "tags", ",".join(value) if value else None)
        else:
            setattr(insight, key, value)
    db.commit()
    db.refresh(insight)
    return _insight_to_read(insight, db)


@router.delete("/insights/{insight_id}")
def delete_insight(
    insight_id: int,
    db: DbDep,
    current_user: CurrentUserDep,
):
    insight = _get_insight_or_404(db, insight_id)
    _assert_insight_owner(insight, current_user)
    db.delete(insight)
    db.commit()
    return {"detail": "Insight deleted successfully"}


@router.get("/insights/diff", response_model=DiffResponse)
def diff_insights(
    left_id: int, right_id: int, db: DbDep, current_user: CurrentUserDep
) -> DiffResponse:
    left = db.get(Insight, left_id)
    right = db.get(Insight, right_id)
    if left is None or right is None:
        raise HTTPException(status_code=404, detail="Insight not found")
    if left.concept_id != right.concept_id:
        raise HTTPException(status_code=400, detail="Insights belong to different concepts")
    if not _can_access_insight(left, current_user) or not _can_access_insight(right, current_user):
        raise HTTPException(status_code=403, detail="No access to one of the insights")

    diff = list(ndiff(left.content.splitlines(), right.content.splitlines()))
    return DiffResponse(
        left=_insight_to_read(left, db),
        right=_insight_to_read(right, db),
        added_lines=[line[2:] for line in diff if line.startswith("+ ")],
        removed_lines=[line[2:] for line in diff if line.startswith("- ")],
    )


@router.get("/calendar", response_model=list[CalendarDay])
def get_calendar(db: DbDep, current_user: CurrentUserDep) -> list[CalendarDay]:
    rows = db.execute(
        select(func.date(Insight.occurred_at), func.count(Insight.id))
        .where(Insight.author_id == current_user.id)
        .group_by(func.date(Insight.occurred_at))
        .order_by(func.date(Insight.occurred_at).asc())
    ).all()
    return [CalendarDay(date=str(day), count=count) for day, count in rows]


@router.post("/share-posters")
def create_share_poster(payload: SharePosterPayload, current_user: CurrentUserDep) -> dict[str, str]:
    # MVP returns structured poster copy; mini-program can render it as a canvas/card.
    title = f"我对「{payload.concept_name}」的新一圈年轮"
    subtitle = f"时间跨度：{payload.time_span}"
    return {"title": title, "subtitle": subtitle, "content": payload.insight_content[:180]}
