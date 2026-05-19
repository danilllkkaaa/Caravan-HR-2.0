from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import EmployeeDomain, VacationRequestDomain, VacationTypeDomain
from app.infrastructure.repositories.employee import EmployeeRepository
from app.infrastructure.repositories.vacation import VacationRepository


def _format_type(vt: VacationTypeDomain) -> dict[str, Any]:
    return {
        "id": str(vt.id),
        "code": vt.code,
        "name": vt.name,
        "is_paid": vt.is_paid,
        "requires_documents": vt.requires_documents,
    }


def _format_employee_summary(emp: EmployeeDomain) -> dict[str, Any]:
    return {
        "id": str(emp.id),
        "first_name": emp.first_name,
        "last_name": emp.last_name,
        "full_name": f"{emp.last_name} {emp.first_name}".strip(),
        "personnel_number": emp.personnel_number,
        "avatar_url": emp.avatar_url,
        "role": emp.role,
    }


def _base_request(
    vr: VacationRequestDomain,
    vacation_type: VacationTypeDomain | None,
    employee: EmployeeDomain | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": str(vr.id),
        "employee_id": str(vr.employee_id),
        "vacation_type_id": str(vr.vacation_type_id),
        "start_date": vr.start_date.isoformat(),
        "end_date": vr.end_date.isoformat(),
        "days_count": vr.days_count,
        "comment": vr.comment,
        "status": vr.status,
        "approver_id": str(vr.approver_id) if vr.approver_id else None,
        "approver_comment": vr.approver_comment,
        "approved_at": vr.approved_at.isoformat() if vr.approved_at else None,
        "created_at": vr.created_at.isoformat(),
        "updated_at": vr.updated_at.isoformat(),
    }
    if vacation_type:
        payload["vacation_type"] = _format_type(vacation_type)
    if employee:
        payload["employee"] = _format_employee_summary(employee)
    return payload


class VacationRequestSerializer:
    def __init__(self, session: AsyncSession) -> None:
        self._vacation_repo = VacationRepository(session)
        self._employee_repo = EmployeeRepository(session)

    async def one(
        self,
        vr: VacationRequestDomain,
        *,
        include_employee: bool = False,
    ) -> dict[str, Any]:
        vtype = await self._vacation_repo.get_type_by_id(vr.vacation_type_id)
        employee = None
        if include_employee:
            employee = await self._employee_repo.get_by_id(vr.employee_id)
        return _base_request(vr, vtype, employee)

    async def many(
        self,
        requests: list[VacationRequestDomain],
        *,
        include_employee: bool = False,
    ) -> list[dict[str, Any]]:
        if not requests:
            return []

        types = {t.id: t for t in await self._vacation_repo.list_types()}
        employees: dict[uuid.UUID, EmployeeDomain] = {}
        if include_employee:
            for vr in requests:
                if vr.employee_id not in employees:
                    emp = await self._employee_repo.get_by_id(vr.employee_id)
                    if emp:
                        employees[vr.employee_id] = emp

        return [
            _base_request(
                vr,
                types.get(vr.vacation_type_id),
                employees.get(vr.employee_id) if include_employee else None,
            )
            for vr in requests
        ]
