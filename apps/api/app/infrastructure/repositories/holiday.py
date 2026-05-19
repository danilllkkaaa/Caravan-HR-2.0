from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models import Holiday


class HolidayRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def dates_between(self, start_date: date, end_date: date) -> set[date]:
        stmt = select(Holiday.date).where(
            Holiday.date >= start_date,
            Holiday.date <= end_date,
        )
        result = await self._session.execute(stmt)
        return set(result.scalars().all())
