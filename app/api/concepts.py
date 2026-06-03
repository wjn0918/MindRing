from datetime import UTC, datetime
from difflib import ndiff
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

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
    InsightWithPrevious,
    SharePosterPayload,
    UserCreate,
    UserRead,
)
from app.services.content_safety import ContentSafetyService

router = APIRouter(prefix="/api", tags=["mindring"])
DbDep = Annotated[Session, Depends(get_db)]


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
        previous_insight_id=insight.previous_insight_id,
        occurred_at=insight.occurred_at,
        created_at=insight.created_at,
        updated_at=insight.updated_at,
    )


def _ensure_user(db: Session, user_id: str, nickname: str | None = None) -> User:
    user = db.get(User, user_id)
    if user is None:
        user = User(id=user_id, nickname=nickname)
        db.add(user)
    elif nickname and not user.nickname:
        user.nickname = nickname
    return user


def _can_access_concept(concept: Concept, user_id: str | None) -> bool:
    return concept.is_shared or (user_id is not None and concept.creator_id == user_id)


def _get_accessible_concept(db: Session, concept_id: int, user_id: str | None) -> Concept:
    concept = db.get(Concept, concept_id)
    if concept is None:
        raise HTTPException(status_code=404, detail="Concept not found")
    if not _can_access_concept(concept, user_id):
        raise HTTPException(status_code=403, detail="Concept is private to its creator")
    return concept


def _assert_concept_owner(concept: Concept, operator_id: str) -> None:
    if concept.creator_id != operator_id:
        raise HTTPException(status_code=403, detail="Only the concept creator can update it")


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def upsert_user(payload: UserCreate, db: DbDep) -> User:
    user = db.get(User, payload.id)
    if user is None:
        user = User(id=payload.id, nickname=payload.nickname, avatar_url=payload.avatar_url)
        db.add(user)
    else:
        user.nickname = payload.nickname
        user.avatar_url = payload.avatar_url
    db.commit()
    db.refresh(user)
    return user


@router.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: str, db: DbDep) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/concepts", response_model=ConceptRead, status_code=status.HTTP_201_CREATED)
def create_concept(payload: ConceptCreate, db: DbDep) -> Concept:
    _ensure_user(db, payload.creator_id)
    concept = Concept(
        name=payload.name.strip(),
        description=payload.description,
        creator_id=payload.creator_id,
        is_shared=payload.is_shared,
    )
    db.add(concept)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Concept already exists for this creator"
        ) from exc
    db.refresh(concept)
    return concept


@router.get("/concepts", response_model=list[ConceptRead])
def search_concepts(
    db: DbDep,
    q: str | None = Query(default=None, description="Search by concept name or description"),
    viewer_id: str | None = Query(default=None, description="Current user for data isolation"),
    creator_id: str | None = Query(default=None, description="Optional owner filter"),
    include_shared: bool = True,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[Concept]:
    statement = select(Concept)
    if q:
        like = f"%{q}%"
        statement = statement.where(or_(Concept.name.like(like), Concept.description.like(like)))
    if creator_id:
        statement = statement.where(Concept.creator_id == creator_id)
    elif viewer_id:
        access_filter = Concept.creator_id == viewer_id
        if include_shared:
            access_filter = or_(access_filter, Concept.is_shared.is_(True))
        statement = statement.where(access_filter)
    else:
        statement = statement.where(Concept.is_shared.is_(True))
    statement = (
        statement.order_by(Concept.is_pinned.desc(), Concept.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(statement))


@router.get("/concepts/{concept_id}", response_model=ConceptRead)
def get_concept(concept_id: int, db: DbDep, viewer_id: str | None = None) -> Concept:
    return _get_accessible_concept(db, concept_id, viewer_id)


@router.patch("/concepts/{concept_id}", response_model=ConceptRead)
def update_concept(concept_id: int, payload: ConceptUpdate, db: DbDep) -> Concept:
    concept = db.get(Concept, concept_id)
    if concept is None:
        raise HTTPException(status_code=404, detail="Concept not found")
    _assert_concept_owner(concept, payload.operator_id)
    update_data = payload.model_dump(exclude={"operator_id"}, exclude_unset=True)
    for key, value in update_data.items():
        setattr(concept, key, value)
    db.commit()
    db.refresh(concept)
    return concept


@router.post("/insights", response_model=InsightWithPrevious, status_code=status.HTTP_201_CREATED)
def create_insight(payload: InsightCreate, db: DbDep) -> InsightWithPrevious:
    _ensure_user(db, payload.author_id)
    concept = _get_accessible_concept(db, payload.concept_id, payload.author_id)

    safety = ContentSafetyService().check_text(payload.content)
    if not safety.allowed:
        raise HTTPException(status_code=422, detail=f"Content safety check failed: {safety.reason}")

    previous_id = payload.previous_insight_id
    if previous_id is None:
        previous_id = db.scalar(
            select(Insight.id)
            .where(Insight.concept_id == payload.concept_id, Insight.author_id == payload.author_id)
            .order_by(Insight.occurred_at.desc(), Insight.id.desc())
            .limit(1)
        )
    else:
        previous = db.get(Insight, previous_id)
        if previous is None or previous.author_id != payload.author_id:
            raise HTTPException(status_code=404, detail="Previous insight not found")

    insight = Insight(
        concept_id=payload.concept_id,
        author_id=payload.author_id,
        content=payload.content,
        mood=payload.mood,
        tags=",".join(tag.strip() for tag in payload.tags if tag.strip()) or None,
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
    viewer_id: str,
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    author_id: str | None = None,
    tag: str | None = None,
    only_mine: bool = Query(default=True, description="Only show insights from current viewer"),
) -> list[InsightRead]:
    concept = _get_accessible_concept(db, concept_id, viewer_id)
    statement = select(Insight).where(Insight.concept_id == concept_id)
    
    # 应用过滤逻辑
    if only_mine:
        statement = statement.where(Insight.author_id == viewer_id)
    elif author_id:
        statement = statement.where(Insight.author_id == author_id)
    elif not concept.is_shared:
        statement = statement.where(Insight.author_id == viewer_id)
    
    if tag:
        statement = statement.where(Insight.tags.like(f"%{tag}%"))
    ordering = Insight.occurred_at.asc() if order == "asc" else Insight.occurred_at.desc()
    statement = statement.order_by(ordering)
    return [_insight_to_read(insight, db) for insight in db.scalars(statement)]


@router.get("/concepts/{concept_id}/timeline", response_model=list[InsightRead])
def get_timeline(
    concept_id: int,
    db: DbDep,
    viewer_id: str,
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
    only_mine: bool = Query(default=True, description="Only show insights from current viewer"),
) -> list[InsightRead]:
    return list_concept_insights(concept_id=concept_id, order=order, db=db, viewer_id=viewer_id, only_mine=only_mine)


@router.get("/insights/diff", response_model=DiffResponse)
def diff_insights(left_id: int, right_id: int, viewer_id: str, db: DbDep) -> DiffResponse:
    left = db.get(Insight, left_id)
    right = db.get(Insight, right_id)
    if left is None or right is None:
        raise HTTPException(status_code=404, detail="Insight not found")
    if left.concept_id != right.concept_id:
        raise HTTPException(status_code=400, detail="Insights belong to different concepts")
    _get_accessible_concept(db, left.concept_id, viewer_id)

    diff = list(ndiff(left.content.splitlines(), right.content.splitlines()))
    return DiffResponse(
        left=_insight_to_read(left, db),
        right=_insight_to_read(right, db),
        added_lines=[line[2:] for line in diff if line.startswith("+ ")],
        removed_lines=[line[2:] for line in diff if line.startswith("- ")],
    )


@router.get("/calendar", response_model=list[CalendarDay])
def get_calendar(user_id: str, db: DbDep) -> list[CalendarDay]:
    rows = db.execute(
        select(func.date(Insight.occurred_at), func.count(Insight.id))
        .where(Insight.author_id == user_id)
        .group_by(func.date(Insight.occurred_at))
        .order_by(func.date(Insight.occurred_at).asc())
    ).all()
    return [CalendarDay(date=str(day), count=count) for day, count in rows]


@router.post("/share-posters")
def create_share_poster(payload: SharePosterPayload) -> dict[str, str]:
    # MVP returns structured poster copy; mini-program can render it as a canvas/card.
    title = f"我对「{payload.concept_name}」的新一圈年轮"
    subtitle = f"时间跨度：{payload.time_span}"
    return {"title": title, "subtitle": subtitle, "content": payload.insight_content[:180]}
