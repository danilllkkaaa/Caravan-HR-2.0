from __future__ import annotations

from datetime import date, timedelta


def count_vacation_days(
    start_date: date,
    end_date: date,
    holiday_dates: set[date] | None = None,
) -> int:
    """Calendar days in range excluding public holidays."""
    holidays = holiday_dates or set()
    count = 0
    current = start_date
    while current <= end_date:
        if current not in holidays:
            count += 1
        current += timedelta(days=1)
    return count


def days_until_start(start_date: date, today: date) -> int:
    return (start_date - today).days


SHORT_NOTICE_DAYS = 14
