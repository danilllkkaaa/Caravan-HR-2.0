"""Personal-data profile endpoints.

Employee routes: /api/v1/profile/*
HR routes:       /api/v1/hr/change-requests/*
"""
from __future__ import annotations

import uuid
from typing import Annotated, Any

import structlog
from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import (
    CurrentEmployee,
    DBSession,
    RedisClient,
    get_client_ip,
    require_roles,
)
from app.api.v1.schemas.personal_data import (
    AddressResponse,
    AddressUpdate,
    BankAccountCreate,
    BankAccountResponse,
    ChangeRequestApprove,
    ChangeRequestCreate,
    ChangeRequestReject,
    ChangeRequestResponse,
    CitizenshipRecordCreate,
    CitizenshipRecordResponse,
    EducationRecordCreate,
    EducationRecordResponse,
    EducationRecordUpdate,
    EmergencyContactResponse,
    EmergencyContactUpdate,
    EmployeeContactResponse,
    EmployeeContactUpdate,
    FamilyMemberCreate,
    FamilyMemberResponse,
    FamilyMemberUpdate,
    IdentityDocumentCreate,
    IdentityDocumentResponse,
    MedicalCertificateCreate,
    MedicalCertificateResponse,
    PersonalDataResponse,
    PersonalDataUpdate,
    PresignedDownloadResponse,
    PresignedUploadResponse,
    SocialInfoResponse,
    SocialInfoUpdate,
)
from app.application.services.personal_data import ChangeRequestService, PersonalDataService
from app.core.config import get_settings
from app.core.encryption import decrypt_field_safe
from app.core.exceptions import NotFoundError
from app.domain.models import EmployeeDomain
from app.infrastructure.repositories.personal_data import (
    ChangeRequestRepository,
    PersonalDataRepository,
)

log = structlog.get_logger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Router definitions
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/profile", tags=["profile"])
hr_router = APIRouter(prefix="/hr", tags=["hr"])


# ---------------------------------------------------------------------------
# Dependency factories
# ---------------------------------------------------------------------------


def _get_pd_service(db: DBSession, redis: RedisClient) -> PersonalDataService:
    return PersonalDataService(
        repo=PersonalDataRepository(db),
        redis=redis,
    )


def _get_cr_service(db: DBSession, redis: RedisClient) -> ChangeRequestService:
    return ChangeRequestService(
        cr_repo=ChangeRequestRepository(db),
        pd_repo=PersonalDataRepository(db),
        redis=redis,
    )


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------


def _serialize_pd(row: Any) -> dict[str, Any] | None:
    if row is None:
        return None
    return PersonalDataResponse.model_validate(row).model_dump(mode="json")


def _serialize_citizenship(rows: list[Any]) -> list[dict[str, Any]]:
    return [CitizenshipRecordResponse.model_validate(r).model_dump(mode="json") for r in rows]


def _serialize_docs(rows: list[Any]) -> list[dict[str, Any]]:
    return [IdentityDocumentResponse.model_validate(r).model_dump(mode="json") for r in rows]


def _serialize_addresses(rows: list[Any]) -> list[dict[str, Any]]:
    return [AddressResponse.model_validate(r).model_dump(mode="json") for r in rows]


def _serialize_education(rows: list[Any]) -> list[dict[str, Any]]:
    return [EducationRecordResponse.model_validate(r).model_dump(mode="json") for r in rows]


def _serialize_family_member(row: Any) -> dict[str, Any]:
    data = FamilyMemberResponse.model_validate(row).model_dump(mode="json")
    # Mask IIN — return last 4 chars only
    if row.iin_encrypted:
        plain = decrypt_field_safe(row.iin_encrypted)
        data["iin_masked"] = f"****{plain[-4:]}" if plain and len(plain) >= 4 else "****"
    return data


def _serialize_family(rows: list[Any]) -> list[dict[str, Any]]:
    return [_serialize_family_member(r) for r in rows]


def _serialize_emergency(row: Any | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return EmergencyContactResponse.model_validate(row).model_dump(mode="json")


def _serialize_contact(row: Any | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return EmployeeContactResponse.model_validate(row).model_dump(mode="json")


def _serialize_social(row: Any | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return SocialInfoResponse.model_validate(row).model_dump(mode="json")


def _serialize_medical(rows: list[Any]) -> list[dict[str, Any]]:
    return [MedicalCertificateResponse.model_validate(r).model_dump(mode="json") for r in rows]


def _serialize_bank_account(row: Any) -> dict[str, Any]:
    data = BankAccountResponse.model_validate(row).model_dump(mode="json")
    if row.account_number_encrypted:
        plain = decrypt_field_safe(row.account_number_encrypted)
        data["account_number_masked"] = f"****{plain[-4:]}" if plain and len(plain) >= 4 else "****"
    return data


def _serialize_bank_accounts(rows: list[Any]) -> list[dict[str, Any]]:
    return [_serialize_bank_account(r) for r in rows]


def _serialize_cr(row: Any) -> dict[str, Any]:
    return ChangeRequestResponse.model_validate(row).model_dump(mode="json")


def _serialize_crs(rows: list[Any]) -> list[dict[str, Any]]:
    return [_serialize_cr(r) for r in rows]


async def _get_user_email(db: DBSession, user_id: uuid.UUID) -> str:
    from sqlalchemy import select

    from app.infrastructure.models import User

    result = await db.execute(select(User.email).where(User.id == user_id))
    return (result.scalar_one_or_none() or "").lower()


async def _get_hr_email_for_work_location(
    db: DBSession,
    hr_employee_id: uuid.UUID | None,
) -> str | None:
    if hr_employee_id is None:
        return None

    from sqlalchemy import select

    from app.infrastructure.models import Employee, User

    result = await db.execute(
        select(User.email)
        .join(Employee, Employee.user_id == User.id)
        .where(Employee.id == hr_employee_id)
    )
    email = result.scalar_one_or_none()
    return email.lower() if email else None


async def _resolve_hr_email(
    db: DBSession,
    redis: RedisClient,
    employee: EmployeeDomain,
) -> str:
    from sqlalchemy import select

    from app.infrastructure.models import WorkLocation

    if not employee.work_location_id:
        return ""

    result = await db.execute(
        select(WorkLocation).where(WorkLocation.id == employee.work_location_id)
    )
    work_location = result.scalar_one_or_none()
    if not work_location:
        return ""

    fallback_email = await _get_hr_email_for_work_location(db, work_location.hr_employee_id)
    service = _get_pd_service(db, redis)
    return await service._get_hr_email(work_location.name, fallback_email)


# ---------------------------------------------------------------------------
# /profile/full
# ---------------------------------------------------------------------------


@router.get("/full")
async def get_full_profile(
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
) -> dict[str, Any]:
    service = _get_pd_service(db, redis)
    sections = await service.get_full_profile(employee.id)
    return {
        "personal_data": _serialize_pd(sections["personal_data"]),
        "citizenship": _serialize_citizenship(sections["citizenship"]),
        "documents": _serialize_docs(sections["documents"]),
        "addresses": _serialize_addresses(sections["addresses"]),
        "education": _serialize_education(sections["education"]),
        "family": _serialize_family(sections["family"]),
        "emergency_contacts": [
            _serialize_emergency(c) for c in sections["emergency_contacts"]
        ],
        "contacts": _serialize_contact(await _get_employee_contact(db, employee.id)),
        "social_info": _serialize_social(sections["social_info"]),
        "medical_certificates": _serialize_medical(sections["medical_certificates"]),
        "bank_accounts": _serialize_bank_accounts(sections["bank_accounts"]),
    }


# ---------------------------------------------------------------------------
# /profile/personal-data
# ---------------------------------------------------------------------------


@router.get("/personal-data")
async def get_personal_data(
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
) -> dict[str, Any]:
    service = _get_pd_service(db, redis)
    row = await service.get_personal_data(employee.id)
    return {"personal_data": _serialize_pd(row)}


@router.patch("/personal-data")
async def update_personal_data(
    body: PersonalDataUpdate,
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
    request: Request,
    is_first_fill: bool = Query(default=False),
) -> dict[str, Any]:
    service = _get_pd_service(db, redis)
    data = body.model_dump(exclude_none=True)
    row = await service.update_section(employee.id, "basic_data", data, is_first_fill)
    await db.commit()
    return {"personal_data": _serialize_pd(row)}


# ---------------------------------------------------------------------------
# /profile/citizenship
# ---------------------------------------------------------------------------


@router.get("/citizenship")
async def get_citizenship(
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
) -> dict[str, Any]:
    service = _get_pd_service(db, redis)
    rows = await service.get_citizenship_records(employee.id)
    return {"citizenship": _serialize_citizenship(rows)}


@router.patch("/citizenship")
async def patch_citizenship(
    body: CitizenshipRecordCreate,
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
    is_first_fill: bool = Query(default=False),
) -> dict[str, Any]:
    pd_repo = PersonalDataRepository(db)
    if is_first_fill:
        data = body.model_dump()
        data["employee_id"] = employee.id
        data["data_source"] = "user"
        row = await pd_repo.add_citizenship_record(data)
        await db.commit()
        return {"record": CitizenshipRecordResponse.model_validate(row).model_dump(mode="json")}
    # Otherwise send change request
    cr_service = _get_cr_service(db, redis)
    emp_repo_data = await pd_repo.get_citizenship_records(employee.id)
    old_val = emp_repo_data[0].__dict__ if emp_repo_data else None
    cr = await cr_service.create_request(
        employee_id=employee.id,
        section="citizenship",
        field_name="citizenship_country",
        old_value=old_val,
        new_value=body.model_dump(),
        hr_email=await _resolve_hr_email(db, redis, employee),
        comment=None,
    )
    await db.commit()
    return {"change_request": _serialize_cr(cr)}


# ---------------------------------------------------------------------------
# /profile/documents
# ---------------------------------------------------------------------------


@router.get("/documents")
async def get_documents(
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
) -> dict[str, Any]:
    service = _get_pd_service(db, redis)
    rows = await service.get_identity_documents(employee.id)
    return {"documents": _serialize_docs(rows)}


@router.post("/documents", status_code=201)
async def add_document(
    body: IdentityDocumentCreate,
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
) -> dict[str, Any]:
    service = _get_pd_service(db, redis)
    doc = await service.add_identity_document(employee.id, body.model_dump())
    await db.commit()
    return {"document": IdentityDocumentResponse.model_validate(doc).model_dump(mode="json")}


@router.get("/documents/{doc_id}/download-url")
async def get_document_download_url(
    doc_id: uuid.UUID,
    employee: CurrentEmployee,
    db: DBSession,
) -> PresignedDownloadResponse:
    from app.core.minio import generate_download_url

    repo = PersonalDataRepository(db)
    doc = await repo.get_identity_document(doc_id)
    if doc is None or doc.employee_id != employee.id:
        raise NotFoundError(message=f"Document {doc_id} not found")
    if not doc.document_url:
        raise NotFoundError(message="No file attached to this document")
    url = generate_download_url(
        settings.minio_bucket_personal_data,
        doc.document_url,
        expires_seconds=3600,
    )
    return PresignedDownloadResponse(download_url=url, expires_in=3600)


@router.post("/documents/upload-url")
async def get_document_upload_url(
    employee: CurrentEmployee,
) -> PresignedUploadResponse:
    from app.core.minio import generate_upload_url

    url, key = generate_upload_url(
        settings.minio_bucket_personal_data,
        prefix=f"documents/{employee.id}",
        expires_seconds=600,
    )
    return PresignedUploadResponse(upload_url=url, object_key=key, expires_in=600)


# ---------------------------------------------------------------------------
# /profile/addresses
# ---------------------------------------------------------------------------


@router.get("/addresses")
async def get_addresses(
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
) -> dict[str, Any]:
    service = _get_pd_service(db, redis)
    rows = await service.get_addresses(employee.id)
    return {"addresses": _serialize_addresses(rows)}


@router.patch("/addresses/{address_type}")
async def update_address(
    address_type: str,
    body: AddressUpdate,
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
    is_first_fill: bool = Query(default=False),
) -> dict[str, Any]:
    if address_type not in ("registration", "residence"):
        from app.core.exceptions import ValidationError
        raise ValidationError(message="address_type must be 'registration' or 'residence'")
    service = _get_pd_service(db, redis)
    data = body.model_dump(exclude_none=True)
    addr = await service.upsert_address(employee.id, address_type, data, is_first_fill)
    await db.commit()
    return {"address": AddressResponse.model_validate(addr).model_dump(mode="json")}


# ---------------------------------------------------------------------------
# /profile/education
# ---------------------------------------------------------------------------


@router.get("/education")
async def get_education(
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
) -> dict[str, Any]:
    service = _get_pd_service(db, redis)
    rows = await service.get_education_records(employee.id)
    return {"education": _serialize_education(rows)}


@router.post("/education", status_code=201)
async def add_education(
    body: EducationRecordCreate,
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
) -> dict[str, Any]:
    service = _get_pd_service(db, redis)
    rec = await service.add_education_record(employee.id, body.model_dump())
    await db.commit()
    return {"record": EducationRecordResponse.model_validate(rec).model_dump(mode="json")}


@router.put("/education/{record_id}")
async def update_education(
    record_id: uuid.UUID,
    body: EducationRecordUpdate,
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
) -> dict[str, Any]:
    service = _get_pd_service(db, redis)
    rec = await service.update_education_record(
        employee.id, record_id, body.model_dump(exclude_none=True)
    )
    await db.commit()
    return {"record": EducationRecordResponse.model_validate(rec).model_dump(mode="json")}


@router.delete("/education/{record_id}", status_code=204)
async def delete_education(
    record_id: uuid.UUID,
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
) -> None:
    service = _get_pd_service(db, redis)
    await service.delete_education_record(employee.id, record_id)
    await db.commit()


# ---------------------------------------------------------------------------
# /profile/family
# ---------------------------------------------------------------------------


@router.get("/family")
async def get_family(
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
) -> dict[str, Any]:
    service = _get_pd_service(db, redis)
    rows = await service.get_family_members(employee.id)
    return {"family": _serialize_family(rows)}


@router.post("/family", status_code=201)
async def add_family_member(
    body: FamilyMemberCreate,
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
) -> dict[str, Any]:
    service = _get_pd_service(db, redis)
    member = await service.add_family_member(employee.id, body.model_dump())
    await db.commit()
    return {"member": _serialize_family_member(member)}


@router.put("/family/{member_id}")
async def update_family_member(
    member_id: uuid.UUID,
    body: FamilyMemberUpdate,
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
) -> dict[str, Any]:
    service = _get_pd_service(db, redis)
    member = await service.update_family_member(
        employee.id, member_id, body.model_dump(exclude_none=True)
    )
    await db.commit()
    return {"member": _serialize_family_member(member)}


@router.delete("/family/{member_id}", status_code=204)
async def delete_family_member(
    member_id: uuid.UUID,
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
) -> None:
    service = _get_pd_service(db, redis)
    await service.delete_family_member(employee.id, member_id)
    await db.commit()


# ---------------------------------------------------------------------------
# /profile/emergency-contact
# ---------------------------------------------------------------------------


@router.get("/emergency-contact")
async def get_emergency_contact(
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
) -> dict[str, Any]:
    service = _get_pd_service(db, redis)
    contact = await service.get_emergency_contact(employee.id)
    return {"emergency_contact": _serialize_emergency(contact)}


@router.put("/emergency-contact")
async def upsert_emergency_contact(
    body: EmergencyContactUpdate,
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
) -> dict[str, Any]:
    service = _get_pd_service(db, redis)
    contact = await service.upsert_emergency_contact(
        employee.id, body.model_dump(exclude_none=True)
    )
    await db.commit()
    return {"emergency_contact": _serialize_emergency(contact)}


# ---------------------------------------------------------------------------
# /profile/contacts
# ---------------------------------------------------------------------------


async def _get_employee_contact(db: DBSession, employee_id: uuid.UUID) -> Any | None:
    from sqlalchemy import select

    from app.infrastructure.models import EmployeeContact

    result = await db.execute(
        select(EmployeeContact).where(EmployeeContact.employee_id == employee_id)
    )
    return result.scalar_one_or_none()


@router.get("/contacts")
async def get_contacts(
    employee: CurrentEmployee,
    db: DBSession,
) -> dict[str, Any]:
    contact = await _get_employee_contact(db, employee.id)
    if contact is None:
        from sqlalchemy import select

        from app.infrastructure.models import User

        result = await db.execute(select(User).where(User.id == employee.user_id))
        user = result.scalar_one_or_none()
        return {
            "contacts": {
                "id": str(employee.id),
                "employee_id": str(employee.id),
                "email": user.email if user else "",
                "mobile_phone": employee.phone,
                "home_phone": None,
                "additional_phone": None,
                "data_source": "user",
                "created_at": None,
                "updated_at": None,
            }
        }
    return {"contacts": _serialize_contact(contact)}


@router.put("/contacts")
async def upsert_contacts(
    body: EmployeeContactUpdate,
    employee: CurrentEmployee,
    db: DBSession,
) -> dict[str, Any]:
    from sqlalchemy import select

    from app.infrastructure.models import EmployeeContact

    contact = await _get_employee_contact(db, employee.id)
    data = body.model_dump(exclude_unset=True)
    if contact is None:
        contact = EmployeeContact(
            employee_id=employee.id,
            email=data.get("email") or "",
            mobile_phone=data.get("mobile_phone") or employee.phone,
            home_phone=data.get("home_phone"),
            additional_phone=data.get("additional_phone"),
            data_source="user",
        )
        db.add(contact)
    else:
        for key, value in data.items():
            setattr(contact, key, value)

    if "mobile_phone" in data and data["mobile_phone"] is not None:
        from app.infrastructure.models import Employee

        result = await db.execute(select(Employee).where(Employee.id == employee.id))
        employee_row = result.scalar_one_or_none()
        if employee_row is not None:
            employee_row.phone = data["mobile_phone"]

    await db.commit()
    await db.refresh(contact)
    return {"contacts": _serialize_contact(contact)}


# ---------------------------------------------------------------------------
# /profile/social-info
# ---------------------------------------------------------------------------


@router.get("/social-info")
async def get_social_info(
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
) -> dict[str, Any]:
    service = _get_pd_service(db, redis)
    info = await service.get_social_info(employee.id)
    return {"social_info": _serialize_social(info)}


@router.patch("/social-info")
async def update_social_info(
    body: SocialInfoUpdate,
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
) -> dict[str, Any]:
    service = _get_pd_service(db, redis)
    info = await service.upsert_social_info(employee.id, body.model_dump(exclude_none=True))
    await db.commit()
    return {"social_info": _serialize_social(info)}


# ---------------------------------------------------------------------------
# /profile/medical-certs
# ---------------------------------------------------------------------------


@router.get("/medical-certs")
async def get_medical_certs(
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
) -> dict[str, Any]:
    service = _get_pd_service(db, redis)
    rows = await service.get_medical_certificates(employee.id)
    return {"medical_certificates": _serialize_medical(rows)}


@router.post("/medical-certs", status_code=201)
async def add_medical_cert(
    body: MedicalCertificateCreate,
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
) -> dict[str, Any]:
    service = _get_pd_service(db, redis)
    cert = await service.add_medical_certificate(employee.id, body.model_dump())
    await db.commit()
    return {"certificate": MedicalCertificateResponse.model_validate(cert).model_dump(mode="json")}


@router.post("/medical-certs/upload-url")
async def get_medical_cert_upload_url(
    employee: CurrentEmployee,
) -> PresignedUploadResponse:
    from app.core.minio import generate_upload_url

    url, key = generate_upload_url(
        settings.minio_bucket_personal_data,
        prefix=f"medical/{employee.id}",
        expires_seconds=600,
    )
    return PresignedUploadResponse(upload_url=url, object_key=key, expires_in=600)


@router.delete("/medical-certs/{cert_id}", status_code=204)
async def delete_medical_cert(
    cert_id: uuid.UUID,
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
) -> None:
    service = _get_pd_service(db, redis)
    await service.delete_medical_certificate(employee.id, cert_id)
    await db.commit()


# ---------------------------------------------------------------------------
# /profile/bank-accounts
# ---------------------------------------------------------------------------


@router.get("/bank-accounts")
async def get_bank_accounts(
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
) -> dict[str, Any]:
    service = _get_pd_service(db, redis)
    rows = await service.get_bank_accounts(employee.id)
    return {"bank_accounts": _serialize_bank_accounts(rows)}


@router.post("/bank-accounts", status_code=201)
async def add_bank_account(
    body: BankAccountCreate,
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
) -> dict[str, Any]:
    service = _get_pd_service(db, redis)
    account = await service.add_bank_account(employee.id, body.model_dump())
    await db.commit()
    return {"bank_account": _serialize_bank_account(account)}


@router.post("/bank-accounts/upload-url")
async def get_bank_account_upload_url(
    employee: CurrentEmployee,
) -> PresignedUploadResponse:
    from app.core.minio import generate_upload_url

    url, key = generate_upload_url(
        settings.minio_bucket_personal_data,
        prefix=f"bank/{employee.id}",
        expires_seconds=600,
    )
    return PresignedUploadResponse(upload_url=url, object_key=key, expires_in=600)


@router.delete("/bank-accounts/{account_id}", status_code=204)
async def delete_bank_account(
    account_id: uuid.UUID,
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
) -> None:
    service = _get_pd_service(db, redis)
    await service.delete_bank_account(employee.id, account_id)
    await db.commit()


# ---------------------------------------------------------------------------
# /profile/change-requests
# ---------------------------------------------------------------------------


@router.get("/change-requests")
async def list_change_requests(
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
    status: str | None = Query(default=None),
) -> dict[str, Any]:
    service = _get_cr_service(db, redis)
    rows = await service.list_by_employee(employee.id, status)
    return {"items": _serialize_crs(rows), "total": len(rows)}


@router.post("/change-requests", status_code=201)
async def create_change_request(
    body: ChangeRequestCreate,
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
    request: Request,
) -> dict[str, Any]:
    service = _get_cr_service(db, redis)
    cr = await service.create_request(
        employee_id=employee.id,
        section=body.section,
        field_name=body.field_name,
        old_value=body.old_value,
        new_value=body.new_value,
        hr_email=await _resolve_hr_email(db, redis, employee),
        comment=body.comment,
        document_url=body.document_url,
    )
    await db.commit()
    return {"change_request": _serialize_cr(cr)}


@router.get("/change-requests/{request_id}")
async def get_change_request(
    request_id: uuid.UUID,
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
) -> dict[str, Any]:
    service = _get_cr_service(db, redis)
    cr = await service.get_request(request_id, employee.id)
    return {"change_request": _serialize_cr(cr)}


@router.delete("/change-requests/{request_id}", status_code=204)
async def cancel_change_request(
    request_id: uuid.UUID,
    employee: CurrentEmployee,
    db: DBSession,
    redis: RedisClient,
) -> None:
    service = _get_cr_service(db, redis)
    await service.cancel_request(request_id, employee.id)
    await db.commit()


# ===========================================================================
# HR endpoints
# ===========================================================================

HROrAdminEmployee = Annotated[EmployeeDomain, Depends(require_roles("hr", "admin"))]


@hr_router.get("/change-requests")
async def hr_list_change_requests(
    hr_employee: HROrAdminEmployee,
    db: DBSession,
    redis: RedisClient,
    status: str | None = Query(default=None),
) -> dict[str, Any]:
    service = _get_cr_service(db, redis)
    rows = await service.list_for_reviewer(
        await _get_user_email(db, hr_employee.user_id),
        is_admin=hr_employee.role == "admin",
        status=status,
    )
    return {"items": _serialize_crs(rows), "total": len(rows)}


@hr_router.get("/change-requests/{request_id}")
async def hr_get_change_request(
    request_id: uuid.UUID,
    hr_employee: HROrAdminEmployee,
    db: DBSession,
    redis: RedisClient,
) -> dict[str, Any]:
    service = _get_cr_service(db, redis)
    cr = await service.get_request_for_reviewer(
        request_id,
        await _get_user_email(db, hr_employee.user_id),
        is_admin=hr_employee.role == "admin",
    )
    return {"change_request": _serialize_cr(cr)}


@hr_router.post("/change-requests/{request_id}/approve")
async def hr_approve_change_request(
    request_id: uuid.UUID,
    body: ChangeRequestApprove,
    request: Request,
    hr_employee: HROrAdminEmployee,
    db: DBSession,
    redis: RedisClient,
) -> dict[str, Any]:
    service = _get_cr_service(db, redis)
    cr = await service.approve_request(
        request_id=request_id,
        hr_employee_id=hr_employee.id,
        hr_email=await _get_user_email(db, hr_employee.user_id),
        is_admin=hr_employee.role == "admin",
        hr_comment=body.hr_comment,
        actor_user_id=hr_employee.user_id,
        ip=get_client_ip(request),
        db_session=db,
    )
    await db.commit()
    return {"change_request": _serialize_cr(cr)}


@hr_router.post("/change-requests/{request_id}/reject")
async def hr_reject_change_request(
    request_id: uuid.UUID,
    body: ChangeRequestReject,
    request: Request,
    hr_employee: HROrAdminEmployee,
    db: DBSession,
    redis: RedisClient,
) -> dict[str, Any]:
    service = _get_cr_service(db, redis)
    cr = await service.reject_request(
        request_id=request_id,
        hr_employee_id=hr_employee.id,
        reason=body.reason,
        hr_email=await _get_user_email(db, hr_employee.user_id),
        is_admin=hr_employee.role == "admin",
        actor_user_id=hr_employee.user_id,
        ip=get_client_ip(request),
        db_session=db,
    )
    await db.commit()
    return {"change_request": _serialize_cr(cr)}
