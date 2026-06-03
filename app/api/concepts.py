from datetime import UTC, datetime
from difflib import ndiff
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Concept, Insight
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
)
from app.services.content_safety import ContentSafetyService

router = APIRouter(prefix="/api", tags=["mindring"])
DbDep = Annotated[Session, Depends(get_db)]


def _split_tags(tags: str | None) -> list[str]:
    if not tags:
        return []
    return [tag for tag in tags.split(",") if tag]


def _insight_to_read(insight: Insight) -> InsightRead:
    return InsightRead(
        id=insight.id,
        concept_id=insight.concept_id,
        author_id=insight.author_id,
        content=insight.content,
        mood=insight.mood,
        tags=_split_tags(insight.tags),
        previous_insight_id=insight.previous_insight_id,
        occurred_at=insight.occurred_at,
        created_at=insight.created_at,
        updated_at=insight.updated_at,
    )


@router.post("/concepts", response_model=ConceptRead, status_code=status.HTTP_201_CREATED)
def create_concept(payload: ConceptCreate, db: DbDep) -> Concept:
    concept = Concept(
        name=payload.name.strip(),
        description=payload.description,
        creator_id=payload.creator_id,
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
    creator_id: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[Concept]:
    statement = select(Concept)
    if q:
        like = f"%{q}%"
        statement = statement.where(or_(Concept.name.like(like), Concept.description.like(like)))
    if creator_id:
        statement = statement.where(Concept.creator_id == creator_id)
    statement = (
        statement.order_by(Concept.is_pinned.desc(), Concept.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(statement))


@router.get("/concepts/{concept_id}", response_model=ConceptRead)
def get_concept(concept_id: int, db: DbDep) -> Concept:
    concept = db.get(Concept, concept_id)
    if concept is None:
        raise HTTPException(status_code=404, detail="Concept not found")
    return concept


@router.patch("/concepts/{concept_id}", response_model=ConceptRead)
def update_concept(
    concept_id: int, payload: ConceptUpdate, db: DbDep
) -> Concept:
    concept = db.get(Concept, concept_id)
    if concept is None:
        raise HTTPException(status_code=404, detail="Concept not found")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(concept, key, value)
    db.commit()
    db.refresh(concept)
    return concept


@router.post("/insights", response_model=InsightWithPrevious, status_code=status.HTTP_201_CREATED)
def create_insight(payload: InsightCreate, db: DbDep) -> InsightWithPrevious:
    concept = db.get(Concept, payload.concept_id)
    if concept is None:
        raise HTTPException(status_code=404, detail="Concept not found")

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
    elif db.get(Insight, previous_id) is None:
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
        **_insight_to_read(insight).model_dump(),
        previous_insight=_insight_to_read(previous) if previous else None,
    )


@router.get("/concepts/{concept_id}/insights", response_model=list[InsightRead])
def list_concept_insights(
    concept_id: int,
    db: DbDep,
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    author_id: str | None = None,
    tag: str | None = None,
) -> list[InsightRead]:
    if db.get(Concept, concept_id) is None:
        raise HTTPException(status_code=404, detail="Concept not found")
    statement = select(Insight).where(Insight.concept_id == concept_id)
    if author_id:
        statement = statement.where(Insight.author_id == author_id)
    if tag:
        statement = statement.where(Insight.tags.like(f"%{tag}%"))
    ordering = Insight.occurred_at.asc() if order == "asc" else Insight.occurred_at.desc()
    statement = statement.order_by(ordering)
    return [_insight_to_read(insight) for insight in db.scalars(statement)]


@router.get("/concepts/{concept_id}/timeline", response_model=list[InsightRead])
def get_timeline(
    concept_id: int,
    db: DbDep,
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
) -> list[InsightRead]:
    return list_concept_insights(concept_id=concept_id, order=order, db=db)


@router.get("/insights/diff", response_model=DiffResponse)
def diff_insights(left_id: int, right_id: int, db: DbDep) -> DiffResponse:
    left = db.get(Insight, left_id)
    right = db.get(Insight, right_id)
    if left is None or right is None:
        raise HTTPException(status_code=404, detail="Insight not found")

    diff = list(ndiff(left.content.splitlines(), right.content.splitlines()))
    return DiffResponse(
        left=_insight_to_read(left),
        right=_insight_to_read(right),
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
