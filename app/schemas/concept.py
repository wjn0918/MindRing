from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    openid: str = Field(min_length=1, max_length=64)
    nickname: str | None = Field(default=None, max_length=120)
    avatar_url: str | None = Field(default=None, max_length=500)
    birth_date: date | str | None = None


class UserRead(BaseModel):
    id: int
    openid: str
    nickname: str | None
    avatar_url: str | None
    birth_date: date | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    nickname: str | None = Field(default=None, max_length=120)
    avatar_url: str | None = Field(default=None, max_length=500)
    birth_date: date | str | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    user: UserRead


class ConceptCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None


class ConceptUpdate(BaseModel):
    description: str | None = None
    is_pinned: bool | None = None


class ConceptRead(BaseModel):
    id: int
    name: str
    description: str | None
    creator_id: int
    is_pinned: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InsightCreate(BaseModel):
    concept_id: int
    content: str = Field(min_length=1)
    mood: str | None = Field(default=None, max_length=80)
    tags: list[str] = Field(default_factory=list)
    is_shared: bool = False
    occurred_at: datetime | None = None
    previous_insight_id: int | None = None


class InsightUpdate(BaseModel):
    content: str | None = Field(default=None, min_length=1)
    mood: str | None = Field(default=None, max_length=80)
    tags: list[str] | None = None
    is_shared: bool | None = None
    occurred_at: datetime | None = None


class InsightRead(BaseModel):
    id: int
    concept_id: int
    author_id: int
    author_nickname: str | None
    author_avatar_url: str | None
    content: str
    mood: str | None
    tags: list[str]
    is_shared: bool
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
