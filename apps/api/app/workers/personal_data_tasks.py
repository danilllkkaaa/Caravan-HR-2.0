"""Personal-data Celery tasks.

The actual implementations live in ``app.workers.sync_tasks`` alongside the
other 1C sync tasks.  This module re-exports them so that Celery's
``include`` list can reference a dedicated namespace while keeping all
task registrations in one place.
"""
from __future__ import annotations

# Re-export so Celery discovers these under the sync_tasks namespace.
from app.workers.sync_tasks import (  # noqa: F401
    send_change_request_email,
    sync_bank_accounts_all,
    sync_education_all,
    sync_family_members_all,
    sync_personal_data_all,
    sync_personal_data_employee,
)
