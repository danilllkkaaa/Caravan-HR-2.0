from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Query

from app.api.deps import CurrentEmployee, DBSession
from app.application.services.notification import NotificationService
from app.infrastructure.repositories.notification import NotificationRepository

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _get_service(db: DBSession) -> NotificationService:
    return NotificationService(NotificationRepository(db))


def _format_notification(n: Any) -> dict[str, Any]:
    return {
        "id": str(n.id),
        "type": n.type,
        "title": n.title,
        "body": n.body,
        "payload": n.payload,
        "read_at": n.read_at.isoformat() if n.read_at else None,
        "created_at": n.created_at.isoformat(),
    }


@router.get("")
async def list_notifications(
    employee: CurrentEmployee,
    db: DBSession,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    unread_only: bool = Query(default=False),
) -> dict[str, Any]:
    service = _get_service(db)
    notifications, total = await service.list_for_employee(
        employee.id, offset, limit, unread_only=unread_only
    )
    return {
        "items": [_format_notification(n) for n in notifications],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.get("/unread-count")
async def get_unread_count(
    employee: CurrentEmployee,
    db: DBSession,
) -> dict[str, int]:
    service = _get_service(db)
    count = await service.count_unread(employee.id)
    return {"count": count}


@router.post("/{notification_id}/read", status_code=200)
async def mark_notification_read(
    notification_id: uuid.UUID,
    employee: CurrentEmployee,
    db: DBSession,
) -> dict[str, Any]:
    service = _get_service(db)
    n = await service.mark_read(notification_id, employee.id)
    return _format_notification(n)


@router.post("/read-all", status_code=204)
async def mark_all_read(
    employee: CurrentEmployee,
    db: DBSession,
) -> None:
    service = _get_service(db)
    await service.mark_all_read(employee.id)
