from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any

from app.domain.models import (
    EmployeeDomain,
    NotificationDomain,
    RefreshTokenDomain,
    SickLeaveDomain,
    TimesheetEntryDomain,
    UserDomain,
    VacationBalanceDomain,
    VacationRequestDomain,
    VacationTypeDomain,
)


class AbstractUserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: uuid.UUID) -> UserDomain | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> UserDomain | None: ...

    @abstractmethod
    async def create(self, email: str, password_hash: str) -> UserDomain: ...

    @abstractmethod
    async def update_failed_attempts(
        self, user_id: uuid.UUID, attempts: int, locked_until: datetime | None
    ) -> None: ...

    @abstractmethod
    async def reset_failed_attempts(self, user_id: uuid.UUID) -> None: ...

    @abstractmethod
    async def update_password_hash(self, user_id: uuid.UUID, password_hash: str) -> None: ...


class AbstractRefreshTokenRepository(ABC):
    @abstractmethod
    async def create(
        self,
        user_id: uuid.UUID,
        token_hash: str,
        device_info: dict[str, Any],
        expires_at: datetime,
    ) -> RefreshTokenDomain: ...

    @abstractmethod
    async def get_by_hash(self, token_hash: str) -> RefreshTokenDomain | None: ...

    @abstractmethod
    async def revoke(self, token_id: uuid.UUID) -> None: ...

    @abstractmethod
    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None: ...

    @abstractmethod
    async def list_active_for_user(self, user_id: uuid.UUID) -> list[RefreshTokenDomain]: ...

    @abstractmethod
    async def get_by_id(self, token_id: uuid.UUID) -> RefreshTokenDomain | None: ...


class AbstractEmployeeRepository(ABC):
    @abstractmethod
    async def get_by_id(self, employee_id: uuid.UUID) -> EmployeeDomain | None: ...

    @abstractmethod
    async def get_by_user_id(self, user_id: uuid.UUID) -> EmployeeDomain | None: ...

    @abstractmethod
    async def list_by_department(
        self, department_id: uuid.UUID, offset: int, limit: int
    ) -> tuple[list[EmployeeDomain], int]: ...

    @abstractmethod
    async def list_by_work_location(
        self,
        work_location_id: uuid.UUID,
        offset: int,
        limit: int,
        search: str | None = None,
        department_id: uuid.UUID | None = None,
    ) -> tuple[list[EmployeeDomain], int]: ...

    @abstractmethod
    async def list_all(
        self,
        offset: int,
        limit: int,
        search: str | None,
        department_id: uuid.UUID | None = None,
    ) -> tuple[list[EmployeeDomain], int]: ...

    @abstractmethod
    async def list_direct_reports(
        self, manager_id: uuid.UUID
    ) -> list[EmployeeDomain]: ...

    @abstractmethod
    async def update_phone(self, employee_id: uuid.UUID, phone: str) -> EmployeeDomain: ...

    @abstractmethod
    async def upsert_from_1c(self, data: dict[str, Any]) -> EmployeeDomain: ...


class AbstractVacationRepository(ABC):
    @abstractmethod
    async def get_request_by_id(
        self, request_id: uuid.UUID
    ) -> VacationRequestDomain | None: ...

    @abstractmethod
    async def list_requests(
        self,
        employee_id: uuid.UUID | None,
        status: str | None,
        offset: int,
        limit: int,
    ) -> tuple[list[VacationRequestDomain], int]: ...

    @abstractmethod
    async def create_request(
        self, employee_id: uuid.UUID, data: dict[str, Any]
    ) -> VacationRequestDomain: ...

    @abstractmethod
    async def update_request(
        self, request_id: uuid.UUID, data: dict[str, Any]
    ) -> VacationRequestDomain: ...

    @abstractmethod
    async def delete_request(self, request_id: uuid.UUID) -> None: ...

    @abstractmethod
    async def check_overlap(
        self,
        employee_id: uuid.UUID,
        start_date: date,
        end_date: date,
        exclude_id: uuid.UUID | None,
    ) -> bool: ...

    @abstractmethod
    async def get_balance(
        self, employee_id: uuid.UUID, year: int
    ) -> VacationBalanceDomain | None: ...

    @abstractmethod
    async def list_types(self) -> list[VacationTypeDomain]: ...

    @abstractmethod
    async def list_pending_for_manager(
        self, manager_id: uuid.UUID, offset: int, limit: int
    ) -> tuple[list[VacationRequestDomain], int]: ...

    @abstractmethod
    async def get_type_by_id(
        self, vacation_type_id: uuid.UUID
    ) -> VacationTypeDomain | None: ...

    @abstractmethod
    async def consume_balance(
        self, employee_id: uuid.UUID, year: int, days: float
    ) -> VacationBalanceDomain: ...

    @abstractmethod
    async def return_balance(
        self, employee_id: uuid.UUID, year: int, days: float
    ) -> VacationBalanceDomain: ...


class AbstractSickLeaveRepository(ABC):
    @abstractmethod
    async def get_by_id(self, sick_leave_id: uuid.UUID) -> SickLeaveDomain | None: ...

    @abstractmethod
    async def list_for_employee(
        self, employee_id: uuid.UUID, offset: int, limit: int
    ) -> tuple[list[SickLeaveDomain], int]: ...

    @abstractmethod
    async def get_open_for_employee(
        self, employee_id: uuid.UUID
    ) -> SickLeaveDomain | None: ...

    @abstractmethod
    async def create(self, employee_id: uuid.UUID, data: dict[str, Any]) -> SickLeaveDomain: ...

    @abstractmethod
    async def update(
        self, sick_leave_id: uuid.UUID, data: dict[str, Any]
    ) -> SickLeaveDomain: ...


class AbstractTimesheetRepository(ABC):
    @abstractmethod
    async def get_entry(
        self, employee_id: uuid.UUID, entry_date: date
    ) -> TimesheetEntryDomain | None: ...

    @abstractmethod
    async def get_entry_by_id(
        self, entry_id: uuid.UUID
    ) -> TimesheetEntryDomain | None: ...

    @abstractmethod
    async def list_entries(
        self,
        employee_id: uuid.UUID,
        date_from: date,
        date_to: date,
    ) -> list[TimesheetEntryDomain]: ...

    @abstractmethod
    async def upsert_entry(self, data: dict[str, Any]) -> TimesheetEntryDomain: ...


class AbstractNotificationRepository(ABC):
    @abstractmethod
    async def get_by_id(
        self, notification_id: uuid.UUID
    ) -> NotificationDomain | None: ...

    @abstractmethod
    async def list_for_employee(
        self,
        employee_id: uuid.UUID,
        offset: int,
        limit: int,
        unread_only: bool = False,
    ) -> tuple[list[NotificationDomain], int]: ...

    @abstractmethod
    async def count_unread(self, employee_id: uuid.UUID) -> int: ...

    @abstractmethod
    async def mark_read(self, notification_id: uuid.UUID, read_at: datetime) -> None: ...

    @abstractmethod
    async def mark_all_read(self, employee_id: uuid.UUID, read_at: datetime) -> None: ...

    @abstractmethod
    async def create(
        self, employee_id: uuid.UUID, data: dict[str, Any]
    ) -> NotificationDomain: ...
