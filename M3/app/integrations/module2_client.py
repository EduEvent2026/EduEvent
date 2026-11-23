from typing import Optional
from uuid import UUID
import httpx
from app.domain.models import Category, EventDetails


class Module2Client:
    def __init__(self, base_url: str, timeout: int = 5) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def get_events(self, page: int, size: int) -> tuple[list[EventDetails], int]:
        raise NotImplementedError

    async def get_event(self, event_id: UUID) -> Optional[EventDetails]:
        raise NotImplementedError

    async def get_categories(self, page: int, size: int) -> tuple[list[Category], int]:
        raise NotImplementedError

    async def get_category(self, category_id: UUID) -> Optional[Category]:
        raise NotImplementedError
