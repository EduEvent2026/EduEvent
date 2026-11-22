from abc import ABC, abstractmethod
from datetime import date

from .models import CalendarView, Event


class ICalendarAPI(ABC):
    """Publiczne API modułu 5 (REST/JSON)."""

    @abstractmethod
    def getDay(self, target_date: date) -> CalendarView:
        pass

    @abstractmethod
    def getWeek(self, target_date: date) -> CalendarView:
        pass

    @abstractmethod
    def getMonth(self, target_date: date) -> CalendarView:
        pass


class IEventsAPI(ABC):
    """Kontrakt API modułu 2 (Wydarzenia i kategorie)."""

    @abstractmethod
    def getEvents(self, from_date: date, to_date: date) -> list[Event]:
        pass