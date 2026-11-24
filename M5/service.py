import datetime as dt
import calendar
from .client import EventsApiClient
from .models import CalendarDay, CalendarView, Event, ViewType
from zoneinfo import ZoneInfo
from operator import attrgetter

ZONE = ZoneInfo("Europe/Warsaw")

class CalendarService:
    """Ustala zakres dat, pobiera wydarzenia przez klienta i składa widok kalendarza."""

    def __init__(self, events_client: EventsApiClient):
        self._eventsClient = events_client

    def build_view(self, view_type: ViewType, target_date: dt.date) -> CalendarView:
        start, end = self._calculate_range(view_type, target_date)
        events = self._events_client.fetch_events(start - dt.timedelta(days=1), end + dt.timedelta(days=1))
        days = self._group_by_day(events, start, end)
        return CalendarView(view_type, start, end, days)

    @staticmethod
    def _calculate_range(view_type: ViewType, target_date: dt.date) -> tuple[dt.date, dt.date]:
        if view_type == ViewType.DAY:
            return target_date, target_date
        if view_type == ViewType.WEEK:
            monday = target_date - dt.timedelta(days=target_date.weekday())
            return monday, monday + dt.timedelta(days=6)
        if view_type == ViewType.MONTH:
            last_day = calendar.monthrange(target_date.year, target_date.month)[1]
            return target_date.replace(day=1), target_date.replace(day=last_day)

    @staticmethod
    def _group_by_day(events: list[Event], start: dt.date, end: dt.date) -> list[CalendarDay]:

        days = {start + dt.timedelta(days=i): CalendarDay(start + dt.timedelta(days=i)) for i in range((end - start).days + 1)}

        for event in events:
            first = event.start.astimezone(ZONE).date()
            last = max(event.end.astimezone(ZONE).date(), first)

            current = max(first, start)
            while current <= min(last, end):
                days[current].events.append(event)
                current += dt.timedelta(days=1)

        for day in days.values():
            day.events.sort(key=attrgetter("start", "title"))

        return list(days.values())