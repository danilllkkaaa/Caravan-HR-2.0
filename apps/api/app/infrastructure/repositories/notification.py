from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import NotificationDomain
from app.domain.repositories import AbstractNotificationRepository
from app.infrastructure.models import Notification


def _to_domain(n: Notification) -> NotificationDomain:
    return NotificationDomain(
        id=n.id,
        employee_id=n.employee_id,
        type=n.type,
        title=n.title,
        body=n.body,
        payload=n.payload,
        read_at=n.read_at,
        created_at=n.created_at,
    )


class NotificationRepository(AbstractNotificationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, notification_id: uuid.UUID) -> NotificationDomain | None:
        result = await self._session.get(Notification, notification_id)
        return _to_domain(result) if result else None

    async def list_for_employee(
        self,
        employee_id: uuid.UUID,
        offset: int,
        limit: int,
        unread_only: bool = False,
    ) -> tuple[list[NotificationDomain], int]:
        base = select(Notification).where(Notification.employee_id == employee_id)
        if unread_only:
            base = base.where(Notification.read_at.is_(None))
        count_result = await self._session.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = count_result.scalar_one()
        result = await self._session.execute(
            base.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
        )
        return [_to_domain(n) for n in result.scalars().all()], total

    async def count_unread(self, employee_id: uuid.UUID) -> int:
        stmt = select(func.count()).where(
            Notification.employee_id == employee_id,
            Notification.read_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def mark_read(self, notification_id: uuid.UUID, read_at: datetime) -> None:
        stmt = (
            update(Notification)
            .where(Notification.id == notification_id)
            .values(read_at=read_at)
        )
        await self._session.execute(stmt)

    async def mark_all_read(self, employee_id: uuid.UUID, read_at: datetime) -> None:
        stmt = (
            update(Notification)
            .where(
                Notification.employee_id == employee_id,
                Notification.read_at.is_(None),
            )
            .values(read_at=read_at)
        )
        await self._session.execute(stmt)

    async def create(
        self, employee_id: uuid.UUID, data: dict[str, Any]
    ) -> NotificationDomain:
        n = Notification(id=uuid.uuid4(), employee_id=employee_id, **data)
        self._session.add(n)
        await self._session.flush()
        await self._session.refresh(n)
        return _to_domain(n)
