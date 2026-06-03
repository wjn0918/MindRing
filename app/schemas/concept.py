from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConceptCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    creator_id: str = Field(min_length=1, max_length=64)


class ConceptUpdate(BaseModel):
    description: str | None = None
    is_pinned: bool | None = None


class ConceptRead(BaseModel):
    id: int
    name: str
    description: str | None
    creator_id: str
    is_pinned: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InsightCreate(BaseModel):
    concept_id: int
    author_id: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1)
    mood: str | None = Field(default=None, max_length=80)
    tags: list[str] = Field(default_factory=list)
    occurred_at: datetime | None = None
    previous_insight_id: int | None = None


class InsightRead(BaseModel):
    id: int
    concept_id: int
    author_id: str
    content: str
    mood: str | None
    tags: list[str]
    previous_insight_id: int | None
    occurred_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InsightWithPrevious(InsightRead):
    previous_insight: InsightRead | None = None


class DiffResponse(BaseModel):
    left: InsightRead
    right: InsightRead
    added_lines: list[str]
    removed_lines: list[str]


class CalendarDay(BaseModel):
    date: str
    count: int


class SharePosterPayload(BaseModel):
    concept_name: str
    insight_content: str
    time_span: str
    author_name: str | None = None
