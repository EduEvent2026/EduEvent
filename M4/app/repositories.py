from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import EventProjection, Registration, RegistrationStatus, UserProjection


class IRegistrationRepository(ABC):
    @abstractmethod
    def upsert_event_projection(
        self, event_id: UUID, max_capacity: int, lock_for_update: bool = False
    ) -> EventProjection:
        raise NotImplementedError

    @abstractmethod
    def ensure_user_projection(self, user_id: UUID) -> UserProjection:
        raise NotImplementedError

    @abstractmethod
    def save(self, reg: Registration) -> Registration:
        raise NotImplementedError

    @abstractmethod
    def find_by_id(self, reg_id: UUID) -> Registration | None:
        raise NotImplementedError

    @abstractmethod
    def find_active_by_event_and_user(
        self, event_id: UUID, user_id: UUID
    ) -> Registration | None:
        raise NotImplementedError

    @abstractmethod
    def count_main_list(self, event_id: UUID) -> int:
        raise NotImplementedError

    @abstractmethod
    def find_oldest_reserve(self, event_id: UUID) -> Registration | None:
        raise NotImplementedError

    @abstractmethod
    def list_paginated(
        self,
        *,
        event_id: UUID | None = None,
        user_id: UUID | None = None,
        status: RegistrationStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Registration], int]:
        raise NotImplementedError


class SqlAlchemyRegistrationRepository(IRegistrationRepository):
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert_event_projection(
        self, event_id: UUID, max_capacity: int, lock_for_update: bool = False
    ) -> EventProjection:
        stmt = select(EventProjection).where(EventProjection.id == str(event_id))
        if lock_for_update:
            stmt = stmt.with_for_update()

        projection = self.db.scalar(stmt)
        if projection is None:
            projection = EventProjection(id=str(event_id), max_capacity=max_capacity)
            self.db.add(projection)
            self.db.flush()
            if lock_for_update:
                projection = self.db.scalar(stmt) or projection
        else:
            projection.max_capacity = max_capacity
            self.db.flush()
        return projection

    def ensure_user_projection(self, user_id: UUID) -> UserProjection:
        projection = self.db.get(UserProjection, str(user_id))
        if projection is None:
            projection = UserProjection(id=str(user_id))
            self.db.add(projection)
            self.db.flush()
        return projection

    def save(self, reg: Registration) -> Registration:
        self.db.add(reg)
        self.db.flush()
        return reg

    def find_by_id(self, reg_id: UUID) -> Registration | None:
        return self.db.get(Registration, str(reg_id))

    def find_active_by_event_and_user(
        self, event_id: UUID, user_id: UUID
    ) -> Registration | None:
        stmt = (
            select(Registration)
            .where(
                Registration.event_id == str(event_id),
                Registration.user_id == str(user_id),
                Registration.status != RegistrationStatus.CANCELLED,
            )
            .limit(1)
        )
        return self.db.scalar(stmt)

    def count_main_list(self, event_id: UUID) -> int:
        stmt = select(func.count(Registration.id)).where(
            Registration.event_id == str(event_id),
            Registration.status == RegistrationStatus.MAIN,
        )
        return int(self.db.scalar(stmt) or 0)

    def find_oldest_reserve(self, event_id: UUID) -> Registration | None:
        stmt = (
            select(Registration)
            .where(
                Registration.event_id == str(event_id),
                Registration.status == RegistrationStatus.RESERVE,
            )
            .order_by(Registration.created_at.asc(), Registration.id.asc())
            .limit(1)
            .with_for_update()
        )
        return self.db.scalar(stmt)

    def list_paginated(
        self,
        *,
        event_id: UUID | None = None,
        user_id: UUID | None = None,
        status: RegistrationStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Registration], int]:
        filters = []
        if event_id is not None:
            filters.append(Registration.event_id == str(event_id))
        if user_id is not None:
            filters.append(Registration.user_id == str(user_id))
        if status is not None:
            filters.append(Registration.status == status)

        count_stmt = select(func.count(Registration.id)).where(*filters)
        total = int(self.db.scalar(count_stmt) or 0)

        items_stmt = (
            select(Registration)
            .where(*filters)
            .order_by(Registration.created_at.asc(), Registration.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(self.db.scalars(items_stmt).all())
        return items, total