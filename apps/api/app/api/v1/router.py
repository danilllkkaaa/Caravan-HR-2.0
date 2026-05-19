from fastapi import APIRouter

from app.api.v1 import (
    admin,
    approvals,
    auth,
    dashboard,
    directories,
    employees,
    notifications,
    personal_data,
    sick_leaves,
    timesheet,
    vacations,
    webhooks,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(vacations.router)
api_router.include_router(approvals.router)
api_router.include_router(sick_leaves.router)
api_router.include_router(timesheet.router)
api_router.include_router(employees.router)
api_router.include_router(directories.router)
api_router.include_router(notifications.router)
api_router.include_router(webhooks.router)
api_router.include_router(admin.router)
api_router.include_router(personal_data.router)
api_router.include_router(personal_data.hr_router)
