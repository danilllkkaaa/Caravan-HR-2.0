from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import CurrentEmployee, DBSession, require_roles
from app.application.services.employee import EmployeeService
from app.domain.models import EmployeeDomain
from app.infrastructure.repositories.employee import EmployeeRepository

router = APIRouter(prefix="/employees", tags=["employees"])

ManagerOrAbove = Annotated[EmployeeDomain, Depends(require_roles("manager", "hr", "admin"))]


class EmployeeProfileUpdate(BaseModel):
    phone: str = Field(default="", max_length=32)


def _get_service(db: DBSession) -> EmployeeService:
    return EmployeeService(EmployeeRepository(db))


def _format_employee(emp: EmployeeDomain) -> dict[str, Any]:
    return {
        "id": str(emp.id),
        "user_id": str(emp.user_id),
        "external_id_1c": emp.external_id_1c,
        "personnel_number": emp.personnel_number,
        "first_name": emp.first_name,
        "last_name": emp.last_name,
        "middle_name": emp.middle_name,
        "birth_date": emp.birth_date.isoformat() if emp.birth_date else None,
        "phone": emp.phone,
        "department_id": str(emp.department_id),
        "position_id": str(emp.position_id),
        "manager_id": str(emp.manager_id) if emp.manager_id else None,
        "role": emp.role,
        "hire_date": emp.hire_date.isoformat(),
        "work_location_id": str(emp.work_location_id) if emp.work_location_id else None,
        "avatar_url": emp.avatar_url,
        "created_at": emp.created_at.isoformat(),
        "updated_at": emp.updated_at.isoformat(),
    }


@router.get("/me")
async def get_my_profile(employee: CurrentEmployee) -> dict[str, Any]:
    return _format_employee(employee)


@router.patch("/me")
async def update_my_profile(
    payload: EmployeeProfileUpdate,
    employee: CurrentEmployee,
    db: DBSession,
) -> dict[str, Any]:
    service = _get_service(db)
    updated = await service.update_my_profile(employee, payload.phone)
    return _format_employee(updated)


@router.get("")
async def list_employees(
    employee: ManagerOrAbove,
    db: DBSession,
    search: str | None = Query(default=None),
    department_id: uuid.UUID | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    service = _get_service(db)
    employees, total = await service.list_employees(
        employee, offset, limit, search, department_id
    )
    return {
        "items": [_format_employee(e) for e in employees],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.get("/direct-reports")
async def list_direct_reports(
    employee: ManagerOrAbove,
    db: DBSession,
) -> list[dict[str, Any]]:
    service = _get_service(db)
    return [_format_employee(emp) for emp in await service.list_direct_reports(employee)]


@router.get("/{employee_id}")
async def get_employee(
    employee_id: uuid.UUID,
    employee: CurrentEmployee,
    db: DBSession,
) -> dict[str, Any]:
    service = _get_service(db)
    target = await service.get_subordinate(employee, employee_id)
    return _format_employee(target)
