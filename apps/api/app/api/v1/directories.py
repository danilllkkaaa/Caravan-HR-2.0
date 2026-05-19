from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import CurrentEmployee, DBSession
from app.infrastructure.models import Department, Position

router = APIRouter(tags=["directories"])


@router.get("/departments")
async def list_departments(
    _employee: CurrentEmployee,
    db: DBSession,
) -> list[dict[str, Any]]:
    result = await db.execute(select(Department).order_by(Department.name))
    return [
        {
            "id": str(department.id),
            "external_id_1c": department.external_id_1c,
            "name": department.name,
            "parent_id": str(department.parent_id) if department.parent_id else None,
            "head_id": str(department.head_id) if department.head_id else None,
        }
        for department in result.scalars().all()
    ]


@router.get("/positions")
async def list_positions(
    _employee: CurrentEmployee,
    db: DBSession,
    department_id: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    stmt = select(Position).order_by(Position.name)
    result = await db.execute(stmt)
    return [
        {
            "id": str(position.id),
            "external_id_1c": position.external_id_1c,
            "name": position.name,
            "department_id": department_id,
        }
        for position in result.scalars().all()
    ]
