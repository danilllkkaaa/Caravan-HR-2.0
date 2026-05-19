from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.infrastructure.database import get_session_factory
from app.infrastructure.models import (
    BankAccount,
    CitizenshipRecord,
    Department,
    EducationRecord,
    EmergencyContact,
    Employee,
    EmployeeAddress,
    EmployeeContact,
    FamilyMember,
    Holiday,
    IdentityDocument,
    MedicalCertificate,
    Notification,
    PersonalData,
    PersonalDataChangeRequest,
    Position,
    SickLeave,
    SocialInfo,
    TimesheetEntry,
    User,
    VacationBalance,
    VacationRequest,
    VacationType,
    WorkLocation,
)

DEMO_PASSWORD = "TestPass123!"
DEMO_MARKER = "[DEMO]"


@dataclass(frozen=True)
class DemoEmployee:
    email: str
    role: str
    personnel_number: str
    external_id: str
    first_name: str
    last_name: str
    middle_name: str
    first_name_en: str
    last_name_en: str
    middle_name_en: str
    birth_date: date
    phone: str
    department: str
    position: str
    manager_email: str | None
    work_location: str
    gender: str
    marital_status: str
    nationality: str
    place_of_birth: str
    hire_date: date


DEPARTMENTS = {
    "hq": ("D-001", "Головной офис"),
    "hr": ("D-010", "HR департамент"),
    "operations": ("D-020", "Операционный департамент"),
    "finance": ("D-030", "Финансовый департамент"),
    "it": ("D-040", "IT департамент"),
}

POSITIONS = {
    "admin": ("P-001", "Администратор портала"),
    "hr_director": ("P-010", "HR директор"),
    "hr_partner": ("P-011", "HR бизнес-партнер"),
    "hr_specialist": ("P-012", "HR специалист"),
    "recruiter": ("P-013", "Специалист по подбору"),
    "operations_manager": ("P-020", "Руководитель операций"),
    "logistics": ("P-021", "Координатор логистики"),
    "warehouse": ("P-022", "Супервайзер склада"),
    "accountant": ("P-030", "Бухгалтер"),
    "engineer": ("P-040", "Инженер поддержки"),
}

WORK_LOCATIONS = {
    "almaty": ("WL-ALA", "Алматы, головной офис", "Алматы"),
    "astana": ("WL-AST", "Астана, филиал", "Астана"),
    "shymkent": ("WL-SHY", "Шымкент, склад", "Шымкент"),
}

EMPLOYEES = [
    DemoEmployee(
        email="admin@example.com",
        role="admin",
        personnel_number="ADM-0001",
        external_id="EMP-ADM-0001",
        first_name="Адиль",
        last_name="Оразбаев",
        middle_name="Серикович",
        first_name_en="Adil",
        last_name_en="Orazbayev",
        middle_name_en="Serikovich",
        birth_date=date(1985, 3, 14),
        phone="+7 701 000 0001",
        department="hq",
        position="admin",
        manager_email=None,
        work_location="almaty",
        gender="male",
        marital_status="married",
        nationality="Казах",
        place_of_birth="Казахстан, Алматы",
        hire_date=date(2020, 1, 10),
    ),
    DemoEmployee(
        email="manager@example.com",
        role="manager",
        personnel_number="OPS-1001",
        external_id="EMP-OPS-1001",
        first_name="Данияр",
        last_name="Смагулов",
        middle_name="Ерланович",
        first_name_en="Daniyar",
        last_name_en="Smagulov",
        middle_name_en="Erlanovich",
        birth_date=date(1988, 8, 21),
        phone="+7 701 000 1001",
        department="operations",
        position="operations_manager",
        manager_email="admin@example.com",
        work_location="almaty",
        gender="male",
        marital_status="married",
        nationality="Казах",
        place_of_birth="Казахстан, Караганда",
        hire_date=date(2021, 2, 1),
    ),
    DemoEmployee(
        email="employee@example.com",
        role="employee",
        personnel_number="OPS-2001",
        external_id="EMP-OPS-2001",
        first_name="Айдана",
        last_name="Сейдахметова",
        middle_name="Нурлановна",
        first_name_en="Aidana",
        last_name_en="Seidakhmetova",
        middle_name_en="Nurlanovna",
        birth_date=date(1994, 11, 3),
        phone="+7 701 000 2001",
        department="operations",
        position="logistics",
        manager_email="manager@example.com",
        work_location="almaty",
        gender="female",
        marital_status="married",
        nationality="Казашка",
        place_of_birth="Казахстан, Тараз",
        hire_date=date(2023, 5, 15),
    ),
    DemoEmployee(
        email="operator@example.com",
        role="employee",
        personnel_number="OPS-2002",
        external_id="EMP-OPS-2002",
        first_name="Руслан",
        last_name="Ким",
        middle_name="Александрович",
        first_name_en="Ruslan",
        last_name_en="Kim",
        middle_name_en="Alexandrovich",
        birth_date=date(1991, 7, 12),
        phone="+7 701 000 2002",
        department="operations",
        position="warehouse",
        manager_email="manager@example.com",
        work_location="shymkent",
        gender="male",
        marital_status="single",
        nationality="Кореец",
        place_of_birth="Казахстан, Шымкент",
        hire_date=date(2022, 9, 5),
    ),
    DemoEmployee(
        email="accountant@example.com",
        role="employee",
        personnel_number="FIN-3001",
        external_id="EMP-FIN-3001",
        first_name="Марина",
        last_name="Петрова",
        middle_name="Игоревна",
        first_name_en="Marina",
        last_name_en="Petrova",
        middle_name_en="Igorevna",
        birth_date=date(1989, 2, 6),
        phone="+7 701 000 3001",
        department="finance",
        position="accountant",
        manager_email="admin@example.com",
        work_location="astana",
        gender="female",
        marital_status="divorced",
        nationality="Русская",
        place_of_birth="Казахстан, Астана",
        hire_date=date(2021, 11, 22),
    ),
    DemoEmployee(
        email="hr@example.com",
        role="hr",
        personnel_number="HR-4001",
        external_id="EMP-HR-4001",
        first_name="Лаура",
        last_name="Нурпеисова",
        middle_name="Канатовна",
        first_name_en="Laura",
        last_name_en="Nurpeisova",
        middle_name_en="Kanatovna",
        birth_date=date(1990, 6, 17),
        phone="+7 701 000 4001",
        department="hr",
        position="hr_partner",
        manager_email="hr.manager@example.com",
        work_location="almaty",
        gender="female",
        marital_status="married",
        nationality="Казашка",
        place_of_birth="Казахстан, Алматы",
        hire_date=date(2022, 4, 4),
    ),
    DemoEmployee(
        email="hr.manager@example.com",
        role="hr",
        personnel_number="HR-4000",
        external_id="EMP-HR-4000",
        first_name="Гульмира",
        last_name="Абдрахманова",
        middle_name="Талгатовна",
        first_name_en="Gulmira",
        last_name_en="Abdrakhmanova",
        middle_name_en="Talgatovna",
        birth_date=date(1984, 12, 9),
        phone="+7 701 000 4000",
        department="hr",
        position="hr_director",
        manager_email="admin@example.com",
        work_location="almaty",
        gender="female",
        marital_status="married",
        nationality="Казашка",
        place_of_birth="Казахстан, Костанай",
        hire_date=date(2019, 3, 1),
    ),
    DemoEmployee(
        email="hr.specialist@example.com",
        role="hr",
        personnel_number="HR-4002",
        external_id="EMP-HR-4002",
        first_name="Асем",
        last_name="Бекенова",
        middle_name="Муратовна",
        first_name_en="Asem",
        last_name_en="Bekenova",
        middle_name_en="Muratovna",
        birth_date=date(1996, 1, 28),
        phone="+7 701 000 4002",
        department="hr",
        position="hr_specialist",
        manager_email="hr.manager@example.com",
        work_location="astana",
        gender="female",
        marital_status="single",
        nationality="Казашка",
        place_of_birth="Казахстан, Павлодар",
        hire_date=date(2024, 1, 15),
    ),
    DemoEmployee(
        email="recruiter@example.com",
        role="hr",
        personnel_number="HR-4003",
        external_id="EMP-HR-4003",
        first_name="Никита",
        last_name="Волков",
        middle_name="Андреевич",
        first_name_en="Nikita",
        last_name_en="Volkov",
        middle_name_en="Andreevich",
        birth_date=date(1993, 4, 2),
        phone="+7 701 000 4003",
        department="hr",
        position="recruiter",
        manager_email="hr.manager@example.com",
        work_location="shymkent",
        gender="male",
        marital_status="single",
        nationality="Русский",
        place_of_birth="Казахстан, Усть-Каменогорск",
        hire_date=date(2023, 8, 7),
    ),
    DemoEmployee(
        email="it.support@example.com",
        role="employee",
        personnel_number="IT-5001",
        external_id="EMP-IT-5001",
        first_name="Ермек",
        last_name="Ахметов",
        middle_name="Болатович",
        first_name_en="Yermek",
        last_name_en="Akhmetov",
        middle_name_en="Bolatovich",
        birth_date=date(1992, 10, 19),
        phone="+7 701 000 5001",
        department="it",
        position="engineer",
        manager_email="admin@example.com",
        work_location="almaty",
        gender="male",
        marital_status="married",
        nationality="Казах",
        place_of_birth="Казахстан, Алматы",
        hire_date=date(2020, 10, 12),
    ),
]


async def _one(session: AsyncSession, stmt: Any) -> Any | None:
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def _get_or_create_department(session: AsyncSession, key: str) -> Department:
    external_id, name = DEPARTMENTS[key]
    row = await _one(
        session, select(Department).where(Department.external_id_1c == external_id)
    )
    if row is None:
        row = Department(external_id_1c=external_id, name=name)
        session.add(row)
        await session.flush()
    else:
        row.name = name
    return row


async def _get_or_create_position(session: AsyncSession, key: str) -> Position:
    external_id, name = POSITIONS[key]
    row = await _one(session, select(Position).where(Position.external_id_1c == external_id))
    if row is None:
        row = Position(external_id_1c=external_id, name=name)
        session.add(row)
        await session.flush()
    else:
        row.name = name
    return row


async def _get_or_create_work_location(session: AsyncSession, key: str) -> WorkLocation:
    external_id, name, city = WORK_LOCATIONS[key]
    row = await _one(
        session, select(WorkLocation).where(WorkLocation.external_id_1c == external_id)
    )
    if row is None:
        row = WorkLocation(external_id_1c=external_id, name=name, city=city)
        session.add(row)
        await session.flush()
    else:
        row.name = name
        row.city = city
    return row


async def _upsert_user(session: AsyncSession, email: str) -> User:
    row = await _one(session, select(User).where(User.email == email))
    password_hash = hash_password(DEMO_PASSWORD)
    if row is None:
        row = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=password_hash,
            is_active=True,
            failed_login_attempts=0,
            locked_until=None,
        )
        session.add(row)
        await session.flush()
    else:
        row.password_hash = password_hash
        row.is_active = True
        row.failed_login_attempts = 0
        row.locked_until = None
    return row


async def _upsert_employee(
    session: AsyncSession,
    demo: DemoEmployee,
    departments: dict[str, Department],
    positions: dict[str, Position],
    locations: dict[str, WorkLocation],
) -> Employee:
    user = await _upsert_user(session, demo.email)
    row = await _one(session, select(Employee).where(Employee.user_id == user.id))
    attrs = {
        "external_id_1c": demo.external_id,
        "personnel_number": demo.personnel_number,
        "first_name": demo.first_name,
        "last_name": demo.last_name,
        "middle_name": demo.middle_name,
        "birth_date": demo.birth_date,
        "phone": demo.phone,
        "department_id": departments[demo.department].id,
        "position_id": positions[demo.position].id,
        "role": demo.role,
        "hire_date": demo.hire_date,
        "work_location_id": locations[demo.work_location].id,
        "avatar_url": f"https://api.dicebear.com/9.x/initials/svg?seed={demo.first_name}%20{demo.last_name}",
        "sync_hash": f"demo:{demo.external_id}",
    }
    if row is None:
        row = Employee(id=uuid.uuid4(), user_id=user.id, **attrs)
        session.add(row)
        await session.flush()
    else:
        for key, value in attrs.items():
            setattr(row, key, value)
    return row


async def _upsert_one_to_one(
    session: AsyncSession,
    model: type[Any],
    employee_id: uuid.UUID,
    data: dict[str, Any],
) -> Any:
    row = await _one(session, select(model).where(model.employee_id == employee_id))
    if row is None:
        row = model(id=uuid.uuid4(), employee_id=employee_id, **data)
        session.add(row)
        await session.flush()
    else:
        for key, value in data.items():
            setattr(row, key, value)
    return row


async def _upsert_address(
    session: AsyncSession,
    employee_id: uuid.UUID,
    address_type: str,
    data: dict[str, Any],
) -> EmployeeAddress:
    row = await _one(
        session,
        select(EmployeeAddress).where(
            EmployeeAddress.employee_id == employee_id,
            EmployeeAddress.address_type == address_type,
        ),
    )
    if row is None:
        row = EmployeeAddress(
            id=uuid.uuid4(), employee_id=employee_id, address_type=address_type, **data
        )
        session.add(row)
        await session.flush()
    else:
        for key, value in data.items():
            setattr(row, key, value)
    return row


async def _upsert_vacation_type(
    session: AsyncSession,
    code: str,
    name: str,
    is_paid: bool,
    requires_documents: bool = False,
) -> VacationType:
    row = await _one(session, select(VacationType).where(VacationType.code == code))
    if row is None:
        row = VacationType(
            id=uuid.uuid4(),
            code=code,
            name=name,
            is_paid=is_paid,
            requires_documents=requires_documents,
        )
        session.add(row)
        await session.flush()
    else:
        row.name = name
        row.is_paid = is_paid
        row.requires_documents = requires_documents
    return row


async def _upsert_balance(
    session: AsyncSession,
    employee_id: uuid.UUID,
    year: int,
    total_days: Decimal,
    used_days: Decimal,
) -> None:
    row = await _one(
        session,
        select(VacationBalance).where(
            VacationBalance.employee_id == employee_id,
            VacationBalance.year == year,
        ),
    )
    data = {
        "total_days": total_days,
        "used_days": used_days,
        "sync_source": "manual",
    }
    if row is None:
        row = VacationBalance(id=uuid.uuid4(), employee_id=employee_id, year=year, **data)
        session.add(row)
    else:
        for key, value in data.items():
            setattr(row, key, value)


async def _reset_demo_rows(session: AsyncSession, employees: dict[str, Employee]) -> None:
    employee_ids = [employee.id for employee in employees.values()]
    for model, predicate in (
        (Notification, Notification.payload["demo_seed"].as_string() == "true"),
        (VacationRequest, VacationRequest.comment.like(f"{DEMO_MARKER}%")),
        (SickLeave, SickLeave.open_comment.like(f"{DEMO_MARKER}%")),
        (PersonalDataChangeRequest, PersonalDataChangeRequest.comment.like(f"{DEMO_MARKER}%")),
    ):
        await session.execute(
            delete(model).where(model.employee_id.in_(employee_ids)).where(predicate)
        )

    await session.execute(delete(TimesheetEntry).where(TimesheetEntry.employee_id.in_(employee_ids)))
    await session.execute(
        delete(Holiday).where(
            Holiday.date.in_(
                [
                    date(2026, 1, 1),
                    date(2026, 3, 21),
                    date(2026, 3, 22),
                    date(2026, 5, 9),
                    date(2026, 12, 16),
                ]
            )
        )
    )


async def _seed_personal_sections(
    session: AsyncSession,
    demo: DemoEmployee,
    employee: Employee,
    email: str,
) -> None:
    await _upsert_one_to_one(
        session,
        PersonalData,
        employee.id,
        {
            "first_name_en": demo.first_name_en,
            "last_name_en": demo.last_name_en,
            "middle_name_en": demo.middle_name_en,
            "gender": demo.gender,
            "nationality": demo.nationality,
            "place_of_birth": demo.place_of_birth,
            "marital_status": demo.marital_status,
            "data_source": "hr_approved",
            "sync_hash": f"demo:{employee.external_id_1c}",
            "last_synced_at_1c": datetime(2026, 5, 19, 8, 0, tzinfo=UTC),
        },
    )
    await _upsert_one_to_one(
        session,
        EmployeeContact,
        employee.id,
        {
            "email": email,
            "mobile_phone": demo.phone,
            "home_phone": "+7 727 000 00 00",
            "additional_phone": "+7 701 999 99 99",
            "data_source": "hr_approved",
        },
    )
    await _upsert_one_to_one(
        session,
        SocialInfo,
        employee.id,
        {
            "pension_status": "ОПВ перечисляется",
            "has_disability": False,
            "disability_group": None,
            "is_ww2_veteran": False,
            "is_ww2_family": False,
            "document_url": f"demo/social/{employee.personnel_number}.pdf",
            "data_source": "hr_approved",
        },
    )

    city = "Алматы" if demo.work_location == "almaty" else "Астана"
    await _upsert_address(
        session,
        employee.id,
        "registration",
        {
            "country": "Казахстан",
            "region": "Алматинская область",
            "city": city,
            "street": "проспект Абая",
            "house": "15",
            "apartment": "24",
            "data_source": "hr_approved",
        },
    )
    await _upsert_address(
        session,
        employee.id,
        "residence",
        {
            "country": "Казахстан",
            "region": "Алматинская область",
            "city": city,
            "street": "улица Толе би",
            "house": "88",
            "apartment": "12",
            "data_source": "user",
        },
    )

    await _delete_employee_rows(
        session,
        employee.id,
        [
            CitizenshipRecord,
            IdentityDocument,
            EducationRecord,
            FamilyMember,
            EmergencyContact,
            MedicalCertificate,
            BankAccount,
        ],
    )
    session.add(
        CitizenshipRecord(
            id=uuid.uuid4(),
            employee_id=employee.id,
            citizenship_country="Казахстан",
            status="rk_citizen",
            iin_in_country=f"9{employee.personnel_number[-4:]}0000001",
            is_primary=True,
            data_source="hr_approved",
        )
    )
    session.add(
        IdentityDocument(
            id=uuid.uuid4(),
            employee_id=employee.id,
            document_type="national_id",
            series="KZ",
            number=f"{employee.personnel_number.replace('-', '')}ID",
            issued_by="МВД Республики Казахстан",
            issue_date=date(2021, 1, 20),
            expiry_date=date(2031, 1, 20),
            document_url=f"demo/documents/{employee.personnel_number}-id.pdf",
            is_active=True,
            data_source="hr_approved",
            external_id_1c=f"DOC-{employee.personnel_number}",
        )
    )
    session.add_all(
        [
            EducationRecord(
                id=uuid.uuid4(),
                employee_id=employee.id,
                education_type="higher",
                institution_name="Казахский национальный университет им. аль-Фараби",
                specialty="Менеджмент",
                qualification="Бакалавр",
                graduation_date=date(2016, 6, 30),
                document_number=f"EDU-{employee.personnel_number}",
                document_url=f"demo/education/{employee.personnel_number}-diploma.pdf",
                data_source="hr_approved",
                external_id_1c=f"EDU-{employee.personnel_number}-1",
            ),
            EducationRecord(
                id=uuid.uuid4(),
                employee_id=employee.id,
                education_type="advanced_qualification",
                institution_name="Caravan Resources Academy",
                specialty="Корпоративные процессы и безопасность",
                qualification="Сертификат",
                graduation_date=date(2025, 11, 12),
                document_number=f"CRT-{employee.personnel_number}",
                document_url=f"demo/education/{employee.personnel_number}-cert.pdf",
                data_source="user",
                external_id_1c=f"EDU-{employee.personnel_number}-2",
            ),
        ]
    )
    if demo.marital_status == "married":
        session.add(
            FamilyMember(
                id=uuid.uuid4(),
                employee_id=employee.id,
                member_type="spouse",
                first_name="Самат" if demo.gender == "female" else "Алия",
                last_name=demo.last_name,
                middle_name="Ермекович" if demo.gender == "female" else "Муратовна",
                birth_date=date(1990, 5, 11),
                iin_encrypted="demo-encrypted-iin",
                spouse_status="active",
                marriage_cert_number=f"MC-{employee.personnel_number}",
                marriage_cert_issue_date=date(2018, 9, 14),
                marriage_cert_org="РАГС г. Алматы",
                document_url=f"demo/family/{employee.personnel_number}-marriage.pdf",
                data_source="hr_approved",
                external_id_1c=f"FAM-{employee.personnel_number}-S",
            )
        )
        session.add(
            FamilyMember(
                id=uuid.uuid4(),
                employee_id=employee.id,
                member_type="child",
                first_name="Амина",
                last_name=demo.last_name,
                middle_name="",
                birth_date=date(2019, 4, 8),
                iin_encrypted="demo-encrypted-child-iin",
                birth_cert_number=f"BC-{employee.personnel_number}",
                birth_cert_series="KZ",
                birth_cert_issue_date=date(2019, 4, 15),
                birth_cert_issued_by="РАГС г. Алматы",
                document_url=f"demo/family/{employee.personnel_number}-child.pdf",
                data_source="user",
                external_id_1c=f"FAM-{employee.personnel_number}-C",
            )
        )
    session.add(
        EmergencyContact(
            id=uuid.uuid4(),
            employee_id=employee.id,
            full_name="Серик Нурланов",
            phone="+7 701 555 55 55",
            address="Казахстан, Алматы, ул. Кабанбай батыра 10",
            relationship="Близкий родственник",
        )
    )
    session.add_all(
        [
            MedicalCertificate(
                id=uuid.uuid4(),
                employee_id=employee.id,
                cert_type="narco_dispensary",
                cert_number=f"ND-{employee.personnel_number}",
                issue_date=date(2026, 1, 12),
                expiry_date=date(2027, 1, 12),
                document_url=f"demo/medical/{employee.personnel_number}-narco.pdf",
            ),
            MedicalCertificate(
                id=uuid.uuid4(),
                employee_id=employee.id,
                cert_type="form_075",
                cert_number=f"075-{employee.personnel_number}",
                issue_date=date(2026, 2, 1),
                expiry_date=date(2027, 2, 1),
                document_url=f"demo/medical/{employee.personnel_number}-075.pdf",
            ),
        ]
    )
    session.add(
        BankAccount(
            id=uuid.uuid4(),
            employee_id=employee.id,
            bank_name="Kaspi Bank",
            account_number_encrypted="demo-encrypted-account-number",
            bik="CASPKZKA",
            account_type="standard",
            holder_name=f"{demo.last_name} {demo.first_name} {demo.middle_name}",
            document_url=f"demo/bank/{employee.personnel_number}-iban.pdf",
            is_primary=True,
            data_source="hr_approved",
            external_id_1c=f"BANK-{employee.personnel_number}",
        )
    )


async def _delete_employee_rows(
    session: AsyncSession,
    employee_id: uuid.UUID,
    models: list[type[Any]],
) -> None:
    for model in models:
        await session.execute(delete(model).where(model.employee_id == employee_id))


async def _seed_vacations(
    session: AsyncSession,
    employees: dict[str, Employee],
    vacation_types: dict[str, VacationType],
) -> None:
    year = 2026
    used_by_email = {
        "employee@example.com": Decimal("5.00"),
        "operator@example.com": Decimal("2.00"),
        "accountant@example.com": Decimal("7.00"),
    }
    for email, employee in employees.items():
        await _upsert_balance(
            session,
            employee.id,
            year,
            Decimal("24.00"),
            used_by_email.get(email, Decimal("0.00")),
        )

    manager = employees["manager@example.com"]
    admin = employees["admin@example.com"]
    paid = vacation_types["annual"]
    unpaid = vacation_types["unpaid"]
    session.add_all(
        [
            VacationRequest(
                id=uuid.uuid4(),
                employee_id=employees["employee@example.com"].id,
                vacation_type_id=paid.id,
                start_date=date(2026, 6, 8),
                end_date=date(2026, 6, 12),
                days_count=5,
                comment=f"{DEMO_MARKER} Семейная поездка, нужна заявка на согласование.",
                status="pending",
                approver_id=manager.id,
            ),
            VacationRequest(
                id=uuid.uuid4(),
                employee_id=employees["operator@example.com"].id,
                vacation_type_id=paid.id,
                start_date=date(2026, 6, 15),
                end_date=date(2026, 6, 19),
                days_count=5,
                comment=f"{DEMO_MARKER} Плановый отпуск сотрудника склада.",
                status="pending",
                approver_id=manager.id,
            ),
            VacationRequest(
                id=uuid.uuid4(),
                employee_id=employees["employee@example.com"].id,
                vacation_type_id=paid.id,
                start_date=date(2026, 4, 6),
                end_date=date(2026, 4, 10),
                days_count=5,
                comment=f"{DEMO_MARKER} Уже согласованный отпуск для истории.",
                status="approved",
                approver_id=manager.id,
                approver_comment="Согласовано, график закрыт.",
                approved_at=datetime(2026, 3, 20, 10, 0, tzinfo=UTC),
            ),
            VacationRequest(
                id=uuid.uuid4(),
                employee_id=employees["accountant@example.com"].id,
                vacation_type_id=unpaid.id,
                start_date=date(2026, 7, 20),
                end_date=date(2026, 7, 22),
                days_count=3,
                comment=f"{DEMO_MARKER} Пример отклоненной заявки.",
                status="rejected",
                approver_id=admin.id,
                approver_comment="Период совпадает с закрытием месяца.",
                approved_at=datetime(2026, 5, 10, 11, 30, tzinfo=UTC),
            ),
        ]
    )


async def _seed_sick_leaves(session: AsyncSession, employees: dict[str, Employee]) -> None:
    hr = employees["hr@example.com"]
    session.add_all(
        [
            SickLeave(
                id=uuid.uuid4(),
                employee_id=employees["employee@example.com"].id,
                start_date=date(2026, 5, 17),
                end_date=None,
                open_comment=f"{DEMO_MARKER} Открытый больничный, документ будет прикреплен позже.",
                close_comment=None,
                document_url="demo/sick-leaves/open-placeholder.pdf",
                status="open",
            ),
            SickLeave(
                id=uuid.uuid4(),
                employee_id=employees["operator@example.com"].id,
                start_date=date(2026, 4, 22),
                end_date=date(2026, 4, 25),
                open_comment=f"{DEMO_MARKER} ОРВИ, обращение в поликлинику.",
                close_comment="Закрыт по справке врача.",
                document_url="demo/sick-leaves/operator-april.pdf",
                status="closed",
                closed_by=hr.id,
            ),
        ]
    )


async def _seed_notifications(session: AsyncSession, employees: dict[str, Employee]) -> None:
    now = datetime.now(UTC)
    data = [
        (
            "employee@example.com",
            "info",
            "Профиль сотрудника заполнен",
            "Демо-данные по личному профилю готовы для просмотра.",
            None,
            now - timedelta(hours=3),
        ),
        (
            "employee@example.com",
            "reminder",
            "Ожидается согласование отпуска",
            "Заявка на отпуск с 08.06.2026 отправлена руководителю.",
            None,
            now - timedelta(hours=2),
        ),
        (
            "manager@example.com",
            "reminder",
            "Новые заявки на отпуск",
            "Две заявки сотрудников ожидают вашего согласования.",
            None,
            now - timedelta(hours=1, minutes=20),
        ),
        (
            "hr@example.com",
            "info",
            "Новая заявка на изменение данных",
            "Сотрудник отправил изменение контактного телефона.",
            None,
            now - timedelta(minutes=55),
        ),
        (
            "hr.manager@example.com",
            "info",
            "HR очередь готова к демонстрации",
            "В очереди есть отправленные, согласованные и отклоненные заявки.",
            None,
            now - timedelta(minutes=40),
        ),
        (
            "admin@example.com",
            "sharepoint_link",
            "Документы синхронизированы",
            "Демо-ссылки на документы доступны в профилях сотрудников.",
            now - timedelta(minutes=15),
            now - timedelta(minutes=30),
        ),
    ]
    for email, type_, title, body, read_at, created_at in data:
        session.add(
            Notification(
                id=uuid.uuid4(),
                employee_id=employees[email].id,
                type=type_,
                title=title,
                body=body,
                payload={"demo_seed": "true"},
                read_at=read_at,
                created_at=created_at,
            )
        )


async def _seed_change_requests(session: AsyncSession, employees: dict[str, Employee]) -> None:
    employee = employees["employee@example.com"]
    operator = employees["operator@example.com"]
    hr = employees["hr@example.com"]
    hr_manager = employees["hr.manager@example.com"]
    session.add_all(
        [
            PersonalDataChangeRequest(
                id=uuid.uuid4(),
                employee_id=employee.id,
                section="emergency_contact",
                field_name="phone",
                old_value={"value": "+7 701 555 55 55"},
                new_value={"phone": "+7 701 777 77 77"},
                comment=f"{DEMO_MARKER} Сотрудник просит обновить номер экстренного контакта.",
                document_url=None,
                hr_employee_id=None,
                hr_email="hr@example.com",
                status="sent",
            ),
            PersonalDataChangeRequest(
                id=uuid.uuid4(),
                employee_id=operator.id,
                section="address",
                field_name="residence",
                old_value={"city": "Шымкент", "street": "ул. Байтурсынова"},
                new_value={
                    "address_type": "residence",
                    "country": "Казахстан",
                    "region": "Алматинская область",
                    "city": "Алматы",
                    "street": "ул. Наурызбай батыра",
                    "house": "45",
                    "apartment": "9",
                },
                comment=f"{DEMO_MARKER} Переезд сотрудника в Алматы.",
                document_url="demo/change-requests/address-proof.pdf",
                hr_employee_id=hr.id,
                hr_email="hr@example.com",
                status="under_review",
            ),
            PersonalDataChangeRequest(
                id=uuid.uuid4(),
                employee_id=employees["accountant@example.com"].id,
                section="basic_data",
                field_name="nationality",
                old_value={"value": "Русская"},
                new_value={"value": "Русская"},
                comment=f"{DEMO_MARKER} Пример уже согласованной заявки.",
                document_url=None,
                hr_employee_id=hr_manager.id,
                hr_email="hr.manager@example.com",
                status="approved",
                hr_comment="Данные подтверждены.",
                processed_at=datetime(2026, 5, 12, 9, 45, tzinfo=UTC),
            ),
            PersonalDataChangeRequest(
                id=uuid.uuid4(),
                employee_id=employees["it.support@example.com"].id,
                section="document",
                field_name="document_url",
                old_value=None,
                new_value={"document_url": "demo/documents/new-id.pdf"},
                comment=f"{DEMO_MARKER} Пример отклоненной заявки из-за нечитабельного файла.",
                document_url="demo/documents/bad-scan.pdf",
                hr_employee_id=hr_manager.id,
                hr_email="hr.manager@example.com",
                status="rejected",
                hr_comment="Загрузите скан лучшего качества.",
                processed_at=datetime(2026, 5, 13, 15, 10, tzinfo=UTC),
            ),
        ]
    )


async def _seed_timesheets(session: AsyncSession, employees: dict[str, Employee]) -> None:
    base_day = date(2026, 5, 19)
    statuses = ["work", "work", "partial", "work", "work", "weekend", "weekend", "work"]
    for employee in employees.values():
        for index, status in enumerate(statuses):
            day = base_day - timedelta(days=index)
            if status == "weekend":
                worked = 0
                first_entry = None
                last_exit = None
                schedule = 0
            elif status == "partial":
                worked = 300
                first_entry = datetime.combine(day, time(9, 15), UTC)
                last_exit = datetime.combine(day, time(14, 30), UTC)
                schedule = 480
            else:
                worked = 480
                first_entry = datetime.combine(day, time(8, 55), UTC)
                last_exit = datetime.combine(day, time(18, 5), UTC)
                schedule = 480
            session.add(
                TimesheetEntry(
                    id=uuid.uuid4(),
                    employee_id=employee.id,
                    date=day,
                    first_entry_at=first_entry,
                    last_exit_at=last_exit,
                    worked_minutes=worked,
                    status=status,
                    schedule_minutes=schedule,
                )
            )


async def _seed_holidays(session: AsyncSession) -> None:
    session.add_all(
        [
            Holiday(date=date(2026, 1, 1), name="Новый год", country_code="KZ"),
            Holiday(date=date(2026, 3, 21), name="Наурыз мейрамы", country_code="KZ"),
            Holiday(date=date(2026, 3, 22), name="Наурыз мейрамы", country_code="KZ"),
            Holiday(date=date(2026, 5, 9), name="День Победы", country_code="KZ"),
            Holiday(date=date(2026, 12, 16), name="День Независимости", country_code="KZ"),
        ]
    )


async def seed_demo() -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        departments = {
            key: await _get_or_create_department(session, key) for key in DEPARTMENTS
        }
        positions = {key: await _get_or_create_position(session, key) for key in POSITIONS}
        locations = {
            key: await _get_or_create_work_location(session, key) for key in WORK_LOCATIONS
        }
        await session.flush()

        employees: dict[str, Employee] = {}
        for demo in EMPLOYEES:
            employees[demo.email] = await _upsert_employee(
                session, demo, departments, positions, locations
            )
        await session.flush()

        for demo in EMPLOYEES:
            employee = employees[demo.email]
            employee.manager_id = (
                employees[demo.manager_email].id if demo.manager_email is not None else None
            )

        departments["hr"].head_id = employees["hr.manager@example.com"].id
        departments["operations"].head_id = employees["manager@example.com"].id
        departments["finance"].head_id = employees["accountant@example.com"].id
        departments["it"].head_id = employees["it.support@example.com"].id
        departments["hq"].head_id = employees["admin@example.com"].id
        locations["almaty"].hr_employee_id = employees["hr@example.com"].id
        locations["astana"].hr_employee_id = employees["hr.specialist@example.com"].id
        locations["shymkent"].hr_employee_id = employees["recruiter@example.com"].id

        await _reset_demo_rows(session, employees)

        for demo in EMPLOYEES:
            await _seed_personal_sections(session, demo, employees[demo.email], demo.email)

        vacation_types = {
            "annual": await _upsert_vacation_type(
                session, "annual_paid", "Ежегодный оплачиваемый отпуск", True
            ),
            "unpaid": await _upsert_vacation_type(
                session, "unpaid", "Отпуск без сохранения заработной платы", False
            ),
            "study": await _upsert_vacation_type(
                session, "study", "Учебный отпуск", True, requires_documents=True
            ),
            "maternity": await _upsert_vacation_type(
                session, "maternity", "Отпуск по беременности и родам", True, True
            ),
        }
        await _seed_vacations(session, employees, vacation_types)
        await _seed_sick_leaves(session, employees)
        await _seed_notifications(session, employees)
        await _seed_change_requests(session, employees)
        await _seed_timesheets(session, employees)
        await _seed_holidays(session)

        await session.commit()

    print("Demo seed completed.")
    print(f"Password for all demo accounts: {DEMO_PASSWORD}")
    for demo in EMPLOYEES:
        print(f"{demo.email} ({demo.role})")


def main() -> None:
    asyncio.run(seed_demo())


if __name__ == "__main__":
    main()
