from uuid import UUID
from app.domain.models import Category, EventDetails, EventFilterSort, EventSummary
from app.integrations.module2_client import Module2Client


class CatalogService:
    def __init__(self, m2_client: Module2Client) -> None:
        self._m2_client = m2_client

    async def get_catalog_events(self, params: EventFilterSort) -> tuple[list[EventSummary], int]:
        raise NotImplementedError

    async def get_event_details(self, event_id: UUID) -> EventDetails:
        raise NotImplementedError

    async def get_categories(self, page: int, size: int) -> tuple[list[Category], int]:
        raise NotImplementedError

    def _map_to_summary(self, event: EventDetails) -> EventSummary:
        return EventSummary(
            id=event.id,
            categoryId=event.categoryId,
            categoryName=event.categoryName,
            title=event.title,
            location=event.location,
            startsAt=event.startsAt,
            endsAt=event.endsAt,
        )

    def _filter_events(self, events: list[EventDetails], params: EventFilterSort) -> list[EventDetails]:
        raise NotImplementedError

    def _sort_events(self, events: list[EventDetails], sort_by: str, sort_order: str) -> list[EventDetails]:
        raise NotImplementedError

    def _paginate_events(self, events: list[EventDetails], page: int, size: int) -> tuple[list[EventDetails], int]:
        raise NotImplementedError
