from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal


@dataclass
class UserDomain:
    id: uuid.UUID
    email: str
    password_hash: str
    is_active: bool
    failed_login_attempts: int
    locked_until: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass
class EmployeeDomain:
    id: uuid.UUID
    user_id: uuid.UUID
    external_id_1c: str
    personnel_number: str
    first_name: str
    last_name: str
    middle_name: str
    birth_date: date | None
    phone: str
    department_id: uuid.UUID
    position_id: uuid.UUID
    manager_id: uuid.UUID | None
    role: str
    hire_date: date
    work_location_id: uuid.UUID | None
    avatar_url: str | None
    sync_hash: str
    created_at: datetime
    updated_at: datetime


@dataclass
class DepartmentDomain:
    id: uuid.UUID
    external_id_1c: str
    name: str
    parent_id: uuid.UUID | None
    head_id: uuid.UUID | None


@dataclass
class PositionDomain:
    id: uuid.UUID
    external_id_1c: str
    name: str


@dataclass
class WorkLocationDomain:
    id: uuid.UUID
    external_id_1c: str
    name: str
    city: str
    hr_employee_id: uuid.UUID | None


@dataclass
class VacationTypeDomain:
    id: uuid.UUID
    code: str
    name: str
    is_paid: bool
    requires_documents: bool


@dataclass
class VacationBalanceDomain:
    id: uuid.UUID
    employee_id: uuid.UUID
    year: int
    total_days: Decimal
    used_days: Decimal
    sync_source: str
    updated_at: datetime

    @property
    def available_days(self) -> Decimal:
        return self.total_days - self.used_days


@dataclass
class VacationRequestDomain:
    id: uuid.UUID
    employee_id: uuid.UUID
    vacation_type_id: uuid.UUID
    start_date: date
    end_date: date
    days_count: int
    comment: str | None
    status: str
    approver_id: uuid.UUID | None
    approver_comment: str | None
    approved_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass
class SickLeaveDomain:
    id: uuid.UUID
    employee_id: uuid.UUID
    start_date: date
    end_date: date | None
    open_comment: str | None
    close_comment: str | None
    document_url: str | None
    status: str
    closed_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


@dataclass
class TimesheetEntryDomain:
    id: uuid.UUID
    employee_id: uuid.UUID
    date: date
    first_entry_at: datetime | None
    last_exit_at: datetime | None
    worked_minutes: int
    status: str
    schedule_minutes: int | None
    created_at: datetime
    updated_at: datetime


@dataclass
class NotificationDomain:
    id: uuid.UUID
    employee_id: uuid.UUID
    type: str
    title: str
    body: str
    payload: dict | None
    read_at: datetime | None
    created_at: datetime


@dataclass
class RefreshTokenDomain:
    id: uuid.UUID
    user_id: uuid.UUID
    token_hash: str
    device_info: dict
    expires_at: datetime
    revoked_at: datetime | None
    created_at: datetime

    @property
    def is_valid(self) -> bool:

        now = datetime.now(UTC)
        return self.revoked_at is None and self.expires_at > now
