"""Contacts section and UUID server defaults

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-18 16:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

_UUID_TABLES = [
    "users",
    "departments",
    "positions",
    "work_locations",
    "employees",
    "vacation_types",
    "vacation_balances",
    "vacation_requests",
    "sick_leaves",
    "timesheet_entries",
    "notifications",
    "refresh_tokens",
    "personal_data",
    "citizenship_records",
    "identity_documents",
    "employee_addresses",
    "education_records",
    "family_members",
    "emergency_contacts",
    "social_info",
    "medical_certificates",
    "bank_accounts",
    "personal_data_change_requests",
]


def upgrade() -> None:
    for table in _UUID_TABLES:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN id SET DEFAULT uuid_generate_v4()")

    op.create_table(
        "employee_contacts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("mobile_phone", sa.String(32), nullable=False),
        sa.Column("home_phone", sa.String(32), nullable=True),
        sa.Column("additional_phone", sa.String(32), nullable=True),
        sa.Column(
            "data_source",
            postgresql.ENUM("1c", "user", "hr_approved", name="data_source", create_type=False),
            nullable=False,
            server_default="user",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_employee_contacts_employee_id",
        "employee_contacts",
        ["employee_id"],
    )
    op.execute("""
        CREATE TRIGGER trg_employee_contacts_updated_at
        BEFORE UPDATE ON employee_contacts
        FOR EACH ROW EXECUTE PROCEDURE set_updated_at();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_employee_contacts_updated_at ON employee_contacts")
    op.drop_index("ix_employee_contacts_employee_id", table_name="employee_contacts")
    op.drop_table("employee_contacts")

    for table in _UUID_TABLES:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN id DROP DEFAULT")
