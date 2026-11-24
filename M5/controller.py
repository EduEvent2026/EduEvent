import datetime as dt
import re
from abc import ABC, abstractmethod
from .models import CalendarView, ViewType
from .service import CalendarService
from flask import Blueprint, jsonify, request

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

class InvalidDateError(ValueError):
    """Data z żądania ma zły format albo nie istnieje."""

class ICalendarAPI(ABC):
    """Publiczne API modułu 5 (REST/JSON)."""

    @abstractmethod
    def get_day(self, target_date: str) -> CalendarView: ...

    @abstractmethod
    def get_week(self, target_date: str) -> CalendarView: ...

    @abstractmethod
    def get_month(self, target_date: str) -> CalendarView: ...


class CalendarController(ICalendarAPI):
    """Odbiera żądanie HTTP, sprawdza poprawność daty, wywołuje serwis i zwraca widok."""

    def __init__(self, service: CalendarService):
        self._service = service

    def get_day(self, target_date: str) -> CalendarView:
        return self._service.build_view(ViewType.DAY, self._parse_date(target_date))

    def get_week(self, target_date: str) -> CalendarView:
        return self._service.build_view(ViewType.WEEK, self._parse_date(target_date))

    def get_month(self, target_date: str) -> CalendarView:
        return self._service.build_view(ViewType.MONTH, self._parse_date(target_date))

    @staticmethod
    def _parse_date(raw_date: str) -> dt.date:
        if raw_date is None or raw_date == "":
            raise InvalidDateError("Parametr date jest wymagany (format RRRR-MM-DD)")
        if not _DATE_RE.match(raw_date):
            raise InvalidDateError("Data musi mieć format RRRR-MM-DD, np. 2026-11-10.")
        try:
            value = dt.date.fromisoformat(raw_date)
        except ValueError:
            raise InvalidDateError(f"Data {raw_date} nie istnieje w kalendarzu.")
        return value