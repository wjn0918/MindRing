from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Concept(Base):
    __tablename__ = "concepts"
    __table_args__ = (UniqueConstraint("name", "creator_id", name="uq_concept_creator_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    creator_id: Mapped[str] = mapped_column(String(64), index=True)
    is_pinned: Mapped[bool] = mapped_column(default=False)
    is_shared: Mapped[bool] = mapped_column(default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    insights: Mapped[list["Insight"]] = relationship(
        back_populates="concept", cascade="all, delete-orphan"
    )


class Insight(Base):
    __tablename__ = "insights"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    concept_id: Mapped[int] = mapped_column(
        ForeignKey("concepts.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[str] = mapped_column(String(64), index=True)
    content: Mapped[str] = mapped_column(Text)
    mood: Mapped[str | None] = mapped_column(String(80), nullable=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Comma-separated tags")
    previous_insight_id: Mapped[int | None] = mapped_column(
        ForeignKey("insights.id", ondelete="SET NULL"), nullable=True
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    concept: Mapped[Concept] = relationship(back_populates="insights")
    previous_insight: Mapped["Insight | None"] = relationship(remote_side=[id])
