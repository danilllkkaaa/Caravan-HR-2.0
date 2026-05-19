from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models import AuditLog


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def log(
        self,
        actor_user_id: uuid.UUID,
        action: str,
        target_type: str,
        target_id: str,
        changes: dict[str, Any],
        ip: str = "127.0.0.1",
    ) -> None:
        entry = AuditLog(
            actor_id=actor_user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            changes=changes,
            ip=ip,
        )
        self._session.add(entry)
        await self._session.flush()
