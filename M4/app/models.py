import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import CHAR, DateTime, Enum, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RegistrationStatus(str, enum.Enum):
    MAIN = "MAIN"
    RESERVE = "RESERVE"
    CANCELLED = "CANCELLED"


class EventProjection(Base):
    """Lokalna kopia danych o wydarzeniu (projekcja z Modułu 2)."""

    __tablename__ = "event_projections"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True)
    max_capacity: Mapped[int] = mapped_column(Integer, nullable=False)

    registrations: Mapped[list["Registration"]] = relationship(
        back_populates="event"
    )


class UserProjection(Base):
    """Lokalna kopia identyfikatora użytkownika (projekcja z Modułu 1)."""

    __tablename__ = "user_projections"

    id: Mapped[str] = mapped_column(CHAR(36), primary_key=True)

    registrations: Mapped[list["Registration"]] = relationship(
        back_populates="user"
    )


class Registration(Base):
    """Główna tabela operacyjna zapisów i listy rezerwowej (kolejka FIFO po created_at)."""

    __tablename__ = "registrations"

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
        ForeignKey("user_projections.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[RegistrationStatus] = mapped_column(
        Enum(RegistrationStatus),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    event: Mapped[EventProjection] = relationship(back_populates="registrations")
    user: Mapped[UserProjection] = relationship(back_populates="registrations")

    __table_args__ = (
        Index("ix_registrations_event_user_status", "event_id", "user_id", "status"),
        Index("ix_registrations_event_status_created", "event_id", "status", "created_at"),
    )