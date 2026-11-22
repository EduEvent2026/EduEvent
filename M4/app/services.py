from datetime import datetime, timezone
import math
from uuid import UUID

from sqlalchemy.orm import Session

from app.auth import CurrentUser, ROLE_ADMIN, ROLE_ORGANIZER, ROLE_SERVICE
from app.clients import IEventsAPI, INotificationsAPI
from app.exceptions import (
    event_capacity_exceeded_error,
    forbidden_error,
    registration_already_cancelled_error,
    registration_duplicate_error,
    registration_not_found_error,
)
from app.models import Registration, RegistrationStatus
from app.repositories import IRegistrationRepository
from app.schemas import PaginatedResponse, RegistrationResponse


class RegistrationService:
    def __init__(
        self,
        db: Session,
        repository: IRegistrationRepository,
        events_api: IEventsAPI,
        notifications_api: INotificationsAPI,
    ) -> None:
        self.db = db
        self.repository = repository
        self.events_api = events_api
        self.notifications_api = notifications_api

    async def register_user(
        self,
        event_id: UUID,
        user_id: UUID,
        auth_header: str | None = None,
    ) -> Registration:
        # 1. Weryfikacja duplikatów
        existing = self.repository.find_active_by_event_and_user(event_id, user_id)
        if existing is not None:
            raise registration_duplicate_error()

        # 2. Pobranie danych wydarzenia i limitu miejsc z Modułu 2
        event_dto = await self.events_api.get_event_details(
            event_id, auth_header=auth_header
        )

        # 3. Transakcja z blokadą na projekcji wydarzenia (ochrona przed wyścigiem)
        try:
            self.repository.upsert_event_projection(
                event_id=event_id,
                max_capacity=event_dto.max_capacity,
                lock_for_update=True,
            )
            self.repository.ensure_user_projection(user_id)

            # Ponowne sprawdzenie duplikatu wewnątrz blokady
            if self.repository.find_active_by_event_and_user(event_id, user_id):
                raise registration_duplicate_error()

            main_list_count = self.repository.count_main_list(event_id)
            assigned_status = (
                RegistrationStatus.MAIN
                if main_list_count < event_dto.max_capacity
                else RegistrationStatus.RESERVE
            )

            reg = Registration(
                event_id=str(event_id),
                user_id=str(user_id),
                status=assigned_status,
                created_at=datetime.now(timezone.utc),
            )
            self.repository.save(reg)
            self.db.commit()
            self.db.refresh(reg)
        except Exception:
            self.db.rollback()
            raise

        # 4. Wysłanie powiadomienia do Modułu 7
        if assigned_status == RegistrationStatus.MAIN:
            await self.notifications_api.send_registration_notification(
                notification_type="REGISTRATION_CONFIRMED",
                user_id=user_id,
                event_id=event_id,
                event_title=event_dto.title,
                starts_at=event_dto.starts_at,
                auth_header=auth_header,
            )
        return reg

    async def cancel_registration(
        self,
        reg_id: UUID,
        current_user: CurrentUser,
        auth_header: str | None = None,
    ) -> Registration:
        reg = self.repository.find_by_id(reg_id)
        if reg is None:
            raise registration_not_found_error()

        is_privileged = current_user.has_any_role(ROLE_ORGANIZER, ROLE_ADMIN)
        if not is_privileged and reg.user_id != current_user.user_id:
            # Zgodnie z zasadami API: 404 jeśli zasób nie istnieje albo nie należy do użytkownika
            raise registration_not_found_error()

        if reg.status == RegistrationStatus.CANCELLED:
            raise registration_already_cancelled_error()

        previous_status = reg.status
        event_id = UUID(reg.event_id)
        cancelled_user_id = UUID(reg.user_id)

        # Pobieramy dane wydarzenia (limit miejsc, tytuł i datę rozpoczęcia dla Modułu 7)
        event_dto = await self.events_api.get_event_details(
            event_id, auth_header=auth_header
        )

        promoted_reg: Registration | None = None
        try:
            if previous_status == RegistrationStatus.MAIN:
                self.repository.upsert_event_projection(
                    event_id=event_id,
                    max_capacity=event_dto.max_capacity,
                    lock_for_update=True,
                )

            reg.status = RegistrationStatus.CANCELLED
            self.repository.save(reg)

            if previous_status == RegistrationStatus.MAIN:
                promoted_reg = self._promote_from_reserve_in_tx(
                    event_id=event_id,
                    max_capacity=event_dto.max_capacity,
                )

            self.db.commit()
            self.db.refresh(reg)
        except Exception:
            self.db.rollback()
            raise

        await self.notifications_api.send_registration_notification(
            notification_type="REGISTRATION_CANCELLED",
            user_id=cancelled_user_id,
            event_id=event_id,
            event_title=event_dto.title,
            starts_at=event_dto.starts_at,
            auth_header=auth_header,
        )

        if promoted_reg is not None:
            await self.notifications_api.send_registration_notification(
                notification_type="WAITLIST_PROMOTED",
                user_id=UUID(promoted_reg.user_id),
                event_id=event_id,
                event_title=event_dto.title,
                starts_at=event_dto.starts_at,
                auth_header=auth_header,
            )

        return reg

    def _promote_from_reserve_in_tx(
        self, event_id: UUID, max_capacity: int
    ) -> Registration | None:
        """Przesuwa najstarszy wpis RESERVE na MAIN (FIFO), jeśli jest wolne miejsce."""
        main_count = self.repository.count_main_list(event_id)
        if main_count >= max_capacity:
            return None

        next_reg = self.repository.find_oldest_reserve(event_id)
        if next_reg is None:
            return None

        next_reg.status = RegistrationStatus.MAIN
        self.repository.save(next_reg)
        return next_reg

    async def promote_from_reserve(
        self, event_id: UUID, auth_header: str | None = None
    ) -> Registration | None:
        """Publiczna metoda zgodna z diagramem klas (możliwa do wywołania np. po zwiększeniu limitu)."""
        event_dto = await self.events_api.get_event_details(
            event_id, auth_header=auth_header
        )
        try:
            self.repository.upsert_event_projection(
                event_id=event_id,
                max_capacity=event_dto.max_capacity,
                lock_for_update=True,
            )
            promoted = self._promote_from_reserve_in_tx(
                event_id=event_id,
                max_capacity=event_dto.max_capacity,
            )
            self.db.commit()
            if promoted is not None:
                self.db.refresh(promoted)
        except Exception:
            self.db.rollback()
            raise

        if promoted is not None:
            await self.notifications_api.send_registration_notification(
                notification_type="WAITLIST_PROMOTED",
                user_id=UUID(promoted.user_id),
                event_id=event_id,
                event_title=event_dto.title,
                starts_at=event_dto.starts_at,
                auth_header=auth_header,
            )
        return promoted

    async def update_registration_status(
        self,
        reg_id: UUID,
        new_status: RegistrationStatus,
        current_user: CurrentUser,
        auth_header: str | None = None,
    ) -> Registration:
        """Operacja UPDATE (PATCH) dla pełnego CRUD."""
        if new_status == RegistrationStatus.CANCELLED:
            return await self.cancel_registration(
                reg_id=reg_id,
                current_user=current_user,
                auth_header=auth_header,
            )

        # Ręczna zmiana na MAIN lub RESERVE wymaga uprawnień Organizatora/Admina
        if not current_user.has_any_role(ROLE_ORGANIZER, ROLE_ADMIN):
            raise forbidden_error(
                "Tylko organizator lub administrator może zmieniać listę uczestnika"
            )

        reg = self.repository.find_by_id(reg_id)
        if reg is None:
            raise registration_not_found_error()

        if reg.status == new_status:
            return reg

        event_id = UUID(reg.event_id)
        event_dto = await self.events_api.get_event_details(
            event_id, auth_header=auth_header
        )

        promoted_reg: Registration | None = None
        previous_status = reg.status

        try:
            self.repository.upsert_event_projection(
                event_id=event_id,
                max_capacity=event_dto.max_capacity,
                lock_for_update=True,
            )

            # Jeśli przywracamy anulowany zapis, sprawdź duplikaty
            if previous_status == RegistrationStatus.CANCELLED:
                active = self.repository.find_active_by_event_and_user(
                    event_id, UUID(reg.user_id)
                )
                if active is not None:
                    raise registration_duplicate_error()

            if new_status == RegistrationStatus.MAIN:
                main_count = self.repository.count_main_list(event_id)
                if main_count >= event_dto.max_capacity:
                    raise event_capacity_exceeded_error()

            reg.status = new_status
            if (
                previous_status == RegistrationStatus.MAIN
                and new_status == RegistrationStatus.RESERVE
            ):
                # Przesunięcie na koniec kolejki rezerwowej (FIFO)
                reg.created_at = datetime.now(timezone.utc)

            self.repository.save(reg)

            if (
                previous_status == RegistrationStatus.MAIN
                and new_status == RegistrationStatus.RESERVE
            ):
                promoted_reg = self._promote_from_reserve_in_tx(
                    event_id=event_id,
                    max_capacity=event_dto.max_capacity,
                )

            self.db.commit()
            self.db.refresh(reg)
        except Exception:
            self.db.rollback()
            raise

        if promoted_reg is not None:
            await self.notifications_api.send_registration_notification(
                notification_type="WAITLIST_PROMOTED",
                user_id=UUID(promoted_reg.user_id),
                event_id=event_id,
                event_title=event_dto.title,
                starts_at=event_dto.starts_at,
                auth_header=auth_header,
            )

        return reg

    def get_registration(
        self, reg_id: UUID, current_user: CurrentUser
    ) -> Registration:
        reg = self.repository.find_by_id(reg_id)
        if reg is None:
            raise registration_not_found_error()

        is_privileged = current_user.has_any_role(
            ROLE_ORGANIZER, ROLE_ADMIN, ROLE_SERVICE
        )
        if not is_privileged and reg.user_id != current_user.user_id:
            raise registration_not_found_error()
        return reg

    def get_registrations(
        self,
        *,
        current_user: CurrentUser,
        event_id: UUID | None = None,
        user_id: UUID | None = None,
        status: RegistrationStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[RegistrationResponse]:
        is_privileged = current_user.has_any_role(
            ROLE_ORGANIZER, ROLE_ADMIN, ROLE_SERVICE
        )

        # Zwykły uczestnik może przeglądać wyłącznie własną historię zapisów
        if not is_privileged:
            if user_id is not None and str(user_id) != current_user.user_id:
                raise forbidden_error("Nie możesz przeglądać zapisów innych użytkowników")
            if event_id is not None and user_id is None:
                raise forbidden_error("Tylko organizator może przeglądać pełną listę uczestników wydarzenia")
            effective_user_id: UUID | None = UUID(current_user.user_id)
        else:
            effective_user_id = user_id

        items, total_items = self.repository.list_paginated(
            event_id=event_id,
            user_id=effective_user_id,
            status=status,
            page=page,
            page_size=page_size,
        )
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0

        return PaginatedResponse[RegistrationResponse](
            items=[RegistrationResponse.model_validate(item) for item in items],
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        )