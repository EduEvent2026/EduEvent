from datetime import datetime, timezone
from typing import Annotated, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer
from pydantic.alias_generators import to_camel

from app.models import RegistrationStatus


def serialize_utc_datetime(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


UtcDateTime = Annotated[datetime, PlainSerializer(serialize_utc_datetime, return_type=str)]


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class ErrorDetail(CamelModel):
    code: str
    message: str


class ErrorResponse(CamelModel):
    error: ErrorDetail


class EventDTO(CamelModel):
    id: UUID
    title: str
    starts_at: UtcDateTime
    max_capacity: int = Field(..., ge=0)


class RegistrationCreateRequest(CamelModel):
    event_id: UUID


class RegistrationUpdateRequest(CamelModel):
    status: RegistrationStatus


class RegistrationResponse(CamelModel):
    id: UUID
    event_id: UUID
    user_id: UUID
    status: RegistrationStatus
    created_at: UtcDateTime


T = TypeVar("T")


class PaginatedResponse(CamelModel, Generic[T]):
    items: list[T]
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=100)
    total_items: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=0)