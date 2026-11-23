from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Boolean, DateTime, Enum as SqlEnum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class NotificationType(str, Enum):
    REGISTRATION = "REGISTRATION"
    WAITLIST_PROMOTED = "WAITLIST_PROMOTED"
    EVENT_CHANGED = "EVENT_CHANGED"
    EVENT_CANCELLED = "EVENT_CANCELLED"
    REMINDER = "REMINDER"


class ReminderStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    SENT = "SENT"
    CANCELLED = "CANCELLED"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recipient_user_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    external_event_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    type: Mapped[NotificationType] = mapped_column(SqlEnum(NotificationType), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recipient_user_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    external_event_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    event_title: Mapped[str] = mapped_column(String(255), nullable=False)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    status: Mapped[ReminderStatus] = mapped_column(
        SqlEnum(ReminderStatus),
        default=ReminderStatus.SCHEDULED,
        nullable=False,
    )


class NotificationRequestDto(BaseModel):
    type: NotificationType
    event_id: str
    user_id: str | None = None
    user_ids: list[str] | None = None
    title: str | None = None
    new_starts_at: datetime | None = None


class EventDetailsDto(BaseModel):
    event_id: str
    title: str
    starts_at: datetime


class NotificationResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recipient_user_id: str
    external_event_id: str
    type: NotificationType
    title: str
    message: str
    is_read: bool
    created_at: datetime