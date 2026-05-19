from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog

from app.core.exceptions import ForbiddenError, NotFoundError
from app.domain.models import NotificationDomain
from app.domain.repositories import AbstractNotificationRepository

log = structlog.get_logger(__name__)


class NotificationService:
    def __init__(self, notification_repo: AbstractNotificationRepository) -> None:
        self._repo = notification_repo

    async def list_for_employee(
        self,
        employee_id: uuid.UUID,
        offset: int,
        limit: int,
        unread_only: bool = False,
    ) -> tuple[list[NotificationDomain], int]:
        return await self._repo.list_for_employee(
            employee_id, offset, limit, unread_only=unread_only
        )

    async def count_unread(self, employee_id: uuid.UUID) -> int:
        return await self._repo.count_unread(employee_id)

    async def mark_read(
        self,
        notification_id: uuid.UUID,
        requester_employee_id: uuid.UUID,
    ) -> NotificationDomain:
        n = await self._repo.get_by_id(notification_id)
        if n is None:
            raise NotFoundError(message="Notification not found")
        if n.employee_id != requester_employee_id:
            raise ForbiddenError()
        if n.read_at is None:
            await self._repo.mark_read(notification_id, datetime.now(UTC))
        return await self._repo.get_by_id(notification_id)  # type: ignore[return-value]

    async def mark_all_read(self, employee_id: uuid.UUID) -> None:
        await self._repo.mark_all_read(employee_id, datetime.now(UTC))

    async def create(
        self,
        employee_id: uuid.UUID,
        type: str,
        title: str,
        body: str,
        payload: dict[str, Any] | None = None,
    ) -> NotificationDomain:
        n = await self._repo.create(
            employee_id,
            {
                "type": type,
                "title": title,
                "body": body,
                "payload": payload,
            },
        )
        log.info(
            "Notification created",
            notification_id=str(n.id),
            employee_id=str(employee_id),
            type=type,
        )
        return n
