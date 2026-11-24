import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.event_client import EventClient
from app.models import NotificationRequestDto, NotificationResponseDto, NotificationType
from app.notification_service import NotificationService
from app.token_validator import TokenValidator


class NotificationsController:
    def __init__(self) -> None:
        self.router = APIRouter(prefix="/notifications", tags=["Notifications"])
        self._token_validator = TokenValidator()
        self._event_client = EventClient()

        self.router.add_api_route(
            "/history",
            self.get_history,
            methods=["GET"],
            response_model=list[NotificationResponseDto],
        )
        self.router.add_api_route(
            "/{notification_id}/read",
            self.mark_as_read,
            methods=["PATCH"],
            status_code=status.HTTP_200_OK,
        )
        self.router.add_api_route(
            "/{notification_id}",
            self.delete_notification,
            methods=["DELETE"],
            status_code=status.HTTP_200_OK,
        )
        self.router.add_api_route(
            "",
            self.handle_event,
            methods=["POST"],
            status_code=status.HTTP_201_CREATED,
        )

    def _extract_bearer_token(self, authorization: str | None) -> str:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token")
        token = authorization.removeprefix("Bearer ").strip()
        if not self._token_validator.is_valid(token):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired JWT")
        return token

    def _get_service(self, db: Session) -> NotificationService:
        return NotificationService(db=db, event_client=self._event_client)

    def get_history(
        self,
        authorization: str | None = Header(default=None),
        db: Session = Depends(get_db),
    ) -> list[NotificationResponseDto]:
        token = self._extract_bearer_token(authorization)
        try:
            user_id = self._token_validator.extract_user_id(token)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

        service = self._get_service(db)
        return service.get_user_history(user_id)

    def mark_as_read(
        self,
        notification_id: int,
        authorization: str | None = Header(default=None),
        db: Session = Depends(get_db),
    ) -> dict[str, str]:
        token = self._extract_bearer_token(authorization)
        try:
            user_id = self._token_validator.extract_user_id(token)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

        service = self._get_service(db)
        service.mark_read(notification_id, user_id)
        return {"status": "read"}

    def delete_notification(
        self,
        notification_id: int,
        authorization: str | None = Header(default=None),
        db: Session = Depends(get_db),
    ) -> dict[str, str]:
        token = self._extract_bearer_token(authorization)
        try:
            user_id = self._token_validator.extract_user_id(token)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

        service = self._get_service(db)
        service.delete(notification_id, user_id)
        return {"status": "deleted"}

    async def handle_event(
        self,
        dto: NotificationRequestDto,
        authorization: str | None = Header(default=None),
        db: Session = Depends(get_db),
    ) -> dict[str, str]:
        self._extract_bearer_token(authorization)
        service = self._get_service(db)

        if dto.type in {NotificationType.REGISTRATION, NotificationType.WAITLIST_PROMOTED}:
            if not dto.user_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id is required")
            try:
                await service.handle_m4_event(dto.user_id, dto.event_id, dto.type)
            except httpx.HTTPError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Failed to fetch event details from Module 2",
                ) from exc
            return {"status": "created"}

        if dto.type in {NotificationType.EVENT_CHANGED, NotificationType.EVENT_CANCELLED}:
            service.handle_m2_change(
                event_id=dto.event_id,
                title=dto.title,
                user_ids=dto.user_ids,
                new_starts_at=dto.new_starts_at,
                event_type=dto.type,
            )
            return {"status": "created"}

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported notification type")