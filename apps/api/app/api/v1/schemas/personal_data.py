"""Pydantic v2 schemas for the personal-data module."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------


class DataSourceInfo(BaseModel):
    is_editable: bool
    source: Literal["1c", "user", "hr_approved"]
    last_synced_at: datetime | None = None


# ---------------------------------------------------------------------------
# PersonalData
# ---------------------------------------------------------------------------


class PersonalDataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: uuid.UUID
    first_name_en: str | None = None
    last_name_en: str | None = None
    middle_name_en: str | None = None
    gender: str | None = None
    nationality: str | None = None
    place_of_birth: str | None = None
    marital_status: str | None = None
    data_source: str
    sync_hash: str | None = None
    created_at: datetime
    updated_at: datetime


class PersonalDataUpdate(BaseModel):
    first_name_en: str | None = None
    last_name_en: str | None = None
    middle_name_en: str | None = None
    gender: Literal["male", "female"] | None = None
    nationality: str | None = None
    place_of_birth: str | None = None
    marital_status: Literal["single", "married", "divorced", "widowed"] | None = None


# ---------------------------------------------------------------------------
# CitizenshipRecord
# ---------------------------------------------------------------------------


class CitizenshipRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: uuid.UUID
    citizenship_country: str
    status: str
    iin_in_country: str | None = None
    is_primary: bool
    data_source: str
    created_at: datetime
    updated_at: datetime


class CitizenshipRecordCreate(BaseModel):
    citizenship_country: str
    status: Literal["rk_citizen", "foreign_citizen", "stateless"]
    iin_in_country: str | None = None
    is_primary: bool = True


class CitizenshipRecordUpdate(BaseModel):
    citizenship_country: str | None = None
    status: Literal["rk_citizen", "foreign_citizen", "stateless"] | None = None
    iin_in_country: str | None = None
    is_primary: bool | None = None


# ---------------------------------------------------------------------------
# IdentityDocument
# ---------------------------------------------------------------------------


class IdentityDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: uuid.UUID
    document_type: str
    series: str | None = None
    number: str
    issued_by: str
    issue_date: date
    expiry_date: date | None = None
    document_url: str | None = None
    is_active: bool
    data_source: str
    external_id_1c: str | None = None
    created_at: datetime
    updated_at: datetime


class IdentityDocumentCreate(BaseModel):
    document_type: Literal["national_id", "passport", "residence_permit", "other"]
    series: str | None = None
    number: str
    issued_by: str
    issue_date: date
    expiry_date: date | None = None
    document_url: str | None = None


# ---------------------------------------------------------------------------
# EmployeeAddress
# ---------------------------------------------------------------------------


class AddressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: uuid.UUID
    address_type: str
    country: str
    region: str | None = None
    city: str
    street: str | None = None
    house: str | None = None
    apartment: str | None = None
    data_source: str
    created_at: datetime
    updated_at: datetime


class AddressUpdate(BaseModel):
    country: str | None = None
    region: str | None = None
    city: str | None = None
    street: str | None = None
    house: str | None = None
    apartment: str | None = None


# ---------------------------------------------------------------------------
# EducationRecord
# ---------------------------------------------------------------------------


class EducationRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: uuid.UUID
    education_type: str
    institution_name: str
    specialty: str | None = None
    qualification: str | None = None
    graduation_date: date | None = None
    document_number: str | None = None
    document_url: str | None = None
    data_source: str
    external_id_1c: str | None = None
    created_at: datetime
    updated_at: datetime


class EducationRecordCreate(BaseModel):
    education_type: Literal["higher", "secondary", "technical", "advanced_qualification", "other"]
    institution_name: str
    specialty: str | None = None
    qualification: str | None = None
    graduation_date: date | None = None
    document_number: str | None = None
    document_url: str | None = None


class EducationRecordUpdate(BaseModel):
    education_type: (
        Literal["higher", "secondary", "technical", "advanced_qualification", "other"] | None
    ) = None
    institution_name: str | None = None
    specialty: str | None = None
    qualification: str | None = None
    graduation_date: date | None = None
    document_number: str | None = None
    document_url: str | None = None


# ---------------------------------------------------------------------------
# FamilyMember
# ---------------------------------------------------------------------------


class FamilyMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: uuid.UUID
    member_type: str
    first_name: str
    last_name: str
    middle_name: str | None = None
    birth_date: date | None = None
    # IIN is never returned in plaintext – callers receive a masked hint
    iin_masked: str | None = Field(default=None, exclude=False)
    birth_cert_number: str | None = None
    birth_cert_series: str | None = None
    birth_cert_issue_date: date | None = None
    birth_cert_issued_by: str | None = None
    spouse_status: str | None = None
    marriage_cert_number: str | None = None
    marriage_cert_issue_date: date | None = None
    marriage_cert_org: str | None = None
    document_url: str | None = None
    data_source: str
    created_at: datetime
    updated_at: datetime


class FamilyMemberCreate(BaseModel):
    member_type: Literal["child", "spouse", "ex_spouse"]
    first_name: str
    last_name: str
    middle_name: str | None = None
    birth_date: date | None = None
    iin: str | None = Field(default=None, max_length=12)
    # Child fields
    birth_cert_number: str | None = None
    birth_cert_series: str | None = None
    birth_cert_issue_date: date | None = None
    birth_cert_issued_by: str | None = None
    # Spouse fields
    spouse_status: str | None = None
    marriage_cert_number: str | None = None
    marriage_cert_issue_date: date | None = None
    marriage_cert_org: str | None = None
    document_url: str | None = None


class FamilyMemberUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None
    birth_date: date | None = None
    iin: str | None = Field(default=None, max_length=12)
    birth_cert_number: str | None = None
    birth_cert_series: str | None = None
    birth_cert_issue_date: date | None = None
    birth_cert_issued_by: str | None = None
    spouse_status: str | None = None
    marriage_cert_number: str | None = None
    marriage_cert_issue_date: date | None = None
    marriage_cert_org: str | None = None
    document_url: str | None = None


# ---------------------------------------------------------------------------
# EmergencyContact
# ---------------------------------------------------------------------------


class EmergencyContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: uuid.UUID
    full_name: str
    phone: str
    address: str | None = None
    relationship: str
    created_at: datetime
    updated_at: datetime


class EmergencyContactUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    address: str | None = None
    relationship: str | None = None


# ---------------------------------------------------------------------------
# EmployeeContact
# ---------------------------------------------------------------------------


class EmployeeContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: uuid.UUID
    email: str
    mobile_phone: str
    home_phone: str | None = None
    additional_phone: str | None = None
    data_source: str
    created_at: datetime
    updated_at: datetime


class EmployeeContactUpdate(BaseModel):
    email: EmailStr | None = None
    mobile_phone: str | None = None
    home_phone: str | None = None
    additional_phone: str | None = None

    @field_validator("mobile_phone", "home_phone", "additional_phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return value
        normalized = value.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if normalized.startswith("+"):
            normalized = normalized[1:]
        if not normalized.isdigit() or len(normalized) < 7 or len(normalized) > 15:
            raise ValueError("phone must contain 7-15 digits")
        return value


# ---------------------------------------------------------------------------
# SocialInfo
# ---------------------------------------------------------------------------


class SocialInfoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: uuid.UUID
    pension_status: str | None = None
    has_disability: bool
    disability_group: int | None = None
    is_ww2_veteran: bool
    is_ww2_family: bool
    document_url: str | None = None
    data_source: str
    created_at: datetime
    updated_at: datetime


class SocialInfoUpdate(BaseModel):
    pension_status: str | None = None
    has_disability: bool | None = None
    disability_group: int | None = None
    is_ww2_veteran: bool | None = None
    is_ww2_family: bool | None = None
    document_url: str | None = None


# ---------------------------------------------------------------------------
# MedicalCertificate
# ---------------------------------------------------------------------------


class MedicalCertificateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: uuid.UUID
    cert_type: str
    cert_number: str
    issue_date: date
    expiry_date: date | None = None
    document_url: str
    created_at: datetime
    updated_at: datetime


class MedicalCertificateCreate(BaseModel):
    cert_type: Literal["narco_dispensary", "psycho_dispensary", "form_075"]
    cert_number: str
    issue_date: date
    expiry_date: date | None = None
    document_url: str


# ---------------------------------------------------------------------------
# BankAccount
# ---------------------------------------------------------------------------


class BankAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: uuid.UUID
    bank_name: str
    # Returns masked account number (last 4 digits)
    account_number_masked: str | None = Field(default=None, exclude=False)
    bik: str
    account_type: str
    holder_name: str
    document_url: str | None = None
    is_primary: bool
    data_source: str
    created_at: datetime
    updated_at: datetime


class BankAccountCreate(BaseModel):
    bank_name: str
    account_number: str
    bik: str
    account_type: Literal["standard", "social", "other"] = "standard"
    holder_name: str
    document_url: str | None = None
    is_primary: bool = True


# ---------------------------------------------------------------------------
# ChangeRequest
# ---------------------------------------------------------------------------


class ChangeRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: uuid.UUID
    section: str
    field_name: str
    old_value: Any | None = None
    new_value: Any
    comment: str | None = None
    document_url: str | None = None
    hr_email: str
    status: str
    hr_comment: str | None = None
    processed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ChangeRequestCreate(BaseModel):
    section: Literal[
        "basic_data", "citizenship", "document", "address", "contacts", "education",
        "family", "emergency_contact", "social_info", "medical", "bank", "other",
    ]
    field_name: str
    old_value: Any | None = None
    new_value: Any
    comment: str | None = None
    document_url: str | None = None


class ChangeRequestApprove(BaseModel):
    hr_comment: str | None = None


class ChangeRequestReject(BaseModel):
    reason: str


# ---------------------------------------------------------------------------
# PresignedURL
# ---------------------------------------------------------------------------


class PresignedUploadResponse(BaseModel):
    upload_url: str
    object_key: str
    expires_in: int


class PresignedDownloadResponse(BaseModel):
    download_url: str
    expires_in: int


# ---------------------------------------------------------------------------
# FullProfileResponse
# ---------------------------------------------------------------------------


class FullProfileResponse(BaseModel):
    personal_data: PersonalDataResponse | None = None
    citizenship: list[CitizenshipRecordResponse] = []
    documents: list[IdentityDocumentResponse] = []
    addresses: list[AddressResponse] = []
    education: list[EducationRecordResponse] = []
    family: list[FamilyMemberResponse] = []
    emergency_contacts: list[EmergencyContactResponse] = []
    contacts: EmployeeContactResponse | None = None
    social_info: SocialInfoResponse | None = None
    medical_certificates: list[MedicalCertificateResponse] = []
    bank_accounts: list[BankAccountResponse] = []
