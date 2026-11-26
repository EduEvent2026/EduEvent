from dataclasses import dataclass, field
from enum import Enum

import datetime as dt

class ViewType(Enum):
    """Rodzaj widoku kalendarza: dzienny, tygodniowy lub miesięczny."""
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"


    #zamienia dane ze stringa np 2026-11-04T18:00:00Z na datetime na którym można wykonywac operacje
def _parse_to_datetime(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


    #zamienia datetime na stringa np 2026-11-04T18:00:00Z
def _parse_to_string(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class Event:
    """Jedno wydarzenie (kopia danych z modułu 2, tylko do odczytu)."""
    id: str
    title: str
    start: dt.datetime
    end: dt.datetime
    location: str
    category: str
    host: str
    status: str

    @classmethod
    def create_from_json(cls, data: dict) -> "Event":
        return cls(
            id=str(data["id"]),
            title=data["title"],
            start=_parse_to_datetime(data["start"]),
            end=_parse_to_datetime(data["end"]),
            location=data["location"],
            category=data["category"],
            host=data["host"],
            status=data["status"],
        )

    def parse_to_json(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "start": _parse_to_string(self.start),
            "end": _parse_to_string(self.end),
            "location": self.location,
            "category": self.category,
            "host": self.host,
            "status": self.status,
        }

@dataclass
class CalendarDay:
    """Jeden dzień w widoku kalendarza."""
    date: dt.date
    events: list[Event] = field(default_factory=list)

    def to_json(self) -> dict:
        return {
            "date": self.date.isoformat(),
            "events": [event.parse_to_json() for event in self.events],
        }


@dataclass
class CalendarView:
    """Cała odpowiedź dla frontendu: rodzaj widoku, zakres dat i lista dni."""
    type: ViewType
    start: dt.date
    end: dt.date
    days: list[CalendarDay]

    def to_json(self) -> dict:
        return {
            "type": self.type.value,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "days": [day.to_json() for day in self.days],
        }