from __future__ import annotations

import uuid

import structlog

from app.core.exceptions import ForbiddenError, NotFoundError
from app.domain.models import EmployeeDomain
from app.domain.repositories import AbstractEmployeeRepository

log = structlog.get_logger(__name__)


class EmployeeService:
    def __init__(self, employee_repo: AbstractEmployeeRepository) -> None:
        self._repo = employee_repo

    async def get_by_id(self, employee_id: uuid.UUID) -> EmployeeDomain:
        emp = await self._repo.get_by_id(employee_id)
        if emp is None:
            raise NotFoundError(message=f"Employee {employee_id} not found")
        return emp

    async def get_my_profile(self, user_id: uuid.UUID) -> EmployeeDomain:
        emp = await self._repo.get_by_user_id(user_id)
        if emp is None:
            raise NotFoundError(message="Employee profile not found for this user")
        return emp

    async def list_employees(
        self,
        requester: EmployeeDomain,
        offset: int,
        limit: int,
        search: str | None = None,
        department_id: uuid.UUID | None = None,
    ) -> tuple[list[EmployeeDomain], int]:
        if requester.role == "admin":
            return await self._repo.list_all(offset, limit, search, department_id)
        elif requester.role == "hr":
            if requester.work_location_id is None:
                return [], 0
            return await self._repo.list_by_work_location(
                requester.work_location_id, offset, limit, search, department_id
            )
        elif requester.role == "manager":
            return await self._repo.list_by_department(
                requester.department_id, offset, limit
            )
        else:
            raise ForbiddenError(message="Insufficient permissions to list employees")

    async def list_direct_reports(self, requester: EmployeeDomain) -> list[EmployeeDomain]:
        if requester.role not in {"manager", "hr", "admin"}:
            raise ForbiddenError(message="Insufficient permissions to list direct reports")
        return await self._repo.list_direct_reports(requester.id)

    async def update_my_profile(
        self, requester: EmployeeDomain, phone: str
    ) -> EmployeeDomain:
        return await self._repo.update_phone(requester.id, phone)

    async def get_subordinate(
        self, requester: EmployeeDomain, employee_id: uuid.UUID
    ) -> EmployeeDomain:
        emp = await self._repo.get_by_id(employee_id)
        if emp is None:
            raise NotFoundError(message=f"Employee {employee_id} not found")

        if requester.role == "admin":
            return emp
        if requester.role == "hr":
            if emp.work_location_id != requester.work_location_id:
                raise ForbiddenError()
            return emp
        if requester.role == "manager":
            if emp.department_id != requester.department_id and emp.id != requester.id:
                raise ForbiddenError()
            return emp
        # employee role - own data only
        if emp.id != requester.id:
            raise ForbiddenError()
        return emp
