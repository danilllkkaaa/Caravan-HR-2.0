from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel


class VacationTypeOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    is_paid: bool
    requires_documents: bool

    model_config = {"from_attributes": True}


class VacationBalanceOut(BaseModel):
    year: int
    total_days: float
    used_days: float
    available_days: float


class OverlapCheckOut(BaseModel):
    has_overlap: bool


class EmployeeSummaryOut(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    full_name: str
    personnel_number: str | None = None
    avatar_url: str | None = None
    role: str

    model_config = {"from_attributes": True}


class VacationRequestOut(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    vacation_type_id: uuid.UUID
    start_date: date
    end_date: date
    days_count: int
    comment: str | None = None
    status: str
    approver_id: uuid.UUID | None = None
    approver_comment: str | None = None
    approved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    vacation_type: VacationTypeOut | None = None
    employee: EmployeeSummaryOut | None = None
    warnings: dict[str, str] | None = None

    model_config = {"from_attributes": True}


class PaginatedVacationOut(BaseModel):
    items: list[VacationRequestOut]
    total: int
    offset: int
    limit: int
