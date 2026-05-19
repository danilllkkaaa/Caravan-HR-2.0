from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter

from app.api.deps import CurrentEmployee, DBSession, RedisClient
from app.core.config import get_settings
from app.infrastructure.repositories.notification import NotificationRepository
from app.infrastructure.repositories.vacation import VacationRepository

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
log = structlog.get_logger(__name__)
settings = get_settings()


@router.get("")
async def get_dashboard(
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
) -> dict[str, Any]:
    cache_key = f"dashboard:{employee.id}"

    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    year = datetime.now(UTC).year

    vacation_repo = VacationRepository(db)
    notification_repo = NotificationRepository(db)

    balance = await vacation_repo.get_balance(employee.id, year)
    notifications, _ = await notification_repo.list_for_employee(employee.id, 0, 3)

    data: dict[str, Any] = {
        "employee": {
            "id": str(employee.id),
            "first_name": employee.first_name,
            "last_name": employee.last_name,
            "middle_name": employee.middle_name,
            "role": employee.role,
            "avatar_url": employee.avatar_url,
        },
        "vacation_balance": {
            "year": year,
            "total_days": float(balance.total_days) if balance else 0.0,
            "used_days": float(balance.used_days) if balance else 0.0,
            "available_days": float(balance.available_days) if balance else 0.0,
        },
        "today_timesheet": None,
        "recent_notifications": [
            {
                "id": str(n.id),
                "type": n.type,
                "title": n.title,
                "body": n.body,
                "read_at": n.read_at.isoformat() if n.read_at else None,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifications
        ],
        "generated_at": datetime.now(UTC).isoformat(),
    }

    await redis.setex(cache_key, settings.redis_cache_ttl, json.dumps(data))
    return data
