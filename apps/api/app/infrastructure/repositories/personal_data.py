"""Repository layer for the personal-data module."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.infrastructure.models import (
    BankAccount,
    CitizenshipRecord,
    EducationRecord,
    EmergencyContact,
    Employee,
    EmployeeAddress,
    EmployeeContact,
    FamilyMember,
    IdentityDocument,
    MedicalCertificate,
    PersonalData,
    PersonalDataChangeRequest,
    SocialInfo,
)

# ---------------------------------------------------------------------------
# PersonalDataRepository
# ---------------------------------------------------------------------------


class PersonalDataRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ---- personal_data ----

    async def get_personal_data(self, employee_id: uuid.UUID) -> PersonalData | None:
        stmt = select(PersonalData).where(PersonalData.employee_id == employee_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_personal_data(
        self,
        employee_id: uuid.UUID,
        data: dict[str, Any],
        source: str,
    ) -> PersonalData:
        row = await self.get_personal_data(employee_id)
        if row is None:
            row = PersonalData(
                id=uuid.uuid4(),
                employee_id=employee_id,
                data_source=source,
                **data,
            )
            self._session.add(row)
        else:
            for key, value in data.items():
                setattr(row, key, value)
            row.data_source = source
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def get_all_sections(self, employee_id: uuid.UUID) -> dict[str, Any]:
        """Return all personal-data sections for the given employee in one call."""
        personal_data = await self.get_personal_data(employee_id)
        citizenship = await self.get_citizenship_records(employee_id)
        documents = await self.get_identity_documents(employee_id)
        addresses = await self.get_addresses(employee_id)
        education = await self.get_education_records(employee_id)
        family = await self.get_family_members(employee_id)
        emergency = await self.get_emergency_contacts(employee_id)
        social = await self.get_social_info(employee_id)
        medical = await self.get_medical_certificates(employee_id)
        bank = await self.get_bank_accounts(employee_id)

        return {
            "personal_data": personal_data,
            "citizenship": citizenship,
            "documents": documents,
            "addresses": addresses,
            "education": education,
            "family": family,
            "emergency_contacts": emergency,
            "social_info": social,
            "medical_certificates": medical,
            "bank_accounts": bank,
        }

    # ---- citizenship_records ----

    async def get_citizenship_records(self, employee_id: uuid.UUID) -> list[CitizenshipRecord]:
        stmt = select(CitizenshipRecord).where(CitizenshipRecord.employee_id == employee_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add_citizenship_record(self, data: dict[str, Any]) -> CitizenshipRecord:
        row = CitizenshipRecord(id=uuid.uuid4(), **data)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def update_citizenship_record(
        self, record_id: uuid.UUID, data: dict[str, Any]
    ) -> CitizenshipRecord:
        row = await self._session.get(CitizenshipRecord, record_id)
        if row is None:
            raise NotFoundError(message=f"CitizenshipRecord {record_id} not found")
        for key, value in data.items():
            setattr(row, key, value)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    # ---- identity_documents ----

    async def get_identity_documents(self, employee_id: uuid.UUID) -> list[IdentityDocument]:
        stmt = select(IdentityDocument).where(IdentityDocument.employee_id == employee_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_identity_document(self, doc_id: uuid.UUID) -> IdentityDocument | None:
        return await self._session.get(IdentityDocument, doc_id)

    async def add_identity_document(self, data: dict[str, Any]) -> IdentityDocument:
        row = IdentityDocument(id=uuid.uuid4(), **data)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    # ---- employee_addresses ----

    async def get_addresses(self, employee_id: uuid.UUID) -> list[EmployeeAddress]:
        stmt = select(EmployeeAddress).where(EmployeeAddress.employee_id == employee_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_address_by_type(
        self, employee_id: uuid.UUID, address_type: str
    ) -> EmployeeAddress | None:
        stmt = select(EmployeeAddress).where(
            EmployeeAddress.employee_id == employee_id,
            EmployeeAddress.address_type == address_type,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_address(
        self, employee_id: uuid.UUID, address_type: str, data: dict[str, Any]
    ) -> EmployeeAddress:
        row = await self.get_address_by_type(employee_id, address_type)
        if row is None:
            row = EmployeeAddress(
                id=uuid.uuid4(),
                employee_id=employee_id,
                address_type=address_type,
                **data,
            )
            self._session.add(row)
        else:
            for key, value in data.items():
                setattr(row, key, value)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    # ---- education_records ----

    async def get_education_records(self, employee_id: uuid.UUID) -> list[EducationRecord]:
        stmt = select(EducationRecord).where(EducationRecord.employee_id == employee_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add_education_record(self, data: dict[str, Any]) -> EducationRecord:
        row = EducationRecord(id=uuid.uuid4(), **data)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def update_education_record(
        self, record_id: uuid.UUID, data: dict[str, Any]
    ) -> EducationRecord:
        row = await self._session.get(EducationRecord, record_id)
        if row is None:
            raise NotFoundError(message=f"EducationRecord {record_id} not found")
        for key, value in data.items():
            setattr(row, key, value)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def delete_education_record(self, record_id: uuid.UUID) -> None:
        """Only deletes records with data_source='user'."""
        row = await self._session.get(EducationRecord, record_id)
        if row is None:
            raise NotFoundError(message=f"EducationRecord {record_id} not found")
        if row.data_source != "user":
            from app.core.exceptions import ForbiddenError
            raise ForbiddenError(
                message="Cannot delete records imported from 1C. Submit a change request instead."
            )
        await self._session.delete(row)
        await self._session.flush()

    # ---- family_members ----

    async def get_family_members(self, employee_id: uuid.UUID) -> list[FamilyMember]:
        stmt = select(FamilyMember).where(FamilyMember.employee_id == employee_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add_family_member(self, data: dict[str, Any]) -> FamilyMember:
        row = FamilyMember(id=uuid.uuid4(), **data)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def update_family_member(
        self, member_id: uuid.UUID, data: dict[str, Any]
    ) -> FamilyMember:
        row = await self._session.get(FamilyMember, member_id)
        if row is None:
            raise NotFoundError(message=f"FamilyMember {member_id} not found")
        for key, value in data.items():
            setattr(row, key, value)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def delete_family_member(self, member_id: uuid.UUID) -> None:
        row = await self._session.get(FamilyMember, member_id)
        if row is None:
            raise NotFoundError(message=f"FamilyMember {member_id} not found")
        await self._session.delete(row)
        await self._session.flush()

    # ---- emergency_contacts ----

    async def get_emergency_contacts(self, employee_id: uuid.UUID) -> list[EmergencyContact]:
        stmt = select(EmergencyContact).where(EmergencyContact.employee_id == employee_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_emergency_contact(self, employee_id: uuid.UUID) -> EmergencyContact | None:
        """Return primary (first) emergency contact."""
        rows = await self.get_emergency_contacts(employee_id)
        return rows[0] if rows else None

    async def upsert_emergency_contact(
        self, employee_id: uuid.UUID, data: dict[str, Any]
    ) -> EmergencyContact:
        existing = await self.get_emergency_contact(employee_id)
        if existing is None:
            existing = EmergencyContact(id=uuid.uuid4(), employee_id=employee_id, **data)
            self._session.add(existing)
        else:
            for key, value in data.items():
                setattr(existing, key, value)
        await self._session.flush()
        await self._session.refresh(existing)
        return existing

    # ---- employee_contacts ----

    async def get_employee_contact(self, employee_id: uuid.UUID) -> EmployeeContact | None:
        stmt = select(EmployeeContact).where(EmployeeContact.employee_id == employee_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_employee_contact(
        self, employee_id: uuid.UUID, data: dict[str, Any]
    ) -> EmployeeContact:
        row = await self.get_employee_contact(employee_id)
        if row is None:
            row = EmployeeContact(id=uuid.uuid4(), employee_id=employee_id, **data)
            self._session.add(row)
        else:
            for key, value in data.items():
                setattr(row, key, value)

        mobile_phone = data.get("mobile_phone")
        if mobile_phone:
            employee = await self._session.get(Employee, employee_id)
            if employee is not None:
                employee.phone = mobile_phone

        await self._session.flush()
        await self._session.refresh(row)
        return row

    # ---- social_info ----

    async def get_social_info(self, employee_id: uuid.UUID) -> SocialInfo | None:
        stmt = select(SocialInfo).where(SocialInfo.employee_id == employee_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_social_info(
        self, employee_id: uuid.UUID, data: dict[str, Any]
    ) -> SocialInfo:
        row = await self.get_social_info(employee_id)
        if row is None:
            row = SocialInfo(id=uuid.uuid4(), employee_id=employee_id, **data)
            self._session.add(row)
        else:
            for key, value in data.items():
                setattr(row, key, value)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    # ---- medical_certificates ----

    async def get_medical_certificates(
        self, employee_id: uuid.UUID
    ) -> list[MedicalCertificate]:
        stmt = select(MedicalCertificate).where(MedicalCertificate.employee_id == employee_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add_medical_certificate(self, data: dict[str, Any]) -> MedicalCertificate:
        row = MedicalCertificate(id=uuid.uuid4(), **data)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def delete_medical_certificate(
        self, cert_id: uuid.UUID, employee_id: uuid.UUID
    ) -> None:
        row = await self._session.get(MedicalCertificate, cert_id)
        if row is None or row.employee_id != employee_id:
            raise NotFoundError(message=f"MedicalCertificate {cert_id} not found")
        await self._session.delete(row)
        await self._session.flush()

    # ---- bank_accounts ----

    async def get_bank_accounts(self, employee_id: uuid.UUID) -> list[BankAccount]:
        stmt = select(BankAccount).where(BankAccount.employee_id == employee_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add_bank_account(self, data: dict[str, Any]) -> BankAccount:
        row = BankAccount(id=uuid.uuid4(), **data)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def delete_bank_account(
        self, account_id: uuid.UUID, employee_id: uuid.UUID
    ) -> None:
        row = await self._session.get(BankAccount, account_id)
        if row is None or row.employee_id != employee_id:
            raise NotFoundError(message=f"BankAccount {account_id} not found")
        await self._session.delete(row)
        await self._session.flush()


# ---------------------------------------------------------------------------
# ChangeRequestRepository
# ---------------------------------------------------------------------------


class ChangeRequestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: dict[str, Any]) -> PersonalDataChangeRequest:
        row = PersonalDataChangeRequest(id=uuid.uuid4(), **data)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row

    async def get(self, request_id: uuid.UUID) -> PersonalDataChangeRequest | None:
        return await self._session.get(PersonalDataChangeRequest, request_id)

    async def list_by_employee(
        self,
        employee_id: uuid.UUID,
        status: str | None = None,
    ) -> list[PersonalDataChangeRequest]:
        stmt = select(PersonalDataChangeRequest).where(
            PersonalDataChangeRequest.employee_id == employee_id
        )
        if status:
            stmt = stmt.where(PersonalDataChangeRequest.status == status)
        stmt = stmt.order_by(PersonalDataChangeRequest.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_for_hr(
        self,
        hr_email: str,
        status: str | None = None,
    ) -> list[PersonalDataChangeRequest]:
        stmt = select(PersonalDataChangeRequest).where(
            PersonalDataChangeRequest.hr_email == hr_email
        )
        if status:
            stmt = stmt.where(PersonalDataChangeRequest.status == status)
        stmt = stmt.order_by(PersonalDataChangeRequest.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(
        self,
        status: str | None = None,
    ) -> list[PersonalDataChangeRequest]:
        stmt = select(PersonalDataChangeRequest)
        if status:
            stmt = stmt.where(PersonalDataChangeRequest.status == status)
        stmt = stmt.order_by(PersonalDataChangeRequest.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        request_id: uuid.UUID,
        status: str,
        hr_comment: str | None = None,
        processed_at: datetime | None = None,
        hr_employee_id: uuid.UUID | None = None,
    ) -> PersonalDataChangeRequest:
        row = await self._session.get(PersonalDataChangeRequest, request_id)
        if row is None:
            raise NotFoundError(message=f"ChangeRequest {request_id} not found")
        row.status = status
        if hr_comment is not None:
            row.hr_comment = hr_comment
        if processed_at is not None:
            row.processed_at = processed_at
        if hr_employee_id is not None:
            row.hr_employee_id = hr_employee_id
        await self._session.flush()
        await self._session.refresh(row)
        return row
