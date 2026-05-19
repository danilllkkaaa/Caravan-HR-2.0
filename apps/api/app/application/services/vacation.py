from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import Any

import structlog

from app.application.services.notification import NotificationService
from app.application.vacation_calendar import (
    SHORT_NOTICE_DAYS,
    count_vacation_days,
    days_until_start,
)
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    InsufficientBalanceError,
    InvalidDateRangeError,
    NotFoundError,
    VacationOverlapError,
    VacationTypeNotFoundError,
)
from app.domain.models import (
    EmployeeDomain,
    VacationBalanceDomain,
    VacationRequestDomain,
    VacationTypeDomain,
)
from app.domain.repositories import AbstractEmployeeRepository, AbstractVacationRepository
from app.infrastructure.repositories.audit import AuditRepository
from app.infrastructure.repositories.holiday import HolidayRepository

log = structlog.get_logger(__name__)


class VacationService:
    def __init__(
        self,
        vacation_repo: AbstractVacationRepository,
        employee_repo: AbstractEmployeeRepository,
        holiday_repo: HolidayRepository,
        notification_service: NotificationService,
        audit_repo: AuditRepository,
    ) -> None:
        self._repo = vacation_repo
        self._employee_repo = employee_repo
        self._holiday_repo = holiday_repo
        self._notifications = notification_service
        self._audit = audit_repo

    async def list_types(self) -> list[VacationTypeDomain]:
        return await self._repo.list_types()

    async def get_balance(
        self, employee_id: uuid.UUID, year: int | None = None
    ) -> VacationBalanceDomain | None:
        if year is None:
            year = datetime.now(UTC).year
        return await self._repo.get_balance(employee_id, year)

    async def check_overlap(
        self,
        employee_id: uuid.UUID,
        start_date: date,
        end_date: date,
        exclude_id: uuid.UUID | None = None,
    ) -> bool:
        self._validate_date_range(start_date, end_date)
        return await self._repo.check_overlap(employee_id, start_date, end_date, exclude_id)

    async def create_request(
        self,
        employee_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        vacation_type_id: uuid.UUID,
        start_date: date,
        end_date: date,
        comment: str | None,
        submit: bool = True,
        actor_ip: str = "127.0.0.1",
    ) -> tuple[VacationRequestDomain, dict[str, Any]]:
        self._validate_date_range(start_date, end_date)

        vtype = await self._repo.get_type_by_id(vacation_type_id)
        if vtype is None:
            raise VacationTypeNotFoundError()

        holiday_dates = await self._holiday_repo.dates_between(start_date, end_date)
        days_count = count_vacation_days(start_date, end_date, holiday_dates)

        if await self._repo.check_overlap(employee_id, start_date, end_date, None):
            raise VacationOverlapError()

        if vtype.is_paid:
            await self._ensure_sufficient_balance(employee_id, start_date.year, days_count)

        employee = await self._employee_repo.get_by_id(employee_id)
        status = "pending" if submit else "draft"
        approver_id = employee.manager_id if employee and submit else None

        data: dict[str, Any] = {
            "vacation_type_id": vacation_type_id,
            "start_date": start_date,
            "end_date": end_date,
            "days_count": days_count,
            "comment": comment,
            "status": status,
            "approver_id": approver_id,
        }
        vr = await self._repo.create_request(employee_id, data)

        await self._audit.log(
            actor_user_id,
            "vacation.create",
            "vacation_request",
            str(vr.id),
            {"status": status, "days_count": days_count},
            ip=actor_ip,
        )

        if status == "pending" and approver_id:
            await self._notify_manager_new_request(vr, employee, approver_id)

        warnings = self._build_warnings(start_date)
        log.info(
            "Vacation request created",
            request_id=str(vr.id),
            employee_id=str(employee_id),
            status=status,
        )
        return vr, warnings

    async def get_request(
        self,
        request_id: uuid.UUID,
        requester_employee_id: uuid.UUID,
        role: str,
    ) -> VacationRequestDomain:
        vr = await self._repo.get_request_by_id(request_id)
        if vr is None:
            raise NotFoundError(message="Vacation request not found")
        if not await self._can_read(vr, requester_employee_id, role):
            raise ForbiddenError()
        return vr

    async def update_request(
        self,
        request_id: uuid.UUID,
        requester_employee_id: uuid.UUID,
        role: str,
        data: dict[str, Any],
        submit: bool = False,
        actor_user_id: uuid.UUID | None = None,
        actor_ip: str = "127.0.0.1",
    ) -> tuple[VacationRequestDomain, dict[str, Any]]:
        vr = await self._repo.get_request_by_id(request_id)
        if vr is None:
            raise NotFoundError(message="Vacation request not found")
        if vr.employee_id != requester_employee_id:
            raise ForbiddenError()
        if vr.status not in ("draft",):
            raise ConflictError(message="Only draft requests can be updated")

        new_start = data.get("start_date", vr.start_date)
        new_end = data.get("end_date", vr.end_date)
        self._validate_date_range(new_start, new_end)

        holiday_dates = await self._holiday_repo.dates_between(new_start, new_end)
        data["days_count"] = count_vacation_days(new_start, new_end, holiday_dates)

        if await self._repo.check_overlap(
            vr.employee_id, new_start, new_end, exclude_id=request_id
        ):
            raise VacationOverlapError()

        vtype = await self._repo.get_type_by_id(
            data.get("vacation_type_id", vr.vacation_type_id)
        )
        if vtype and vtype.is_paid:
            await self._ensure_sufficient_balance(
                vr.employee_id, new_start.year, data["days_count"]
            )

        if submit:
            employee = await self._employee_repo.get_by_id(vr.employee_id)
            data["status"] = "pending"
            data["approver_id"] = employee.manager_id if employee else None

        updated = await self._repo.update_request(request_id, data)

        if submit and actor_user_id:
            await self._audit.log(
                actor_user_id,
                "vacation.submit",
                "vacation_request",
                str(request_id),
                {"status": "pending"},
                ip=actor_ip,
            )
            if updated.approver_id:
                employee = await self._employee_repo.get_by_id(vr.employee_id)
                await self._notify_manager_new_request(updated, employee, updated.approver_id)

        warnings = self._build_warnings(updated.start_date)
        return updated, warnings

    async def cancel_request(
        self,
        request_id: uuid.UUID,
        requester_employee_id: uuid.UUID,
        role: str,
        actor_user_id: uuid.UUID,
        actor_ip: str = "127.0.0.1",
    ) -> VacationRequestDomain:
        vr = await self._repo.get_request_by_id(request_id)
        if vr is None:
            raise NotFoundError(message="Vacation request not found")
        if vr.employee_id != requester_employee_id and role not in ("hr", "admin"):
            raise ForbiddenError()

        is_privileged = role in ("hr", "admin")
        if vr.status == "pending":
            pass  # any authorized user can withdraw a pending request
        elif vr.status == "approved" and is_privileged:
            pass  # HR/admin may revoke an already-approved vacation
        else:
            raise ConflictError(
                message=(
                    "Only pending requests can be withdrawn; approved requests "
                    "can only be cancelled by HR or admin"
                )
            )

        previous_status = vr.status
        updated = await self._repo.update_request(request_id, {"status": "cancelled"})

        # When revoking an approved paid vacation restore the balance
        if previous_status == "approved":
            vtype = await self._repo.get_type_by_id(vr.vacation_type_id)
            if vtype and vtype.is_paid:
                await self._repo.return_balance(
                    vr.employee_id, vr.start_date.year, float(vr.days_count)
                )

            await self._notifications.create(
                vr.employee_id,
                "info",
                "Отпуск отменён кадровиком",
                (
                    f"Ваш отпуск с {vr.start_date} по {vr.end_date} был отменён. "
                    f"{vr.days_count} дн. возвращено на баланс."
                    if (vtype and vtype.is_paid)
                    else f"Ваш отпуск с {vr.start_date} по {vr.end_date} был отменён."
                ),
                payload={"vacation_request_id": str(vr.id)},
            )

        await self._audit.log(
            actor_user_id,
            "vacation.cancel",
            "vacation_request",
            str(request_id),
            {"previous_status": previous_status},
            ip=actor_ip,
        )
        return updated

    async def list_requests(
        self,
        employee_id: uuid.UUID,
        role: str,
        status_filter: str | None,
        offset: int,
        limit: int,
    ) -> tuple[list[VacationRequestDomain], int]:
        return await self._repo.list_requests(employee_id, status_filter, offset, limit)

    async def approve_request(
        self,
        request_id: uuid.UUID,
        approver: EmployeeDomain,
        comment: str | None,
        actor_ip: str = "127.0.0.1",
    ) -> VacationRequestDomain:
        vr = await self._repo.get_request_by_id(request_id)
        if vr is None:
            raise NotFoundError(message="Vacation request not found")
        if vr.status != "pending":
            raise ConflictError(message="Only pending requests can be approved")

        await self._check_approval_access(vr, approver)

        vtype = await self._repo.get_type_by_id(vr.vacation_type_id)
        if vtype and vtype.is_paid:
            await self._ensure_sufficient_balance(
                vr.employee_id, vr.start_date.year, vr.days_count
            )

        data = {
            "status": "approved",
            "approver_id": approver.id,
            "approver_comment": comment,
            "approved_at": datetime.now(UTC),
        }
        updated = await self._repo.update_request(request_id, data)

        if vtype and vtype.is_paid:
            await self._repo.consume_balance(
                vr.employee_id, vr.start_date.year, float(vr.days_count)
            )

        await self._notifications.create(
            vr.employee_id,
            "approved",
            "Отпуск одобрен",
            f"Заявление на отпуск с {vr.start_date} по {vr.end_date} одобрено.",
            payload={"vacation_request_id": str(vr.id)},
        )

        await self._audit.log(
            approver.user_id,
            "vacation.approve",
            "vacation_request",
            str(request_id),
            {"approver_comment": comment},
            ip=actor_ip,
        )

        log.info(
            "Vacation request approved",
            request_id=str(request_id),
            approver_id=str(approver.id),
        )
        return updated

    async def reject_request(
        self,
        request_id: uuid.UUID,
        approver: EmployeeDomain,
        comment: str,
        actor_ip: str = "127.0.0.1",
    ) -> VacationRequestDomain:
        if not comment.strip():
            raise ConflictError(message="Rejection comment is required")

        vr = await self._repo.get_request_by_id(request_id)
        if vr is None:
            raise NotFoundError(message="Vacation request not found")
        if vr.status != "pending":
            raise ConflictError(message="Only pending requests can be rejected")

        await self._check_approval_access(vr, approver)

        data = {
            "status": "rejected",
            "approver_id": approver.id,
            "approver_comment": comment,
        }
        updated = await self._repo.update_request(request_id, data)

        await self._notifications.create(
            vr.employee_id,
            "rejected",
            "Отпуск отклонён",
            f"Заявление отклонено. Причина: {comment}",
            payload={"vacation_request_id": str(vr.id)},
        )

        await self._audit.log(
            approver.user_id,
            "vacation.reject",
            "vacation_request",
            str(request_id),
            {"approver_comment": comment},
            ip=actor_ip,
        )

        log.info(
            "Vacation request rejected",
            request_id=str(request_id),
            approver_id=str(approver.id),
        )
        return updated

    async def list_pending_approvals(
        self,
        approver: EmployeeDomain,
        offset: int,
        limit: int,
    ) -> tuple[list[VacationRequestDomain], int]:
        if approver.role not in ("manager", "hr", "admin"):
            raise ForbiddenError()
        if approver.role == "manager":
            return await self._repo.list_pending_for_manager(approver.id, offset, limit)
        return await self._repo.list_requests(None, "pending", offset, limit)

    async def _ensure_sufficient_balance(
        self, employee_id: uuid.UUID, year: int, days_count: int
    ) -> None:
        balance = await self._repo.get_balance(employee_id, year)
        available = float(balance.available_days) if balance else 0.0
        if available < days_count:
            raise InsufficientBalanceError(
                details={"available": available, "requested": days_count}
            )

    async def _notify_manager_new_request(
        self,
        vr: VacationRequestDomain,
        employee: EmployeeDomain | None,
        manager_id: uuid.UUID,
    ) -> None:
        name = "Сотрудник"
        if employee:
            name = f"{employee.last_name} {employee.first_name}".strip()
        await self._notifications.create(
            manager_id,
            "info",
            "Новая заявка на отпуск",
            f"{name} подал(а) заявку на отпуск с {vr.start_date} по {vr.end_date}.",
            payload={"vacation_request_id": str(vr.id), "employee_id": str(vr.employee_id)},
        )

    async def _check_approval_access(
        self, vr: VacationRequestDomain, approver: EmployeeDomain
    ) -> None:
        if approver.role in ("hr", "admin"):
            return
        if approver.role != "manager":
            raise ForbiddenError()
        if vr.approver_id == approver.id:
            return
        emp = await self._employee_repo.get_by_id(vr.employee_id)
        if emp is None or emp.manager_id != approver.id:
            raise ForbiddenError()

    async def _can_read(
        self,
        vr: VacationRequestDomain,
        requester_id: uuid.UUID,
        role: str,
    ) -> bool:
        if role in ("admin", "hr"):
            return True
        if vr.employee_id == requester_id:
            return True
        if role == "manager":
            if vr.approver_id == requester_id:
                return True
            emp = await self._employee_repo.get_by_id(vr.employee_id)
            return emp is not None and emp.manager_id == requester_id
        return False

    @staticmethod
    def _validate_date_range(start_date: date, end_date: date) -> None:
        if end_date < start_date:
            raise InvalidDateRangeError()

    @staticmethod
    def _build_warnings(start_date: date) -> dict[str, Any]:
        today = datetime.now(UTC).date()
        warnings: dict[str, Any] = {}
        days_before = days_until_start(start_date, today)
        if days_before < SHORT_NOTICE_DAYS:
            warnings["short_notice"] = (
                f"До начала отпуска менее {SHORT_NOTICE_DAYS} дней "
                f"(осталось {max(days_before, 0)})."
            )
        return warnings
