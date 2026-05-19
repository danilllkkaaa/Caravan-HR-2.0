from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import CurrentEmployee, DBSession
from app.infrastructure.models import TimesheetEntry

router = APIRouter(prefix="/timesheet", tags=["timesheet"])


def _format_entry(e: TimesheetEntry) -> dict[str, Any]:
    return {
        "id": str(e.id),
        "employee_id": str(e.employee_id),
        "date": e.date.isoformat(),
        "first_entry_at": e.first_entry_at.isoformat() if e.first_entry_at else None,
        "last_exit_at": e.last_exit_at.isoformat() if e.last_exit_at else None,
        "worked_minutes": e.worked_minutes,
        "status": e.status,
        "schedule_minutes": e.schedule_minutes,
        "created_at": e.created_at.isoformat(),
        "updated_at": e.updated_at.isoformat(),
    }


@router.get("")
async def list_timesheet(
    employee: CurrentEmployee,
    db: DBSession,
    date_from: date = Query(default=None),
    date_to: date = Query(default=None),
) -> dict[str, Any]:
    today = date.today()
    if date_from is None:
        date_from = today.replace(day=1)
    if date_to is None:
        date_to = today

    stmt = (
        select(TimesheetEntry)
        .where(
            TimesheetEntry.employee_id == employee.id,
            TimesheetEntry.date >= date_from,
            TimesheetEntry.date <= date_to,
        )
        .order_by(TimesheetEntry.date)
    )
    result = await db.execute(stmt)
    entries = result.scalars().all()
    return {
        "items": [_format_entry(e) for e in entries],
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
    }


@router.get("/summary")
async def get_timesheet_summary(
    employee: CurrentEmployee,
    db: DBSession,
    date_from: date = Query(default=None),
    date_to: date = Query(default=None),
) -> dict[str, Any]:
    today = date.today()
    if date_from is None:
        date_from = today.replace(day=1)
    if date_to is None:
        date_to = today

    stmt = (
        select(TimesheetEntry)
        .where(
            TimesheetEntry.employee_id == employee.id,
            TimesheetEntry.date >= date_from,
            TimesheetEntry.date <= date_to,
        )
    )
    result = await db.execute(stmt)
    entries = result.scalars().all()

    total_worked = sum(e.worked_minutes for e in entries)
    total_scheduled = sum(e.schedule_minutes or 0 for e in entries)
    status_counts: dict[str, int] = {}
    for e in entries:
        status_counts[e.status] = status_counts.get(e.status, 0) + 1

    return {
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "total_worked_minutes": total_worked,
        "total_scheduled_minutes": total_scheduled,
        "total_worked_hours": round(total_worked / 60, 2),
        "days_count": len(entries),
        "status_breakdown": status_counts,
    }


@router.get("/entries/{entry_id}")
async def get_timesheet_entry(
    entry_id: uuid.UUID,
    employee: CurrentEmployee,
    db: DBSession,
) -> dict[str, Any]:
    from app.core.exceptions import ForbiddenError, NotFoundError

    result = await db.get(TimesheetEntry, entry_id)
    if result is None:
        raise NotFoundError(message="Timesheet entry not found")
    if result.employee_id != employee.id and employee.role not in ("admin", "hr", "manager"):
        raise ForbiddenError()
    return _format_entry(result)
