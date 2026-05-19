from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import SickLeaveDomain
from app.domain.repositories import AbstractSickLeaveRepository
from app.infrastructure.models import SickLeave


def _to_domain(sl: SickLeave) -> SickLeaveDomain:
    return SickLeaveDomain(
        id=sl.id,
        employee_id=sl.employee_id,
        start_date=sl.start_date,
        end_date=sl.end_date,
        open_comment=sl.open_comment,
        close_comment=sl.close_comment,
        document_url=sl.document_url,
        status=sl.status,
        closed_by=sl.closed_by,
        created_at=sl.created_at,
        updated_at=sl.updated_at,
    )


class SickLeaveRepository(AbstractSickLeaveRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, sick_leave_id: uuid.UUID) -> SickLeaveDomain | None:
        result = await self._session.get(SickLeave, sick_leave_id)
        return _to_domain(result) if result else None

    async def list_for_employee(
        self, employee_id: uuid.UUID, offset: int, limit: int
    ) -> tuple[list[SickLeaveDomain], int]:
        base = select(SickLeave).where(SickLeave.employee_id == employee_id)
        count_result = await self._session.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = count_result.scalar_one()
        result = await self._session.execute(
            base.order_by(SickLeave.created_at.desc()).offset(offset).limit(limit)
        )
        return [_to_domain(sl) for sl in result.scalars().all()], total

    async def get_open_for_employee(
        self, employee_id: uuid.UUID
    ) -> SickLeaveDomain | None:
        stmt = select(SickLeave).where(
            SickLeave.employee_id == employee_id,
            SickLeave.status == "open",
        )
        result = await self._session.execute(stmt)
        sl = result.scalar_one_or_none()
        return _to_domain(sl) if sl else None

    async def create(
        self, employee_id: uuid.UUID, data: dict[str, Any]
    ) -> SickLeaveDomain:
        sl = SickLeave(id=uuid.uuid4(), employee_id=employee_id, **data)
        self._session.add(sl)
        await self._session.flush()
        await self._session.refresh(sl)
        return _to_domain(sl)

    async def update(
        self, sick_leave_id: uuid.UUID, data: dict[str, Any]
    ) -> SickLeaveDomain:
        sl = await self._session.get(SickLeave, sick_leave_id)
        if sl is None:
            raise ValueError(f"SickLeave {sick_leave_id} not found")
        for key, value in data.items():
            setattr(sl, key, value)
        await self._session.flush()
        await self._session.refresh(sl)
        return _to_domain(sl)
