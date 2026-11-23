from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class EventStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"
    CANCELLED = "CANCELLED"


class Category(BaseModel):
    id: UUID
    name: str
    description: str


class EventSummary(BaseModel):
    id: UUID
    categoryId: UUID
    categoryName: str
    title: str
    location: str
    startsAt: datetime
    endsAt: datetime


class EventDetails(EventSummary):
    organizerId: UUID
    description: str
    capacity: int
    status: EventStatus
    createdAt: datetime
    updatedAt: datetime


class EventFilterSort(BaseModel):
    query: Optional[str] = None
    categoryId: Optional[UUID] = None
    location: Optional[str] = None
    dateFrom: Optional[datetime] = None
    dateTo: Optional[datetime] = None
    sortBy: str = "startsAt"
    sortOrder: str = "asc"
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

    def validate_dates(self) -> bool:
        if self.dateFrom and self.dateTo:
            return self.dateTo >= self.dateFrom
        return True

    def validate_sorting(self) -> bool:
        return self.sortBy in {"startsAt", "title"} and self.sortOrder in {"asc", "desc"}
