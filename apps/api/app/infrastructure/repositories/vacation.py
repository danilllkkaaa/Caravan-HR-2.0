from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import (
    VacationBalanceDomain,
    VacationRequestDomain,
    VacationTypeDomain,
)
from app.domain.repositories import AbstractVacationRepository
from app.infrastructure.models import (
    Employee,
    VacationBalance,
    VacationRequest,
    VacationType,
)


def _request_to_domain(vr: VacationRequest) -> VacationRequestDomain:
    return VacationRequestDomain(
        id=vr.id,
        employee_id=vr.employee_id,
        vacation_type_id=vr.vacation_type_id,
        start_date=vr.start_date,
        end_date=vr.end_date,
        days_count=vr.days_count,
        comment=vr.comment,
        status=vr.status,
        approver_id=vr.approver_id,
        approver_comment=vr.approver_comment,
        approved_at=vr.approved_at,
        created_at=vr.created_at,
        updated_at=vr.updated_at,
    )


def _balance_to_domain(vb: VacationBalance) -> VacationBalanceDomain:
    return VacationBalanceDomain(
        id=vb.id,
        employee_id=vb.employee_id,
        year=vb.year,
        total_days=vb.total_days,
        used_days=vb.used_days,
        sync_source=vb.sync_source,
        updated_at=vb.updated_at,
    )


def _type_to_domain(vt: VacationType) -> VacationTypeDomain:
    return VacationTypeDomain(
        id=vt.id,
        code=vt.code,
        name=vt.name,
        is_paid=vt.is_paid,
        requires_documents=vt.requires_documents,
    )


class VacationRepository(AbstractVacationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_request_by_id(
        self, request_id: uuid.UUID
    ) -> VacationRequestDomain | None:
        result = await self._session.get(VacationRequest, request_id)
        return _request_to_domain(result) if result else None

    async def list_requests(
        self,
        employee_id: uuid.UUID | None,
        status: str | None,
        offset: int,
        limit: int,
    ) -> tuple[list[VacationRequestDomain], int]:
        base = select(VacationRequest)
        if employee_id:
            base = base.where(VacationRequest.employee_id == employee_id)
        if status:
            base = base.where(VacationRequest.status == status)
        count_result = await self._session.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = count_result.scalar_one()
        result = await self._session.execute(
            base.order_by(VacationRequest.created_at.desc()).offset(offset).limit(limit)
        )
        return [_request_to_domain(r) for r in result.scalars().all()], total

    async def create_request(
        self, employee_id: uuid.UUID, data: dict[str, Any]
    ) -> VacationRequestDomain:
        vr = VacationRequest(id=uuid.uuid4(), employee_id=employee_id, **data)
        self._session.add(vr)
        await self._session.flush()
        await self._session.refresh(vr)
        return _request_to_domain(vr)

    async def update_request(
        self, request_id: uuid.UUID, data: dict[str, Any]
    ) -> VacationRequestDomain:
        vr = await self._session.get(VacationRequest, request_id)
        if vr is None:
            raise ValueError(f"VacationRequest {request_id} not found")
        for key, value in data.items():
            setattr(vr, key, value)
        await self._session.flush()
        await self._session.refresh(vr)
        return _request_to_domain(vr)

    async def delete_request(self, request_id: uuid.UUID) -> None:
        vr = await self._session.get(VacationRequest, request_id)
        if vr:
            await self._session.delete(vr)
            await self._session.flush()

    async def check_overlap(
        self,
        employee_id: uuid.UUID,
        start_date: date,
        end_date: date,
        exclude_id: uuid.UUID | None = None,
    ) -> bool:
        stmt = select(VacationRequest).where(
            VacationRequest.employee_id == employee_id,
            VacationRequest.status == "approved",
            VacationRequest.start_date <= end_date,
            VacationRequest.end_date >= start_date,
        )
        if exclude_id:
            stmt = stmt.where(VacationRequest.id != exclude_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_balance(
        self, employee_id: uuid.UUID, year: int
    ) -> VacationBalanceDomain | None:
        stmt = select(VacationBalance).where(
            VacationBalance.employee_id == employee_id,
            VacationBalance.year == year,
        )
        result = await self._session.execute(stmt)
        vb = result.scalar_one_or_none()
        return _balance_to_domain(vb) if vb else None

    async def list_types(self) -> list[VacationTypeDomain]:
        result = await self._session.execute(select(VacationType))
        return [_type_to_domain(t) for t in result.scalars().all()]

    async def get_type_by_id(
        self, vacation_type_id: uuid.UUID
    ) -> VacationTypeDomain | None:
        result = await self._session.get(VacationType, vacation_type_id)
        return _type_to_domain(result) if result else None

    async def consume_balance(
        self, employee_id: uuid.UUID, year: int, days: float
    ) -> VacationBalanceDomain:
        stmt = select(VacationBalance).where(
            VacationBalance.employee_id == employee_id,
            VacationBalance.year == year,
        )
        result = await self._session.execute(stmt)
        balance = result.scalar_one_or_none()
        if balance is None:
            raise ValueError(f"No vacation balance for employee {employee_id} year {year}")
        balance.used_days = balance.used_days + Decimal(str(days))
        await self._session.flush()
        await self._session.refresh(balance)
        return _balance_to_domain(balance)

    async def return_balance(
        self, employee_id: uuid.UUID, year: int, days: float
    ) -> VacationBalanceDomain:
        stmt = select(VacationBalance).where(
            VacationBalance.employee_id == employee_id,
            VacationBalance.year == year,
        )
        result = await self._session.execute(stmt)
        balance = result.scalar_one_or_none()
        if balance is None:
            raise ValueError(f"No vacation balance for employee {employee_id} year {year}")
        balance.used_days = max(Decimal("0"), balance.used_days - Decimal(str(days)))
        await self._session.flush()
        await self._session.refresh(balance)
        return _balance_to_domain(balance)

    async def list_pending_for_manager(
        self, manager_id: uuid.UUID, offset: int, limit: int
    ) -> tuple[list[VacationRequestDomain], int]:
        subordinate_ids_stmt = select(Employee.id).where(
            Employee.manager_id == manager_id
        )
        base = select(VacationRequest).where(
            VacationRequest.status == "pending",
            or_(
                VacationRequest.approver_id == manager_id,
                (
                    VacationRequest.approver_id.is_(None)
                    & VacationRequest.employee_id.in_(subordinate_ids_stmt)
                ),
            ),
        )
        count_result = await self._session.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = count_result.scalar_one()
        result = await self._session.execute(
            base.order_by(VacationRequest.created_at.asc()).offset(offset).limit(limit)
        )
        return [_request_to_domain(r) for r in result.scalars().all()], total
