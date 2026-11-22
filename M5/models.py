from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum


class ViewType(Enum):
    """Rodzaj widoku kalendarza: dzienny, tygodniowy lub miesięczny."""
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"


@dataclass
class Event:
    """Jedno wydarzenie (kopia danych z modułu 2, tylko do odczytu)."""
    id: int
    title: str
    start: datetime
    end: datetime
    location: str
    category: str
    host: str
    status: str


@dataclass
class CalendarDay:
    """Jeden dzień w widoku kalendarza."""
    date: date
    events: list[Event] = field(default_factory=list)


@dataclass
class CalendarView:
    """Cała odpowiedź dla frontendu: rodzaj widoku, zakres dat i lista dni."""
    type: ViewType
    start: date
    end: date
    days: list[CalendarDay] = field(default_factory=list)