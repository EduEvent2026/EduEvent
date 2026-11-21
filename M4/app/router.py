from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.auth import CurrentUser, get_current_user
from app.clients import HttpEventsAPI, HttpNotificationsAPI
from app.database import get_db
from app.models import RegistrationStatus
from app.repositories import SqlAlchemyRegistrationRepository
from app.schemas import (
    ErrorResponse,
    PaginatedResponse,
    RegistrationCreateRequest,
    RegistrationResponse,
    RegistrationUpdateRequest,
)
from app.services import RegistrationService

router = APIRouter(prefix="/api/v1/registrations", tags=["Registrations"])


def get_registration_service(db: Session = Depends(get_db)) -> RegistrationService:
    return RegistrationService(
        db=db,
        repository=SqlAlchemyRegistrationRepository(db),
        events_api=HttpEventsAPI(),
        notifications_api=HttpNotificationsAPI(),
    )


@router.post(
    "",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
    summary="Zapisanie użytkownika na wydarzenie (lista główna lub rezerwowa)",
)
async def create_registration(
    payload: RegistrationCreateRequest,
    request: Request,
    response: Response,
    current_user: CurrentUser = Depends(get_current_user),
    authorization: str | None = Header(default=None),
    service: RegistrationService = Depends(get_registration_service),
) -> RegistrationResponse:
    reg = await service.register_user(
        event_id=payload.event_id,
        user_id=UUID(current_user.user_id),
        auth_header=authorization,
    )
    response.headers["Location"] = str(
        request.url_for("get_registration_by_id", registration_id=reg.id)
    )
    return RegistrationResponse.model_validate(reg)


@router.get(
    "",
    response_model=PaginatedResponse[RegistrationResponse],
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
    },
    summary="Pobranie paginowanej listy zapisów (główna, rezerwowa, historia)",
)
def get_registrations(
    event_id: UUID | None = Query(default=None, alias="eventId"),
    user_id: UUID | None = Query(default=None, alias="userId"),
    registration_status: RegistrationStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    current_user: CurrentUser = Depends(get_current_user),
    service: RegistrationService = Depends(get_registration_service),
) -> PaginatedResponse[RegistrationResponse]:
    return service.get_registrations(
        current_user=current_user,
        event_id=event_id,
        user_id=user_id,
        status=registration_status,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{registration_id}",
    name="get_registration_by_id",
    response_model=RegistrationResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
    summary="Pobranie szczegółów pojedynczego zapisu",
)
def get_registration(
    registration_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    service: RegistrationService = Depends(get_registration_service),
) -> RegistrationResponse:
    reg = service.get_registration(
        reg_id=registration_id,
        current_user=current_user,
    )
    return RegistrationResponse.model_validate(reg)


@router.patch(
    "/{registration_id}",
    response_model=RegistrationResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
    summary="Aktualizacja statusu zapisu (CRUD - Update)",
)
async def update_registration(
    registration_id: UUID,
    payload: RegistrationUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    authorization: str | None = Header(default=None),
    service: RegistrationService = Depends(get_registration_service),
) -> RegistrationResponse:
    reg = await service.update_registration_status(
        reg_id=registration_id,
        new_status=payload.status,
        current_user=current_user,
        auth_header=authorization,
    )
    return RegistrationResponse.model_validate(reg)


@router.delete(
    "/{registration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
    summary="Rezygnacja z udziału i ewentualny awans kolejnej osoby z listy rezerwowej",
)
async def delete_registration(
    registration_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    authorization: str | None = Header(default=None),
    service: RegistrationService = Depends(get_registration_service),
) -> Response:
    await service.cancel_registration(
        reg_id=registration_id,
        current_user=current_user,
        auth_header=authorization,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)