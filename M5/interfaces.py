from abc import ABC, abstractmethod
from datetime import date

from .models import CalendarView, Event

class IEventsAPI(ABC):
    """Kontrakt API modułu 2 (Wydarzenia i kategorie)."""

    @abstractmethod
    def getEvents(self, from_date: date, to_date: date) -> list[Event]:
        pass