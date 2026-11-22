from datetime import date

from .interfaces import ICalendarAPI
from .models import CalendarView
from .service import CalendarService


class CalendarController(ICalendarAPI):
    """Odbiera żądanie HTTP, sprawdza poprawność daty, wywołuje serwis i zwraca widok."""

    def __init__(self, service: CalendarService) -> None:
        self._service = service

    def getDay(self, target_date: date) -> CalendarView:
        pass

    def getWeek(self, target_date: date) -> CalendarView:
        pass

    def getMonth(self, target_date: date) -> CalendarView:
        pass