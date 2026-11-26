import os
from datetime import date, datetime, timezone
from typing import Any

import requests

from .interfaces import IEventsAPI
from .models import Event


class EventsApiError(Exception):
    """Moduł 2 jest niedostępny albo zwrócił niepoprawne dane."""


class EventsApiClient:
    """Wysyła zapytanie HTTP GET z zakresem dat do Modułu 2 i zamienia JSON na listę wydarzeń."""

    def __init__(
        self,
        base_url: str | None = None,
        events_api: IEventsAPI | None = None,
        timeout: float = 5.0,
        use_mock: bool | None = None,
    ) -> None:
        self._base_url = (base_url or os.getenv("EVENTS_API_URL", "http://m2:8000")).rstrip("/")
        self._events_endpoint = os.getenv("EVENTS_API_ENDPOINT", "/api/events")
        self._events_api = events_api
        self._timeout = timeout
        if use_mock is None:
            self._use_mock = os.getenv("USE_MOCK_EVENTS", "true").lower() == "true"
        else:
            self._use_mock = use_mock

    def fetch_events(self, from_date: date, to_date: date) -> list[Event]:
        """Pobiera wszystkie wydarzenia z podanego zakresu dat (z obsługą paginacji)."""
        if self._events_api is not None:
            try:
                return self._events_api.get_events(from_date, to_date)
            except Exception as exc:
                raise EventsApiError("Błąd podczas pobierania wydarzeń z IEventsAPI.") from exc

        if self._use_mock:
            return self._get_mock_events(from_date, to_date)

        events: list[Event] = []
        page = 1

        while True:
            try:
                response = requests.get(
                    f"{self._base_url}{self._events_endpoint}",
                    params={
                        "from": from_date.isoformat(),
                        "to": to_date.isoformat(),
                        "page": page,
                    },
                    timeout=self._timeout,
                )
                response.raise_for_status()
                payload: Any = response.json()
            except (requests.RequestException, ValueError) as exc:
                raise EventsApiError(f"Błąd komunikacji z Modułem 2: {exc}") from exc

            if isinstance(payload, list):
                raw_items = payload
                has_next = False
            elif isinstance(payload, dict):
                raw_items = payload.get("items") or payload.get("results") or payload.get("events") or []
                has_next = bool(payload.get("has_next") or payload.get("next"))
            else:
                raise EventsApiError("Nieoczekiwany format odpowiedzi z Modułu 2.")

            if not raw_items:
                break

            try:
                events.extend(Event.create_from_json(item) for item in raw_items)
            except (KeyError, TypeError, ValueError) as exc:
                raise EventsApiError(f"Niepoprawne dane wydarzenia z Modułu 2: {exc}") from exc

            if not has_next:
                break
            page += 1

        return events

    @staticmethod
    def _get_mock_events(from_date: date, to_date: date) -> list[Event]:
        """Tymczasowe dane testowe na czas braku działającego Modułu 2."""
        mid_date = from_date + (to_date - from_date) // 2
        sample_events = [
            Event(
                id="mock-1",
                title="Wykład z Inżynierii Oprogramowania",
                start=datetime(mid_date.year, mid_date.month, mid_date.day, 9, 15, tzinfo=timezone.utc),
                end=datetime(mid_date.year, mid_date.month, mid_date.day, 10, 45, tzinfo=timezone.utc),
                location="Aula A1",
                category="Wykład",
                host="dr Jan Kowalski",
                status="ACTIVE",
            ),
            Event(
                id="mock-2",
                title="Laboratorium: Docker i Mikroserwisy",
                start=datetime(mid_date.year, mid_date.month, mid_date.day, 13, 0, tzinfo=timezone.utc),
                end=datetime(mid_date.year, mid_date.month, mid_date.day, 14, 30, tzinfo=timezone.utc),
                location="Sala 204",
                category="Laboratorium",
                host="mgr Anna Nowak",
                status="ACTIVE",
            ),
        ]
        return [e for e in sample_events if from_date <= e.start.date() <= to_date]