from datetime import date

from .interfaces import IEventsAPI
from .models import Event

class EventsApiError(Exception):
    """Moduł 2 jest niedostępny albo zwrócił niepoprawne dane."""

class EventsApiClient:
    """Wysyła zapytanie HTTP GET z zakresem dat do modułu 2 i zamienia JSON na listę wydarzeń."""

    def __init__(self, events_api: IEventsAPI | None = None) -> None:
        self._events_api = events_api

    def fetch_events(self, from_date: date, to_date: date) -> list[Event]:
        pass