from __future__ import annotations

from datetime import date

from app.application.vacation_calendar import count_vacation_days, days_until_start


def test_count_vacation_days_excludes_holidays() -> None:
    start = date(2026, 5, 1)
    end = date(2026, 5, 7)
    holidays = {date(2026, 5, 1), date(2026, 5, 7)}
    assert count_vacation_days(start, end, holidays) == 5


def test_count_vacation_days_without_holidays() -> None:
    start = date(2026, 7, 1)
    end = date(2026, 7, 14)
    assert count_vacation_days(start, end) == 14


def test_days_until_start() -> None:
    assert days_until_start(date(2026, 6, 1), date(2026, 5, 18)) == 14
