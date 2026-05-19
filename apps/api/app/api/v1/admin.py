from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr

from app.api.deps import DBSession, require_roles
from app.core.security import hash_password
from app.domain.models import EmployeeDomain
from app.infrastructure.models import Employee, VacationBalance
from app.infrastructure.repositories.user import UserRepository

router = APIRouter(prefix="/admin", tags=["admin"])

AdminEmployee = Depends(require_roles("admin"))


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str
    is_active: bool = True


class UpdateEmployeeRoleRequest(BaseModel):
    role: str


class SetVacationBalanceRequest(BaseModel):
    year: int
    total_days: float
    sync_source: str = "manual"


class SyncTriggerRequest(BaseModel):
    task: str


@router.post("/users", status_code=201)
async def create_user(
    body: CreateUserRequest,
    db: DBSession,
    _: EmployeeDomain = AdminEmployee,
) -> dict[str, Any]:
    user_repo = UserRepository(db)
    existing = await user_repo.get_by_email(body.email)
    if existing:
        from app.core.exceptions import ConflictError
        raise ConflictError(message="User with this email already exists")

    user = await user_repo.create(body.email, hash_password(body.password))
    return {"id": str(user.id), "email": user.email, "is_active": user.is_active}


@router.patch("/employees/{employee_id}/role")
async def update_employee_role(
    employee_id: uuid.UUID,
    body: UpdateEmployeeRoleRequest,
    db: DBSession,
    _: EmployeeDomain = AdminEmployee,
) -> dict[str, Any]:
    from app.core.exceptions import NotFoundError

    valid_roles = {"employee", "manager", "hr", "admin"}
    if body.role not in valid_roles:
        from app.core.exceptions import ValidationError
        raise ValidationError(message=f"Invalid role. Must be one of: {valid_roles}")

    emp = await db.get(Employee, employee_id)
    if emp is None:
        raise NotFoundError(message="Employee not found")
    emp.role = body.role
    await db.flush()
    return {"id": str(emp.id), "role": emp.role}


@router.post("/employees/{employee_id}/vacation-balance")
async def set_vacation_balance(
    employee_id: uuid.UUID,
    body: SetVacationBalanceRequest,
    db: DBSession,
    _: EmployeeDomain = AdminEmployee,
) -> dict[str, Any]:
    from decimal import Decimal

    from sqlalchemy import select

    stmt = select(VacationBalance).where(
        VacationBalance.employee_id == employee_id,
        VacationBalance.year == body.year,
    )
    result = await db.execute(stmt)
    balance = result.scalar_one_or_none()

    if balance is None:
        balance = VacationBalance(
            id=uuid.uuid4(),
            employee_id=employee_id,
            year=body.year,
            total_days=Decimal(str(body.total_days)),
            used_days=Decimal("0"),
            sync_source=body.sync_source,
        )
        db.add(balance)
    else:
        balance.total_days = Decimal(str(body.total_days))
        balance.sync_source = body.sync_source

    await db.flush()
    return {
        "employee_id": str(employee_id),
        "year": body.year,
        "total_days": float(balance.total_days),
        "used_days": float(balance.used_days),
    }


@router.post("/sync/trigger")
async def trigger_sync(
    body: SyncTriggerRequest,
    _: EmployeeDomain = AdminEmployee,
) -> dict[str, str]:
    from app.workers.sync_tasks import (
        sync_departments,
        sync_employees,
        sync_positions,
        sync_vacation_balances,
    )

    task_map = {
        "sync_employees": sync_employees,
        "sync_vacation_balances": sync_vacation_balances,
        "sync_departments": sync_departments,
        "sync_positions": sync_positions,
    }

    task_fn = task_map.get(body.task)
    if task_fn is None:
        from app.core.exceptions import ValidationError
        raise ValidationError(message=f"Unknown task: {body.task}. Available: {list(task_map)}")

    task = task_fn.delay()
    return {"task_id": task.id, "task": body.task, "status": "queued"}
