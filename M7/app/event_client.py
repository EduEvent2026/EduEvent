from datetime import datetime

import httpx

from app.config import settings
from app.models import EventDetailsDto


class EventClient:
    def __init__(self, base_url: str = settings.events_api_url) -> None:
        self._base_url = base_url.rstrip("/")

    async def get_event_details(self, event_id: str) -> EventDetailsDto:
        url = f"{self._base_url}/events/{event_id}"
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        raw_starts_at = data.get("starts_at") or data.get("startsAt")
        title = data.get("title") or data.get("name") or f"Wydarzenie {event_id}"
        return EventDetailsDto(
            event_id=str(data.get("id", event_id)),
            title=title,
            starts_at=datetime.fromisoformat(raw_starts_at),
        )