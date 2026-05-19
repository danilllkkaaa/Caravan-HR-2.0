from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.orm import relationship as orm_relationship

# ---------------------------------------------------------------------------
# Personal-data enums (defined here so SQLAlchemy knows about them)
# ---------------------------------------------------------------------------
DataSourceEnum = Enum(
    "1c", "user", "hr_approved",
    name="data_source",
    create_type=False,
)
GenderTypeEnum = Enum(
    "male", "female",
    name="gender_type",
    create_type=False,
)
CitizenshipStatusEnum = Enum(
    "rk_citizen", "foreign_citizen", "stateless",
    name="citizenship_status",
    create_type=False,
)
IdentityDocTypeEnum = Enum(
    "national_id", "passport", "residence_permit", "other",
    name="identity_doc_type",
    create_type=False,
)
AddressTypeEnum = Enum(
    "registration", "residence",
    name="address_type",
    create_type=False,
)
EducationTypeEnum = Enum(
    "higher", "secondary", "technical", "advanced_qualification", "other",
    name="education_type",
    create_type=False,
)
FamilyMemberTypeEnum = Enum(
    "child", "spouse", "ex_spouse",
    name="family_member_type",
    create_type=False,
)
MaritalStatusEnum = Enum(
    "single", "married", "divorced", "widowed",
    name="marital_status",
    create_type=False,
)
MedicalCertTypeEnum = Enum(
    "narco_dispensary", "psycho_dispensary", "form_075",
    name="medical_cert_type",
    create_type=False,
)
BankAccountTypeEnum = Enum(
    "standard", "social", "other",
    name="bank_account_type",
    create_type=False,
)
ChangeRequestStatusEnum = Enum(
    "sent", "under_review", "approved", "rejected",
    name="change_request_status",
    create_type=False,
)
ChangeRequestSectionEnum = Enum(
    "basic_data", "citizenship", "document", "address", "education",
    "family", "emergency_contact", "social_info", "medical", "bank", "other",
    name="change_request_section",
    create_type=False,
)

JsonType = JSON().with_variant(JSONB, "postgresql")
InetType = String(45).with_variant(INET, "postgresql")

EmployeeRoleEnum = Enum(
    "employee",
    "manager",
    "hr",
    "admin",
    name="employee_role",
    create_type=True,
)
SyncSourceEnum = Enum("1c", "manual", name="sync_source", create_type=True)
VacationStatusEnum = Enum(
    "draft",
    "pending",
    "approved",
    "rejected",
    "cancelled",
    name="vacation_status",
    create_type=True,
)
SickLeaveStatusEnum = Enum("open", "closed", name="sick_leave_status", create_type=True)
AttendanceEventTypeEnum = Enum(
    "entry", "exit", name="attendance_event_type", create_type=True
)
TimesheetStatusEnum = Enum(
    "work",
    "overtime",
    "partial",
    "weekend",
    "holiday",
    "absence",
    "vacation",
    "sick",
    name="timesheet_status",
    create_type=True,
)
NotificationTypeEnum = Enum(
    "approved",
    "rejected",
    "info",
    "reminder",
    "sharepoint_link",
    name="notification_type",
    create_type=True,
)


class Base(DeclarativeBase):
    pass


class UUIDPKMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class User(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    employee: Mapped[Employee | None] = orm_relationship(
        "Employee", back_populates="user", uselist=False
    )
    refresh_tokens: Mapped[list[RefreshToken]] = orm_relationship(
        "RefreshToken", back_populates="user"
    )


class Department(UUIDPKMixin, Base):
    __tablename__ = "departments"

    external_id_1c: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True
    )
    head_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True
    )


class Position(UUIDPKMixin, Base):
    __tablename__ = "positions"

    external_id_1c: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)


class WorkLocation(UUIDPKMixin, Base):
    __tablename__ = "work_locations"

    external_id_1c: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(128), nullable=False)
    hr_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True
    )


class Employee(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "employees"
    __table_args__ = (
        Index("ix_employees_external_id_1c", "external_id_1c"),
        Index("ix_employees_personnel_number", "personnel_number"),
        Index("ix_employees_department_id", "department_id"),
        Index("ix_employees_manager_id", "manager_id"),
        Index("ix_employees_work_location_id", "work_location_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )
    external_id_1c: Mapped[str] = mapped_column(String(64), nullable=False)
    personnel_number: Mapped[str] = mapped_column(String(32), nullable=False)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    middle_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    phone: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False
    )
    position_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("positions.id"), nullable=False
    )
    manager_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True
    )
    role: Mapped[str] = mapped_column(EmployeeRoleEnum, nullable=False, default="employee")
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    work_location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("work_locations.id"), nullable=True
    )
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    sync_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")

    user: Mapped[User] = orm_relationship("User", back_populates="employee")
    vacation_balances: Mapped[list[VacationBalance]] = orm_relationship(
        "VacationBalance", back_populates="employee"
    )
    vacation_requests: Mapped[list[VacationRequest]] = orm_relationship(
        "VacationRequest",
        back_populates="employee",
        foreign_keys="VacationRequest.employee_id",
    )
    sick_leaves: Mapped[list[SickLeave]] = orm_relationship(
        "SickLeave", back_populates="employee", foreign_keys="SickLeave.employee_id"
    )
    notifications: Mapped[list[Notification]] = orm_relationship(
        "Notification", back_populates="employee"
    )
    timesheet_entries: Mapped[list[TimesheetEntry]] = orm_relationship(
        "TimesheetEntry", back_populates="employee"
    )

    # Personal data relationships
    personal_data: Mapped[PersonalData | None] = orm_relationship(
        "PersonalData", back_populates="employee", uselist=False
    )
    citizenship_records: Mapped[list[CitizenshipRecord]] = orm_relationship(
        "CitizenshipRecord", back_populates="employee"
    )
    identity_documents: Mapped[list[IdentityDocument]] = orm_relationship(
        "IdentityDocument", back_populates="employee"
    )
    addresses: Mapped[list[EmployeeAddress]] = orm_relationship(
        "EmployeeAddress", back_populates="employee"
    )
    education_records: Mapped[list[EducationRecord]] = orm_relationship(
        "EducationRecord", back_populates="employee"
    )
    family_members: Mapped[list[FamilyMember]] = orm_relationship(
        "FamilyMember", back_populates="employee"
    )
    emergency_contacts: Mapped[list[EmergencyContact]] = orm_relationship(
        "EmergencyContact", back_populates="employee"
    )
    contact_info: Mapped[EmployeeContact | None] = orm_relationship(
        "EmployeeContact", back_populates="employee", uselist=False
    )
    social_info: Mapped[SocialInfo | None] = orm_relationship(
        "SocialInfo", back_populates="employee", uselist=False
    )
    medical_certificates: Mapped[list[MedicalCertificate]] = orm_relationship(
        "MedicalCertificate", back_populates="employee"
    )
    bank_accounts: Mapped[list[BankAccount]] = orm_relationship(
        "BankAccount", back_populates="employee"
    )
    change_requests: Mapped[list[PersonalDataChangeRequest]] = orm_relationship(
        "PersonalDataChangeRequest",
        back_populates="employee",
        foreign_keys="PersonalDataChangeRequest.employee_id",
    )


class Holiday(Base):
    __tablename__ = "holidays"
    __table_args__ = (UniqueConstraint("date", name="uq_holidays_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False, default="KZ")


class VacationType(UUIDPKMixin, Base):
    __tablename__ = "vacation_types"

    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_documents: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class VacationBalance(UUIDPKMixin, Base):
    __tablename__ = "vacation_balances"
    __table_args__ = (
        UniqueConstraint("employee_id", "year", name="uq_vacation_balances_employee_year"),
        Index("ix_vacation_balances_employee_year", "employee_id", "year"),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    total_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    used_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    sync_source: Mapped[str] = mapped_column(SyncSourceEnum, nullable=False, default="manual")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    employee: Mapped[Employee] = orm_relationship("Employee", back_populates="vacation_balances")


class VacationRequest(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "vacation_requests"
    __table_args__ = (
        Index("ix_vacation_requests_employee_status", "employee_id", "status"),
        Index("ix_vacation_requests_dates", "start_date", "end_date"),
        Index("ix_vacation_requests_approver", "approver_id"),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False
    )
    vacation_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vacation_types.id"), nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    days_count: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(VacationStatusEnum, nullable=False, default="draft")
    approver_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True
    )
    approver_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    employee: Mapped[Employee] = orm_relationship(
        "Employee", back_populates="vacation_requests", foreign_keys=[employee_id]
    )
    vacation_type: Mapped[VacationType] = orm_relationship("VacationType")
    approver: Mapped[Employee | None] = orm_relationship("Employee", foreign_keys=[approver_id])


class SickLeave(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "sick_leaves"
    __table_args__ = (Index("ix_sick_leaves_employee_status", "employee_id", "status"),)

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    open_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    close_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(SickLeaveStatusEnum, nullable=False, default="open")
    closed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True
    )

    employee: Mapped[Employee] = orm_relationship(
        "Employee", back_populates="sick_leaves", foreign_keys=[employee_id]
    )
    closed_by_employee: Mapped[Employee | None] = orm_relationship(
        "Employee", foreign_keys=[closed_by]
    )


class AttendanceEvent(Base):
    __tablename__ = "attendance_events"
    __table_args__ = (
        Index("ix_attendance_events_employee_at", "employee_id", "event_at"),
        Index("ix_attendance_events_processed", "processed"),
        Index("ix_attendance_events_hikvision_person_id", "hikvision_person_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    employee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True
    )
    hikvision_person_id: Mapped[str] = mapped_column(String(255), nullable=False)
    event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_type: Mapped[str] = mapped_column(AttendanceEventTypeEnum, nullable=False)
    device_id: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JsonType, nullable=False, default=dict)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class TimesheetEntry(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "timesheet_entries"
    __table_args__ = (
        UniqueConstraint("employee_id", "date", name="uq_timesheet_employee_date"),
        Index("ix_timesheet_entries_employee_date", "employee_id", "date"),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    first_entry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_exit_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    worked_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(TimesheetStatusEnum, nullable=False, default="work")
    schedule_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    employee: Mapped[Employee] = orm_relationship("Employee", back_populates="timesheet_entries")


class Notification(UUIDPKMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_employee_read", "employee_id", "read_at"),
        Index("ix_notifications_created_at", "created_at"),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False
    )
    type: Mapped[str] = mapped_column(NotificationTypeEnum, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JsonType, nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    employee: Mapped[Employee] = orm_relationship("Employee", back_populates="notifications")


class RefreshToken(UUIDPKMixin, Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (
        Index("ix_refresh_tokens_token_hash", "token_hash"),
        Index("ix_refresh_tokens_user_revoked", "user_id", "revoked_at"),
        Index("ix_refresh_tokens_expires_at", "expires_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    device_info: Mapped[dict[str, Any]] = mapped_column(JsonType, nullable=False, default=dict)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped[User] = orm_relationship("User", back_populates="refresh_tokens")


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_log_actor", "actor_id"),
        Index("ix_audit_log_target", "target_type", "target_id"),
        Index("ix_audit_log_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    target_type: Mapped[str] = mapped_column(String(255), nullable=False)
    target_id: Mapped[str] = mapped_column(String(255), nullable=False)
    changes: Mapped[dict[str, Any]] = mapped_column(JsonType, nullable=False, default=dict)
    ip: Mapped[str] = mapped_column(InetType, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ===========================================================================
# Personal Data module — ORM models
# ===========================================================================


class PersonalData(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "personal_data"
    __table_args__ = (Index("ix_personal_data_employee_id", "employee_id"),)

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False, unique=True,
    )
    first_name_en: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name_en: Mapped[str | None] = mapped_column(String(100), nullable=True)
    middle_name_en: Mapped[str | None] = mapped_column(String(100), nullable=True)
    gender: Mapped[str | None] = mapped_column(GenderTypeEnum, nullable=True)
    nationality: Mapped[str | None] = mapped_column(String(100), nullable=True)
    place_of_birth: Mapped[str | None] = mapped_column(String(255), nullable=True)
    marital_status: Mapped[str | None] = mapped_column(MaritalStatusEnum, nullable=True)
    data_source: Mapped[str] = mapped_column(
        DataSourceEnum, nullable=False, server_default="1c"
    )
    sync_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_synced_at_1c: Mapped[datetime | None] = mapped_column(
        "1c_last_synced_at", DateTime(timezone=True), nullable=True
    )

    employee: Mapped[Employee] = orm_relationship("Employee", back_populates="personal_data")


class CitizenshipRecord(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "citizenship_records"
    __table_args__ = (Index("ix_citizenship_records_employee_id", "employee_id"),)

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    citizenship_country: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(CitizenshipStatusEnum, nullable=False)
    iin_in_country: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    data_source: Mapped[str] = mapped_column(
        DataSourceEnum, nullable=False, server_default="1c"
    )

    employee: Mapped[Employee] = orm_relationship("Employee", back_populates="citizenship_records")


class IdentityDocument(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "identity_documents"
    __table_args__ = (Index("ix_identity_documents_employee_id", "employee_id"),)

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    document_type: Mapped[str] = mapped_column(IdentityDocTypeEnum, nullable=False)
    series: Mapped[str | None] = mapped_column(String(20), nullable=True)
    number: Mapped[str] = mapped_column(String(50), nullable=False)
    issued_by: Mapped[str] = mapped_column(String(255), nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    document_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    data_source: Mapped[str] = mapped_column(
        DataSourceEnum, nullable=False, server_default="1c"
    )
    external_id_1c: Mapped[str | None] = mapped_column(String(64), nullable=True)

    employee: Mapped[Employee] = orm_relationship("Employee", back_populates="identity_documents")


class EmployeeAddress(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "employee_addresses"
    __table_args__ = (
        UniqueConstraint("employee_id", "address_type", name="uq_employee_addresses_emp_type"),
        Index("ix_employee_addresses_employee_id", "employee_id"),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    address_type: Mapped[str] = mapped_column(AddressTypeEnum, nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    street: Mapped[str | None] = mapped_column(String(255), nullable=True)
    house: Mapped[str | None] = mapped_column(String(20), nullable=True)
    apartment: Mapped[str | None] = mapped_column(String(20), nullable=True)
    data_source: Mapped[str] = mapped_column(
        DataSourceEnum, nullable=False, server_default="1c"
    )

    employee: Mapped[Employee] = orm_relationship("Employee", back_populates="addresses")


class EducationRecord(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "education_records"
    __table_args__ = (Index("ix_education_records_employee_id", "employee_id"),)

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    education_type: Mapped[str] = mapped_column(EducationTypeEnum, nullable=False)
    institution_name: Mapped[str] = mapped_column(String(255), nullable=False)
    specialty: Mapped[str | None] = mapped_column(String(255), nullable=True)
    qualification: Mapped[str | None] = mapped_column(String(255), nullable=True)
    graduation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    document_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    document_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_source: Mapped[str] = mapped_column(
        DataSourceEnum, nullable=False, server_default="1c"
    )
    external_id_1c: Mapped[str | None] = mapped_column(String(64), nullable=True)

    employee: Mapped[Employee] = orm_relationship("Employee", back_populates="education_records")


class FamilyMember(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "family_members"
    __table_args__ = (Index("ix_family_members_employee_id", "employee_id"),)

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    member_type: Mapped[str] = mapped_column(FamilyMemberTypeEnum, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Fernet-encrypted IIN stored as ciphertext
    iin_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Child-specific
    birth_cert_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    birth_cert_series: Mapped[str | None] = mapped_column(String(50), nullable=True)
    birth_cert_issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    birth_cert_issued_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Spouse-specific
    spouse_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    marriage_cert_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    marriage_cert_issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    marriage_cert_org: Mapped[str | None] = mapped_column(String(255), nullable=True)
    document_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_source: Mapped[str] = mapped_column(
        DataSourceEnum, nullable=False, server_default="1c"
    )
    external_id_1c: Mapped[str | None] = mapped_column(String(64), nullable=True)

    employee: Mapped[Employee] = orm_relationship("Employee", back_populates="family_members")


class EmergencyContact(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "emergency_contacts"
    __table_args__ = (Index("ix_emergency_contacts_employee_id", "employee_id"),)

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    relationship: Mapped[str] = mapped_column(String(100), nullable=False)

    employee: Mapped[Employee] = orm_relationship("Employee", back_populates="emergency_contacts")


class EmployeeContact(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "employee_contacts"
    __table_args__ = (Index("ix_employee_contacts_employee_id", "employee_id"),)

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    mobile_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    home_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    additional_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    data_source: Mapped[str] = mapped_column(
        DataSourceEnum, nullable=False, server_default="user"
    )

    employee: Mapped[Employee] = orm_relationship("Employee", back_populates="contact_info")


class SocialInfo(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "social_info"
    __table_args__ = (Index("ix_social_info_employee_id", "employee_id"),)

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False, unique=True,
    )
    pension_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    has_disability: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    disability_group: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_ww2_veteran: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_ww2_family: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    document_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_source: Mapped[str] = mapped_column(
        DataSourceEnum, nullable=False, server_default="1c"
    )

    employee: Mapped[Employee] = orm_relationship("Employee", back_populates="social_info")


class MedicalCertificate(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "medical_certificates"
    __table_args__ = (Index("ix_medical_certificates_employee_id", "employee_id"),)

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    cert_type: Mapped[str] = mapped_column(MedicalCertTypeEnum, nullable=False)
    cert_number: Mapped[str] = mapped_column(String(100), nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    document_url: Mapped[str] = mapped_column(Text, nullable=False)

    employee: Mapped[Employee] = orm_relationship("Employee", back_populates="medical_certificates")


class BankAccount(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "bank_accounts"
    __table_args__ = (Index("ix_bank_accounts_employee_id", "employee_id"),)

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    bank_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Fernet-encrypted account number stored as ciphertext
    account_number_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    bik: Mapped[str] = mapped_column(String(20), nullable=False)
    account_type: Mapped[str] = mapped_column(
        BankAccountTypeEnum, nullable=False, default="standard"
    )
    holder_name: Mapped[str] = mapped_column(String(255), nullable=False)
    document_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    data_source: Mapped[str] = mapped_column(
        DataSourceEnum, nullable=False, server_default="1c"
    )
    external_id_1c: Mapped[str | None] = mapped_column(String(64), nullable=True)

    employee: Mapped[Employee] = orm_relationship("Employee", back_populates="bank_accounts")


class PersonalDataChangeRequest(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "personal_data_change_requests"
    __table_args__ = (
        Index("ix_pdcr_employee_id", "employee_id"),
        Index("ix_pdcr_employee_status", "employee_id", "status"),
        Index("ix_pdcr_hr_employee_status", "hr_employee_id", "status"),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    section: Mapped[str] = mapped_column(ChangeRequestSectionEnum, nullable=False)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[dict[str, Any] | None] = mapped_column(JsonType, nullable=True)
    new_value: Mapped[dict[str, Any]] = mapped_column(JsonType, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    hr_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True
    )
    hr_email: Mapped[str] = mapped_column(String(320), nullable=False)
    status: Mapped[str] = mapped_column(
        ChangeRequestStatusEnum, nullable=False, default="sent"
    )
    hr_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    employee: Mapped[Employee] = orm_relationship(
        "Employee",
        back_populates="change_requests",
        foreign_keys=[employee_id],
    )
    hr_employee: Mapped[Employee | None] = orm_relationship(
        "Employee",
        foreign_keys=[hr_employee_id],
    )
