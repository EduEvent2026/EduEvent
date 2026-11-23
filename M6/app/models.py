# model rekordu obecności
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import CHAR, DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

class AttendanceStatus(str, enum.Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"

class EventProjection(Base):
    """Lokalna kopia danych o wydarzeniu (projekcja z Modułu 2)."""

    __tablename__ = "event_projections"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    source_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(
        back_populates="event"
    )

class UserProjection(Base):
    """Lokalna kopia identyfikatora użytkownika (projekcja z Modułu 1)."""

    __tablename__ = "user_projections"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True)

    registrations: Mapped[list["Registration"]] = relationship(
        back_populates="user"
    )




class AttendanceRecord(Base):
    """Rekord obecności uczestnika na wydarzeniu."""

    __tablename__ = "attendance_records"

    id: Mapped[str] = mapped_column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    event_id: Mapped[str] = mapped_column(
        CHAR(36),
        ForeignKey("event_projections.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        CHAR(36),
        nullable=False,
        index=True,
    )
    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus, create_constraint=True, validate_strings=True),
        nullable=False,
    )
    marked_by_user_id: Mapped[str] = mapped_column(CHAR(36), nullable=False)
    marked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    event: Mapped[EventProjection] = relationship(
        back_populates="attendance_records"
    )

    __table_args__ = (
        Index(
            "ux_attendance_records_event_user",
            "event_id",
            "user_id",
            unique=True,
        ),
    )


