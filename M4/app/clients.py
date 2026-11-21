from abc import ABC, abstractmethod
import logging
from uuid import UUID
from datetime import datetime, timezone
from app.schemas import EventDTO, serialize_utc_datetime

import httpx

from app.config import settings
from app.exceptions import event_not_found_error, external_service_error
from app.schemas import EventDTO

logger = logging.getLogger(__name__)


class IEventsAPI(ABC):
    @abstractmethod
    async def get_event_details(
        self, event_id: UUID, auth_header: str | None = None
    ) -> EventDTO:
        raise NotImplementedError


class HttpEventsAPI(IEventsAPI):
    async def get_event_details(
        self, event_id: UUID, auth_header: str | None = None
    ) -> EventDTO:
        if settings.dev_mock_external_apis:
            return EventDTO(
                id=event_id,
                title="Przykładowe wydarzenie (DEV)",
                starts_at=datetime(2026, 11, 15, 12, 0, 0, tzinfo=timezone.utc),
                max_capacity=settings.dev_default_event_capacity,
            )

        headers = {"Authorization": auth_header} if auth_header else {}
        url = f"{settings.events_api_url}/api/v1/events/{event_id}"

        try:
            async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
                response = await client.get(url, headers=headers)
        except httpx.RequestError as exc:
            logger.error("Nie udało się połączyć z Modułem 2 (Events): %s", exc)
            raise external_service_error("Events") from exc

        if response.status_code == 404:
            raise event_not_found_error()
        if response.status_code != 200:
            logger.error("Nieoczekiwany status z Modułu 2: %s", response.status_code)
            raise external_service_error("Events")

        data = response.json()
        capacity = data.get("maxCapacity", data.get("capacity"))
        title = data.get("title", data.get("eventTitle", "Wydarzenie"))
        starts_at = data.get("startsAt")

        if capacity is None or starts_at is None:
            raise external_service_error("Events")

        return EventDTO(
            id=event_id,
            title=str(title),
            starts_at=starts_at,
            max_capacity=int(capacity),
        )


class INotificationsAPI(ABC):
    @abstractmethod
    async def send_registration_notification(
        self,
        *,
        notification_type: str,
        user_id: UUID,
        event_id: UUID,
        event_title: str,
        starts_at: datetime,
        auth_header: str | None = None,
    ) -> None:
        raise NotImplementedError


class HttpNotificationsAPI(INotificationsAPI):
    async def send_registration_notification(
        self,
        *,
        notification_type: str,
        user_id: UUID,
        event_id: UUID,
        event_title: str,
        starts_at: datetime,
        auth_header: str | None = None,
    ) -> None:
        payload = {
            "type": notification_type,
            "userId": str(user_id),
            "eventId": str(event_id),
            "eventTitle": event_title,
            "startsAt": serialize_utc_datetime(starts_at),
        }

        if settings.dev_mock_external_apis:
            logger.info("[MOCK POST /notifications] %s", payload)
            return

        headers = {"Authorization": auth_header} if auth_header else {}
        url = f"{settings.notifications_api_url}/notifications"

        try:
            async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code >= 400:
                    logger.warning(
                        "Moduł 7 (Notifications) zwrócił status %s: %s",
                        response.status_code,
                        response.text,
                    )
        except httpx.RequestError as exc:
            logger.warning("Nie udało się wysłać powiadomienia do Modułu 7: %s", exc)