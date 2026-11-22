from datetime import date

from .client import EventsApiClient
from .models import CalendarDay, CalendarView, Event, ViewType


class CalendarService:
    """Ustala zakres dat, pobiera wydarzenia przez klienta i składa widok kalendarza."""

    def __init__(self, events_client: EventsApiClient) -> None:
        self._eventsClient = events_client

    def buildView(self, view_type: ViewType, target_date: date) -> CalendarView:
        pass

    def _calculateRange(self, view_type: ViewType, target_date: date) -> tuple[date, date]:
        pass

    def _groupByDay(self, events: list[Event], start: date, end: date) -> list[CalendarDay]:
        pass