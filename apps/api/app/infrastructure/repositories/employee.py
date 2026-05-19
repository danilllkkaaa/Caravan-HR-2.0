from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import EmployeeDomain
from app.domain.repositories import AbstractEmployeeRepository
from app.infrastructure.models import Employee


def _employee_to_domain(emp: Employee) -> EmployeeDomain:
    return EmployeeDomain(
        id=emp.id,
        user_id=emp.user_id,
        external_id_1c=emp.external_id_1c,
        personnel_number=emp.personnel_number,
        first_name=emp.first_name,
        last_name=emp.last_name,
        middle_name=emp.middle_name,
        birth_date=emp.birth_date,
        phone=emp.phone,
        department_id=emp.department_id,
        position_id=emp.position_id,
        manager_id=emp.manager_id,
        role=emp.role,
        hire_date=emp.hire_date,
        work_location_id=emp.work_location_id,
        avatar_url=emp.avatar_url,
        sync_hash=emp.sync_hash,
        created_at=emp.created_at,
        updated_at=emp.updated_at,
    )


class EmployeeRepository(AbstractEmployeeRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, employee_id: uuid.UUID) -> EmployeeDomain | None:
        result = await self._session.get(Employee, employee_id)
        return _employee_to_domain(result) if result else None

    async def get_by_user_id(self, user_id: uuid.UUID) -> EmployeeDomain | None:
        stmt = select(Employee).where(Employee.user_id == user_id)
        result = await self._session.execute(stmt)
        emp = result.scalar_one_or_none()
        return _employee_to_domain(emp) if emp else None

    async def list_by_department(
        self, department_id: uuid.UUID, offset: int, limit: int
    ) -> tuple[list[EmployeeDomain], int]:
        base = select(Employee).where(Employee.department_id == department_id)
        count_result = await self._session.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = count_result.scalar_one()
        result = await self._session.execute(base.offset(offset).limit(limit))
        return [_employee_to_domain(e) for e in result.scalars().all()], total

    async def list_by_work_location(
        self,
        work_location_id: uuid.UUID,
        offset: int,
        limit: int,
        search: str | None = None,
        department_id: uuid.UUID | None = None,
    ) -> tuple[list[EmployeeDomain], int]:
        base = select(Employee).where(Employee.work_location_id == work_location_id)
        if department_id:
            base = base.where(Employee.department_id == department_id)
        if search:
            pattern = f"%{search}%"
            base = base.where(
                or_(
                    Employee.first_name.ilike(pattern),
                    Employee.last_name.ilike(pattern),
                    Employee.personnel_number.ilike(pattern),
                )
            )
        count_result = await self._session.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = count_result.scalar_one()
        result = await self._session.execute(base.offset(offset).limit(limit))
        return [_employee_to_domain(e) for e in result.scalars().all()], total

    async def list_all(
        self,
        offset: int,
        limit: int,
        search: str | None = None,
        department_id: uuid.UUID | None = None,
    ) -> tuple[list[EmployeeDomain], int]:
        base = select(Employee)
        if department_id:
            base = base.where(Employee.department_id == department_id)
        if search:
            pattern = f"%{search}%"
            base = base.where(
                or_(
                    Employee.first_name.ilike(pattern),
                    Employee.last_name.ilike(pattern),
                    Employee.personnel_number.ilike(pattern),
                )
            )
        count_result = await self._session.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = count_result.scalar_one()
        result = await self._session.execute(base.offset(offset).limit(limit))
        return [_employee_to_domain(e) for e in result.scalars().all()], total

    async def list_direct_reports(self, manager_id: uuid.UUID) -> list[EmployeeDomain]:
        stmt = select(Employee).where(Employee.manager_id == manager_id)
        result = await self._session.execute(stmt)
        return [_employee_to_domain(e) for e in result.scalars().all()]

    async def update_phone(self, employee_id: uuid.UUID, phone: str) -> EmployeeDomain:
        emp = await self._session.get(Employee, employee_id)
        if emp is None:
            raise ValueError(f"Employee {employee_id} not found")
        emp.phone = phone
        await self._session.flush()
        await self._session.refresh(emp)
        return _employee_to_domain(emp)

    async def upsert_from_1c(self, data: dict[str, Any]) -> EmployeeDomain:
        stmt = select(Employee).where(Employee.external_id_1c == data["external_id_1c"])
        result = await self._session.execute(stmt)
        emp = result.scalar_one_or_none()
        if emp is None:
            emp = Employee(id=uuid.uuid4(), **data)
            self._session.add(emp)
        else:
            for key, value in data.items():
                setattr(emp, key, value)
        await self._session.flush()
        await self._session.refresh(emp)
        return _employee_to_domain(emp)
