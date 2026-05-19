from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.application.services.personal_data import ChangeRequestService
from app.core.exceptions import ForbiddenError, ValidationError


def _change_request(**overrides):
    data = {
        "id": uuid.uuid4(),
        "employee_id": uuid.uuid4(),
        "section": "contacts",
        "field_name": "mobile_phone",
        "old_value": {"mobile_phone": "+7 700 000 00 00"},
        "new_value": {"mobile_phone": "+7 701 111 22 33"},
        "comment": None,
        "document_url": None,
        "hr_employee_id": None,
        "hr_email": "hr@example.com",
        "status": "sent",
        "hr_comment": None,
        "processed_at": None,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    data.update(overrides)
    return SimpleNamespace(**data)


class FakeChangeRequestRepository:
    def __init__(self, row):
        self.row = row
        self.updated = False

    async def get(self, request_id):
        return self.row if self.row.id == request_id else None

    async def update_status(
        self,
        request_id,
        status,
        hr_comment=None,
        processed_at=None,
        hr_employee_id=None,
    ):
        self.updated = True
        self.row.status = status
        self.row.hr_comment = hr_comment
        self.row.processed_at = processed_at
        self.row.hr_employee_id = hr_employee_id
        return self.row

    async def list_for_hr(self, hr_email, status=None):
        if self.row.hr_email == hr_email and (status is None or self.row.status == status):
            return [self.row]
        return []

    async def list_all(self, status=None):
        if status is None or self.row.status == status:
            return [self.row]
        return []


class FakePersonalDataRepository:
    def __init__(self):
        self.contact = None
        self.contact_updates = []

    async def get_employee_contact(self, employee_id):
        return self.contact

    async def upsert_employee_contact(self, employee_id, data):
        self.contact_updates.append((employee_id, data))
        self.contact = SimpleNamespace(employee_id=employee_id, **data)
        return self.contact


def _service(row, pd_repo=None):
    redis = AsyncMock()
    redis.delete = AsyncMock()
    return ChangeRequestService(
        cr_repo=FakeChangeRequestRepository(row),
        pd_repo=pd_repo or FakePersonalDataRepository(),
        redis=redis,
    )


@pytest.mark.asyncio
async def test_hr_cannot_approve_request_assigned_to_another_hr():
    row = _change_request(hr_email="hr.owner@example.com")
    service = _service(row)

    with pytest.raises(ForbiddenError):
        await service.approve_request(
            row.id,
            hr_employee_id=uuid.uuid4(),
            hr_email="hr.other@example.com",
        )

    assert row.status == "sent"
    assert service._cr_repo.updated is False


@pytest.mark.asyncio
async def test_approve_does_not_mark_approved_when_auto_apply_is_unsupported():
    row = _change_request(section="document", field_name="document_url")
    service = _service(row)

    with pytest.raises(ValidationError):
        await service.approve_request(
            row.id,
            hr_employee_id=uuid.uuid4(),
            hr_email="hr@example.com",
        )

    assert row.status == "sent"
    assert service._cr_repo.updated is False


@pytest.mark.asyncio
async def test_approve_contacts_request_applies_data_before_status_update(monkeypatch):
    row = _change_request()
    pd_repo = FakePersonalDataRepository()
    service = _service(row, pd_repo)
    monkeypatch.setattr(
        "app.workers.notification_tasks.send_push_notification.delay",
        lambda *args, **kwargs: None,
    )

    approved = await service.approve_request(
        row.id,
        hr_employee_id=uuid.uuid4(),
        hr_email="hr@example.com",
        hr_comment="OK",
    )

    assert approved.status == "approved"
    assert pd_repo.contact_updates == [
        (
            row.employee_id,
            {
                "mobile_phone": "+7 701 111 22 33",
                "data_source": "hr_approved",
                "email": "",
            },
        )
    ]
