from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.application.services.notification import NotificationService
from app.application.services.vacation import VacationService
from app.core.exceptions import (
    InsufficientBalanceError,
    InvalidDateRangeError,
    VacationOverlapError,
)
from app.domain.models import (
    EmployeeDomain,
    VacationBalanceDomain,
    VacationRequestDomain,
    VacationTypeDomain,
)
from app.infrastructure.repositories.audit import AuditRepository
from app.infrastructure.repositories.holiday import HolidayRepository


def _employee(manager_id: uuid.UUID | None = None) -> EmployeeDomain:
    return EmployeeDomain(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        external_id_1c="E1",
        personnel_number="P1",
        first_name="Ivan",
        last_name="Petrov",
        middle_name="",
        birth_date=None,
        phone="",
        department_id=uuid.uuid4(),
        position_id=uuid.uuid4(),
        manager_id=manager_id,
        role="employee",
        hire_date=date(2020, 1, 1),
        work_location_id=None,
        avatar_url=None,
        sync_hash="x",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _paid_type() -> VacationTypeDomain:
    return VacationTypeDomain(
        id=uuid.uuid4(),
        code="ANNUAL",
        name="Annual",
        is_paid=True,
        requires_documents=False,
    )


@pytest.fixture
def service() -> VacationService:
    vacation_repo = AsyncMock()
    employee_repo = AsyncMock()
    holiday_repo = AsyncMock(spec=HolidayRepository)
    holiday_repo.dates_between = AsyncMock(return_value=set())
    notification_service = AsyncMock(spec=NotificationService)
    notification_service.create = AsyncMock()
    audit_repo = AsyncMock(spec=AuditRepository)
    audit_repo.log = AsyncMock()
    return VacationService(
        vacation_repo=vacation_repo,
        employee_repo=employee_repo,
        holiday_repo=holiday_repo,
        notification_service=notification_service,
        audit_repo=audit_repo,
    )


@pytest.mark.asyncio
async def test_create_request_rejects_invalid_dates(service: VacationService) -> None:
    emp = _employee()
    with pytest.raises(InvalidDateRangeError):
        await service.create_request(
            employee_id=emp.id,
            actor_user_id=emp.user_id,
            vacation_type_id=uuid.uuid4(),
            start_date=date(2026, 8, 10),
            end_date=date(2026, 8, 1),
            comment=None,
        )


@pytest.mark.asyncio
async def test_create_request_rejects_overlap(service: VacationService) -> None:
    emp = _employee()
    vtype = _paid_type()
    service._repo.get_type_by_id = AsyncMock(return_value=vtype)
    service._repo.check_overlap = AsyncMock(return_value=True)
    service._employee_repo.get_by_id = AsyncMock(return_value=emp)

    with pytest.raises(VacationOverlapError):
        await service.create_request(
            employee_id=emp.id,
            actor_user_id=emp.user_id,
            vacation_type_id=vtype.id,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 10),
            comment=None,
        )


@pytest.mark.asyncio
async def test_create_request_rejects_insufficient_balance(service: VacationService) -> None:
    emp = _employee()
    vtype = _paid_type()
    service._repo.get_type_by_id = AsyncMock(return_value=vtype)
    service._repo.check_overlap = AsyncMock(return_value=False)
    service._repo.get_balance = AsyncMock(
        return_value=VacationBalanceDomain(
            id=uuid.uuid4(),
            employee_id=emp.id,
            year=2026,
            total_days=Decimal("5"),
            used_days=Decimal("0"),
            sync_source="manual",
            updated_at=datetime.now(UTC),
        )
    )
    service._employee_repo.get_by_id = AsyncMock(return_value=emp)

    with pytest.raises(InsufficientBalanceError):
        await service.create_request(
            employee_id=emp.id,
            actor_user_id=emp.user_id,
            vacation_type_id=vtype.id,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 14),
            comment=None,
        )


@pytest.mark.asyncio
async def test_approve_request_consumes_balance(service: VacationService) -> None:
    manager = _employee()
    manager.role = "manager"
    manager.id = uuid.uuid4()

    vr = VacationRequestDomain(
        id=uuid.uuid4(),
        employee_id=uuid.uuid4(),
        vacation_type_id=uuid.uuid4(),
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 5),
        days_count=5,
        comment=None,
        status="pending",
        approver_id=manager.id,
        approver_comment=None,
        approved_at=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    vtype = _paid_type()
    vtype.id = vr.vacation_type_id

    service._repo.get_request_by_id = AsyncMock(return_value=vr)
    service._repo.get_type_by_id = AsyncMock(return_value=vtype)
    service._repo.get_balance = AsyncMock(
        return_value=VacationBalanceDomain(
            id=uuid.uuid4(),
            employee_id=vr.employee_id,
            year=2026,
            total_days=Decimal("20"),
            used_days=Decimal("0"),
            sync_source="manual",
            updated_at=datetime.now(UTC),
        )
    )
    approved = VacationRequestDomain(
        id=vr.id,
        employee_id=vr.employee_id,
        vacation_type_id=vr.vacation_type_id,
        start_date=vr.start_date,
        end_date=vr.end_date,
        days_count=vr.days_count,
        comment=vr.comment,
        status="approved",
        approver_id=manager.id,
        approver_comment=None,
        approved_at=datetime.now(UTC),
        created_at=vr.created_at,
        updated_at=datetime.now(UTC),
    )
    service._repo.update_request = AsyncMock(return_value=approved)
    service._repo.consume_balance = AsyncMock()

    await service.approve_request(vr.id, manager, None)

    service._repo.consume_balance.assert_awaited_once_with(
        vr.employee_id, 2026, float(vr.days_count)
    )
    service._notifications.create.assert_awaited()


@pytest.mark.asyncio
async def test_approve_request_stops_if_locked_balance_is_insufficient(
    service: VacationService,
) -> None:
    manager = _employee()
    manager.role = "manager"

    vr = VacationRequestDomain(
        id=uuid.uuid4(),
        employee_id=uuid.uuid4(),
        vacation_type_id=uuid.uuid4(),
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 5),
        days_count=5,
        comment=None,
        status="pending",
        approver_id=manager.id,
        approver_comment=None,
        approved_at=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    approved = VacationRequestDomain(
        id=vr.id,
        employee_id=vr.employee_id,
        vacation_type_id=vr.vacation_type_id,
        start_date=vr.start_date,
        end_date=vr.end_date,
        days_count=vr.days_count,
        comment=vr.comment,
        status="approved",
        approver_id=manager.id,
        approver_comment=None,
        approved_at=datetime.now(UTC),
        created_at=vr.created_at,
        updated_at=datetime.now(UTC),
    )
    balance = VacationBalanceDomain(
        id=uuid.uuid4(),
        employee_id=vr.employee_id,
        year=2026,
        total_days=Decimal("20"),
        used_days=Decimal("0"),
        sync_source="manual",
        updated_at=datetime.now(UTC),
    )

    service._repo.get_request_by_id = AsyncMock(return_value=vr)
    service._repo.get_type_by_id = AsyncMock(return_value=_paid_type())
    service._repo.get_balance = AsyncMock(return_value=balance)
    service._repo.update_request = AsyncMock(return_value=approved)
    service._repo.consume_balance = AsyncMock(side_effect=InsufficientBalanceError())

    with pytest.raises(InsufficientBalanceError):
        await service.approve_request(vr.id, manager, None)

    service._notifications.create.assert_not_awaited()
    service._audit.log.assert_not_awaited()
