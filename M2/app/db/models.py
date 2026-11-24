from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("name", name="uq_categories_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    events: Mapped[list["Event"]] = relationship(back_populates="category", passive_deletes=True)


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("capacity > 0", name="ck_events_positive_capacity"),
        CheckConstraint("end_at > start_at", name="ck_events_valid_date_range"),
        CheckConstraint("status IN ('DRAFT','PUBLISHED','ARCHIVED','CANCELLED')", name="ck_events_valid_status"),
        Index("ix_events_status_start_at", "status", "start_at"),
        Index("ix_events_organizer_id", "organizer_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    organizer_id: Mapped[str] = mapped_column(String(36), nullable=False)
    category_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="DRAFT")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    category: Mapped[Category] = relationship(back_populates="events")
