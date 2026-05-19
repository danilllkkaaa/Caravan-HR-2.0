from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.notification import NotificationService
from app.application.services.vacation import VacationService
from app.infrastructure.repositories.audit import AuditRepository
from app.infrastructure.repositories.employee import EmployeeRepository
from app.infrastructure.repositories.holiday import HolidayRepository
from app.infrastructure.repositories.notification import NotificationRepository
from app.infrastructure.repositories.vacation import VacationRepository


def build_vacation_service(db: AsyncSession) -> VacationService:
    return VacationService(
        vacation_repo=VacationRepository(db),
        employee_repo=EmployeeRepository(db),
        holiday_repo=HolidayRepository(db),
        notification_service=NotificationService(NotificationRepository(db)),
        audit_repo=AuditRepository(db),
    )
