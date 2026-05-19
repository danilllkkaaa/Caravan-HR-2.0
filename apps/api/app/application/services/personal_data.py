"""Application-layer services for the personal-data module."""
from __future__ import annotations

import json
import uuid
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
from typing import Any

import structlog

from app.core.encryption import encrypt_field
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.infrastructure.models import (
    BankAccount,
    CitizenshipRecord,
    EducationRecord,
    EmergencyContact,
    EmployeeAddress,
    FamilyMember,
    IdentityDocument,
    MedicalCertificate,
    PersonalData,
    PersonalDataChangeRequest,
    SocialInfo,
)
from app.infrastructure.repositories.personal_data import (
    ChangeRequestRepository,
    PersonalDataRepository,
)

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Cache TTLs (seconds)
# ---------------------------------------------------------------------------
TTL = {
    "personal": 300,
    "documents": 1800,
    "addresses": 1800,
    "education": 1800,
    "family": 900,
    "emergency": 1800,
    "social": 1800,
    "medical": 1800,
    "bank": 1800,
    "change_req": 120,
    "hr_routing": 86400,
}

# HR routing — specific overrides before falling back to work_locations.hr_email
_HR_ROUTING_OVERRIDES: dict[str, list[str]] = {
    "Алмалы": ["hralmaly@caravanresources.com", "hr.almaly2@caravanresources.com"],
    "Ашыктас": ["hr.ashyktas@caravanresources.com"],
}

CHANGE_REQUEST_EDITABLE_FIELDS: dict[str, set[str]] = {
    "basic_data": {
        "first_name_en",
        "last_name_en",
        "middle_name_en",
        "gender",
        "nationality",
        "place_of_birth",
        "marital_status",
    },
    "citizenship": {
        "citizenship_country",
        "status",
        "iin_in_country",
        "is_primary",
    },
    "address": {
        "country",
        "region",
        "city",
        "street",
        "house",
        "apartment",
    },
    "contacts": {
        "email",
        "mobile_phone",
        "home_phone",
        "additional_phone",
    },
    "social_info": {
        "pension_status",
        "has_disability",
        "disability_group",
        "is_ww2_veteran",
        "is_ww2_family",
        "document_url",
    },
    "emergency_contact": {
        "full_name",
        "phone",
        "address",
        "relationship",
    },
}


def _cache_key(section: str, employee_id: uuid.UUID) -> str:
    return f"profile:{section}:{employee_id}"


def _serialize(obj: Any) -> str:
    """JSON-serialize SQLAlchemy model instances or plain dicts/lists."""
    return json.dumps(_to_serializable(obj), default=str)


def _to_serializable(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, list):
        return [_to_serializable(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    if hasattr(obj, "__dict__"):
        # SQLAlchemy model — filter out SA internal state
        data = {
            k: v
            for k, v in obj.__dict__.items()
            if not k.startswith("_")
        }
        return _to_serializable(data)
    return obj


# ---------------------------------------------------------------------------
# PersonalDataService
# ---------------------------------------------------------------------------


class PersonalDataService:
    def __init__(
        self,
        repo: PersonalDataRepository,
        redis: Any,
    ) -> None:
        self._repo = repo
        self._redis = redis

    # ---- cache helpers ----

    async def get_section_cached(
        self,
        employee_id: uuid.UUID,
        section: str,
        fetch_fn: Callable[[], Coroutine[Any, Any, Any]],
    ) -> Any:
        key = _cache_key(section, employee_id)
        cached = await self._redis.get(key)
        if cached:
            return json.loads(cached)
        data = await fetch_fn()
        await self._redis.setex(key, TTL[section], _serialize(data))
        return data

    async def invalidate_profile_cache(self, employee_id: uuid.UUID) -> None:
        sections = [
            "personal", "documents", "addresses", "education",
            "family", "emergency", "social", "medical", "bank", "change_req",
        ]
        for section in sections:
            await self._redis.delete(_cache_key(section, employee_id))

    async def _invalidate_section(self, employee_id: uuid.UUID, section: str) -> None:
        await self._redis.delete(_cache_key(section, employee_id))

    # ---- HR routing ----

    async def _get_hr_email(
        self, work_location_name: str, work_location_hr_email: str | None
    ) -> str:
        """Resolve HR e-mail for a work location.

        Priority:
          1. Cached `config:hr_routing` (JSON dict keyed by location name)
          2. Hard-coded overrides for known locations
          3. work_locations.hr_email from caller
        """
        cache_key = "config:hr_routing"
        routing_raw = await self._redis.get(cache_key)
        if routing_raw:
            routing: dict[str, str] = json.loads(routing_raw)
            if work_location_name in routing:
                return routing[work_location_name]

        # Hard-coded overrides
        for loc_name, emails in _HR_ROUTING_OVERRIDES.items():
            if loc_name.lower() in work_location_name.lower():
                hr_email = emails[0]
                log.debug(
                    "HR routing resolved via override",
                    location=work_location_name,
                    hr_email=hr_email,
                )
                return hr_email

        # Fall back to DB value
        if work_location_hr_email:
            return work_location_hr_email

        raise ValidationError(
            message=f"Could not determine HR email for location '{work_location_name}'"
        )

    # ---- full profile ----

    async def get_full_profile(self, employee_id: uuid.UUID) -> dict[str, Any]:
        sections = await self._repo.get_all_sections(employee_id)
        return sections

    # ---- personal data ----

    async def get_personal_data(self, employee_id: uuid.UUID) -> PersonalData | None:
        return await self._repo.get_personal_data(employee_id)

    async def update_section(
        self,
        employee_id: uuid.UUID,
        section: str,
        data: dict[str, Any],
        is_first_fill: bool = False,
    ) -> Any:
        """Write directly if first fill; otherwise create a change request."""
        if is_first_fill:
            row = await self._repo.upsert_personal_data(employee_id, data, source="user")
            await self._invalidate_section(employee_id, "personal")
            return row
        # Otherwise caller should use ChangeRequestService.create_request
        raise ValidationError(
            message="Direct updates after initial fill require a change request."
        )

    # ---- documents ----

    async def get_identity_documents(self, employee_id: uuid.UUID) -> list[IdentityDocument]:
        return await self._repo.get_identity_documents(employee_id)

    async def add_identity_document(
        self, employee_id: uuid.UUID, data: dict[str, Any]
    ) -> IdentityDocument:
        data["employee_id"] = employee_id
        data.setdefault("data_source", "user")
        doc = await self._repo.add_identity_document(data)
        await self._invalidate_section(employee_id, "documents")
        return doc

    # ---- addresses ----

    async def get_addresses(self, employee_id: uuid.UUID) -> list[EmployeeAddress]:
        return await self._repo.get_addresses(employee_id)

    async def upsert_address(
        self, employee_id: uuid.UUID, address_type: str, data: dict[str, Any], is_first_fill: bool
    ) -> EmployeeAddress:
        data.setdefault("data_source", "user" if is_first_fill else "user")
        addr = await self._repo.upsert_address(employee_id, address_type, data)
        await self._invalidate_section(employee_id, "addresses")
        return addr

    # ---- education ----

    async def get_education_records(self, employee_id: uuid.UUID) -> list[EducationRecord]:
        return await self._repo.get_education_records(employee_id)

    async def add_education_record(
        self, employee_id: uuid.UUID, data: dict[str, Any]
    ) -> EducationRecord:
        data["employee_id"] = employee_id
        data.setdefault("data_source", "user")
        rec = await self._repo.add_education_record(data)
        await self._invalidate_section(employee_id, "education")
        return rec

    async def update_education_record(
        self, employee_id: uuid.UUID, record_id: uuid.UUID, data: dict[str, Any]
    ) -> EducationRecord:
        rec = await self._repo.update_education_record(record_id, data)
        await self._invalidate_section(employee_id, "education")
        return rec

    async def delete_education_record(
        self, employee_id: uuid.UUID, record_id: uuid.UUID
    ) -> None:
        await self._repo.delete_education_record(record_id)
        await self._invalidate_section(employee_id, "education")

    # ---- family ----

    async def get_family_members(self, employee_id: uuid.UUID) -> list[FamilyMember]:
        members = await self._repo.get_family_members(employee_id)
        return members

    async def add_family_member(
        self, employee_id: uuid.UUID, data: dict[str, Any]
    ) -> FamilyMember:
        # Encrypt IIN before storing
        if "iin" in data and data["iin"]:
            data["iin_encrypted"] = encrypt_field(data.pop("iin"))
        else:
            data.pop("iin", None)
            data.setdefault("iin_encrypted", None)
        data["employee_id"] = employee_id
        data.setdefault("data_source", "user")
        member = await self._repo.add_family_member(data)
        await self._invalidate_section(employee_id, "family")
        return member

    async def update_family_member(
        self, employee_id: uuid.UUID, member_id: uuid.UUID, data: dict[str, Any]
    ) -> FamilyMember:
        if "iin" in data and data["iin"]:
            data["iin_encrypted"] = encrypt_field(data.pop("iin"))
        else:
            data.pop("iin", None)
        member = await self._repo.update_family_member(member_id, data)
        await self._invalidate_section(employee_id, "family")
        return member

    async def delete_family_member(
        self, employee_id: uuid.UUID, member_id: uuid.UUID
    ) -> None:
        await self._repo.delete_family_member(member_id)
        await self._invalidate_section(employee_id, "family")

    # ---- emergency contact ----

    async def get_emergency_contact(self, employee_id: uuid.UUID) -> EmergencyContact | None:
        return await self._repo.get_emergency_contact(employee_id)

    async def upsert_emergency_contact(
        self, employee_id: uuid.UUID, data: dict[str, Any]
    ) -> EmergencyContact:
        contact = await self._repo.upsert_emergency_contact(employee_id, data)
        await self._invalidate_section(employee_id, "emergency")
        return contact

    # ---- social info ----

    async def get_social_info(self, employee_id: uuid.UUID) -> SocialInfo | None:
        return await self._repo.get_social_info(employee_id)

    async def upsert_social_info(
        self, employee_id: uuid.UUID, data: dict[str, Any]
    ) -> SocialInfo:
        info = await self._repo.upsert_social_info(employee_id, data)
        await self._invalidate_section(employee_id, "social")
        return info

    # ---- medical certificates ----

    async def get_medical_certificates(
        self, employee_id: uuid.UUID
    ) -> list[MedicalCertificate]:
        return await self._repo.get_medical_certificates(employee_id)

    async def add_medical_certificate(
        self, employee_id: uuid.UUID, data: dict[str, Any]
    ) -> MedicalCertificate:
        data["employee_id"] = employee_id
        cert = await self._repo.add_medical_certificate(data)
        await self._invalidate_section(employee_id, "medical")
        return cert

    async def delete_medical_certificate(
        self, employee_id: uuid.UUID, cert_id: uuid.UUID
    ) -> None:
        await self._repo.delete_medical_certificate(cert_id, employee_id)
        await self._invalidate_section(employee_id, "medical")

    # ---- bank accounts ----

    async def get_bank_accounts(self, employee_id: uuid.UUID) -> list[BankAccount]:
        return await self._repo.get_bank_accounts(employee_id)

    async def add_bank_account(
        self, employee_id: uuid.UUID, data: dict[str, Any]
    ) -> BankAccount:
        if "account_number" in data and data["account_number"]:
            data["account_number_encrypted"] = encrypt_field(data.pop("account_number"))
        data["employee_id"] = employee_id
        data.setdefault("data_source", "user")
        account = await self._repo.add_bank_account(data)
        await self._invalidate_section(employee_id, "bank")
        return account

    async def delete_bank_account(
        self, employee_id: uuid.UUID, account_id: uuid.UUID
    ) -> None:
        await self._repo.delete_bank_account(account_id, employee_id)
        await self._invalidate_section(employee_id, "bank")

    # ---- citizenship ----

    async def get_citizenship_records(self, employee_id: uuid.UUID) -> list[CitizenshipRecord]:
        return await self._repo.get_citizenship_records(employee_id)


# ---------------------------------------------------------------------------
# ChangeRequestService
# ---------------------------------------------------------------------------


class ChangeRequestService:
    def __init__(
        self,
        cr_repo: ChangeRequestRepository,
        pd_repo: PersonalDataRepository,
        redis: Any,
    ) -> None:
        self._cr_repo = cr_repo
        self._pd_repo = pd_repo
        self._redis = redis

    async def _invalidate(self, employee_id: uuid.UUID) -> None:
        await self._redis.delete(f"profile:change_req:{employee_id}")

    async def create_request(
        self,
        employee_id: uuid.UUID,
        section: str,
        field_name: str,
        old_value: Any,
        new_value: Any,
        hr_email: str,
        comment: str | None = None,
        document_url: str | None = None,
    ) -> PersonalDataChangeRequest:
        row = await self._cr_repo.create(
            {
                "employee_id": employee_id,
                "section": section,
                "field_name": field_name,
                "old_value": old_value,
                "new_value": new_value,
                "comment": comment,
                "document_url": document_url,
                "hr_email": hr_email,
                "status": "sent",
            }
        )
        await self._invalidate(employee_id)
        # Fire-and-forget email notification via Celery
        try:
            from app.workers.sync_tasks import send_change_request_email  # noqa: PLC0415
            send_change_request_email.delay(str(row.id))
        except Exception as exc:
            log.warning("Failed to enqueue change-request email", error=str(exc))
        return row

    async def get_request(
        self, request_id: uuid.UUID, employee_id: uuid.UUID | None = None
    ) -> PersonalDataChangeRequest:
        row = await self._cr_repo.get(request_id)
        if row is None:
            raise NotFoundError(message=f"ChangeRequest {request_id} not found")
        if employee_id is not None and row.employee_id != employee_id:
            raise ForbiddenError()
        return row

    async def list_by_employee(
        self, employee_id: uuid.UUID, status: str | None = None
    ) -> list[PersonalDataChangeRequest]:
        return await self._cr_repo.list_by_employee(employee_id, status)

    async def list_for_hr(
        self, hr_email: str, status: str | None = None
    ) -> list[PersonalDataChangeRequest]:
        return await self._cr_repo.list_for_hr(hr_email, status)

    async def list_for_reviewer(
        self, hr_email: str, is_admin: bool, status: str | None = None
    ) -> list[PersonalDataChangeRequest]:
        if is_admin:
            return await self._cr_repo.list_all(status)
        return await self._cr_repo.list_for_hr(hr_email, status)

    async def get_request_for_reviewer(
        self, request_id: uuid.UUID, hr_email: str, is_admin: bool
    ) -> PersonalDataChangeRequest:
        row = await self.get_request(request_id)
        self._ensure_reviewer_access(row, hr_email, is_admin)
        return row

    async def cancel_request(
        self, request_id: uuid.UUID, employee_id: uuid.UUID
    ) -> PersonalDataChangeRequest:
        row = await self.get_request(request_id, employee_id)
        if row.status != "sent":
            raise ValidationError(message="Only 'sent' requests can be cancelled.")
        row = await self._cr_repo.update_status(
            request_id, "rejected", hr_comment="Cancelled by employee"
        )
        await self._invalidate(employee_id)
        return row

    async def approve_request(
        self,
        request_id: uuid.UUID,
        hr_employee_id: uuid.UUID,
        hr_email: str,
        hr_comment: str | None = None,
        actor_user_id: uuid.UUID | None = None,
        ip: str = "unknown",
        db_session: Any = None,
        is_admin: bool = False,
    ) -> PersonalDataChangeRequest:
        row = await self._cr_repo.get(request_id)
        if row is None:
            raise NotFoundError(message=f"ChangeRequest {request_id} not found")
        self._ensure_reviewer_access(row, hr_email, is_admin)
        if row.status not in ("sent", "under_review"):
            raise ValidationError(message="Only sent or under_review requests can be approved.")

        # Apply field change to target table
        await self._apply_change(row)

        now = datetime.now(UTC)
        row = await self._cr_repo.update_status(
            request_id,
            status="approved",
            hr_comment=hr_comment,
            processed_at=now,
            hr_employee_id=hr_employee_id,
        )

        # Write audit log
        if db_session and actor_user_id:
            from app.infrastructure.models import AuditLog  # noqa: PLC0415
            audit = AuditLog(
                actor_id=actor_user_id,
                action="personal_data_change_request.approved",
                target_type="personal_data_change_requests",
                target_id=str(request_id),
                changes={
                    "section": row.section,
                    "field": row.field_name,
                    "new_value": row.new_value,
                },
                ip=ip,
            )
            db_session.add(audit)
            await db_session.flush()

        await self._invalidate(row.employee_id)

        # Notify employee
        try:
            from app.workers.notification_tasks import send_push_notification  # noqa: PLC0415
            send_push_notification.delay(
                str(row.employee_id),
                "approved",
                "Personal data update approved",
                f"Your change request for field '{row.field_name}' has been approved.",
                {"change_request_id": str(request_id)},
            )
        except Exception as exc:
            log.warning("Failed to enqueue approval notification", error=str(exc))

        return row

    async def reject_request(
        self,
        request_id: uuid.UUID,
        hr_employee_id: uuid.UUID,
        reason: str,
        actor_user_id: uuid.UUID | None = None,
        ip: str = "unknown",
        db_session: Any = None,
        hr_email: str = "",
        is_admin: bool = False,
    ) -> PersonalDataChangeRequest:
        row = await self._cr_repo.get(request_id)
        if row is None:
            raise NotFoundError(message=f"ChangeRequest {request_id} not found")
        self._ensure_reviewer_access(row, hr_email, is_admin)
        if row.status not in ("sent", "under_review"):
            raise ValidationError(message="Only sent or under_review requests can be rejected.")

        now = datetime.now(UTC)
        row = await self._cr_repo.update_status(
            request_id,
            status="rejected",
            hr_comment=reason,
            processed_at=now,
            hr_employee_id=hr_employee_id,
        )

        # Write audit log
        if db_session and actor_user_id:
            from app.infrastructure.models import AuditLog  # noqa: PLC0415
            audit = AuditLog(
                actor_id=actor_user_id,
                action="personal_data_change_request.rejected",
                target_type="personal_data_change_requests",
                target_id=str(request_id),
                changes={"reason": reason, "field": row.field_name},
                ip=ip,
            )
            db_session.add(audit)
            await db_session.flush()

        await self._invalidate(row.employee_id)

        try:
            from app.workers.notification_tasks import send_push_notification  # noqa: PLC0415
            send_push_notification.delay(
                str(row.employee_id),
                "rejected",
                "Personal data update rejected",
                f"Your change request for field '{row.field_name}' was rejected. Reason: {reason}",
                {"change_request_id": str(request_id)},
            )
        except Exception as exc:
            log.warning("Failed to enqueue rejection notification", error=str(exc))

        return row

    async def _apply_change(self, row: PersonalDataChangeRequest) -> None:
        """Apply the approved change to the appropriate table."""
        section = row.section
        if not isinstance(row.new_value, dict):
            raise ValidationError(message="Change request new_value must be an object.")

        new_val = row.new_value
        emp_id = row.employee_id

        if section == "basic_data":
            await self._pd_repo.upsert_personal_data(
                emp_id,
                self._extract_field_update(section, row.field_name, new_val),
                source="hr_approved",
            )
            return

        if section == "citizenship":
            data = self._extract_bulk_update(section, new_val)
            records = await self._pd_repo.get_citizenship_records(emp_id)
            data["data_source"] = "hr_approved"
            if records:
                await self._pd_repo.update_citizenship_record(records[0].id, data)
            else:
                data["employee_id"] = emp_id
                data.setdefault("citizenship_country", "")
                data.setdefault("status", "rk_citizen")
                await self._pd_repo.add_citizenship_record(data)
            return

        if section == "address":
            address_type = str(new_val.get("address_type", "registration"))
            if address_type not in ("registration", "residence"):
                raise ValidationError(message="address_type must be registration or residence.")
            data = self._extract_bulk_update(section, new_val, ignore={"address_type"})
            data["data_source"] = "hr_approved"
            await self._pd_repo.upsert_address(emp_id, address_type, data)
            return

        if section == "contacts":
            data = self._extract_bulk_update(section, new_val)
            data["data_source"] = "hr_approved"
            contact = await self._pd_repo.get_employee_contact(emp_id)
            if contact is None:
                data.setdefault("email", "")
                data.setdefault("mobile_phone", "")
            await self._pd_repo.upsert_employee_contact(emp_id, data)
            return

        if section == "social_info":
            data = self._extract_bulk_update(section, new_val)
            data["data_source"] = "hr_approved"
            await self._pd_repo.upsert_social_info(emp_id, data)
            return

        if section == "emergency_contact":
            data = self._extract_bulk_update(section, new_val)
            existing = await self._pd_repo.get_emergency_contact(emp_id)
            if existing is None:
                data.setdefault("full_name", "")
                data.setdefault("phone", "")
                data.setdefault("relationship", "")
            await self._pd_repo.upsert_emergency_contact(emp_id, data)
            return

        raise ValidationError(
            message=f"Auto-apply is not implemented for change request section '{section}'."
        )

    @staticmethod
    def _ensure_reviewer_access(
        row: PersonalDataChangeRequest, hr_email: str, is_admin: bool
    ) -> None:
        if is_admin:
            return
        if not hr_email or row.hr_email.lower() != hr_email.lower():
            raise ForbiddenError(message="Change request is assigned to another HR reviewer.")

    @staticmethod
    def _extract_field_update(
        section: str, field_name: str, new_value: dict[str, Any]
    ) -> dict[str, Any]:
        allowed = CHANGE_REQUEST_EDITABLE_FIELDS.get(section, set())
        if field_name not in allowed:
            raise ValidationError(message=f"Field '{field_name}' cannot be updated in {section}.")
        return {field_name: new_value.get("value")}

    @staticmethod
    def _extract_bulk_update(
        section: str,
        new_value: dict[str, Any],
        ignore: set[str] | None = None,
    ) -> dict[str, Any]:
        ignored = ignore or set()
        allowed = CHANGE_REQUEST_EDITABLE_FIELDS.get(section, set())
        data = {
            key: value
            for key, value in new_value.items()
            if key in allowed and key not in ignored
        }
        unknown = set(new_value) - allowed - ignored
        if unknown:
            raise ValidationError(
                message=f"Unsupported fields for {section}: {sorted(unknown)}"
            )
        if not data:
            raise ValidationError(message=f"No supported fields provided for {section}.")
        return data
