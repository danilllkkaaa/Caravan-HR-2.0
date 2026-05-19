"""Personal data module - all tables, enums, indexes, triggers

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-18 14:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NEW_TABLES = [
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

_NEW_ENUMS = [
    "data_source",
    "gender_type",
    "citizenship_status",
    "identity_doc_type",
    "address_type",
    "education_type",
    "family_member_type",
    "marital_status",
    "medical_cert_type",
    "bank_account_type",
    "change_request_status",
    "change_request_section",
]


def _create_updated_at_trigger(table_name: str) -> None:
    """Create set_updated_at trigger on the given table."""
    op.execute(f"""
        CREATE TRIGGER trg_{table_name}_updated_at
        BEFORE UPDATE ON {table_name}
        FOR EACH ROW EXECUTE PROCEDURE set_updated_at();
    """)


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Shared trigger function (idempotent)
    # ------------------------------------------------------------------
    op.execute("""
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # ------------------------------------------------------------------
    # ENUMs
    # ------------------------------------------------------------------
    op.execute("CREATE TYPE data_source AS ENUM ('1c', 'user', 'hr_approved')")
    op.execute("CREATE TYPE gender_type AS ENUM ('male', 'female')")
    op.execute(
        "CREATE TYPE citizenship_status AS ENUM ('rk_citizen', 'foreign_citizen', 'stateless')"
    )
    op.execute(
        "CREATE TYPE identity_doc_type AS ENUM ('national_id', 'passport', 'residence_permit', 'other')"
    )
    op.execute("CREATE TYPE address_type AS ENUM ('registration', 'residence')")
    op.execute(
        "CREATE TYPE education_type AS ENUM ('higher', 'secondary', 'technical', 'advanced_qualification', 'other')"
    )
    op.execute(
        "CREATE TYPE family_member_type AS ENUM ('child', 'spouse', 'ex_spouse')"
    )
    op.execute(
        "CREATE TYPE marital_status AS ENUM ('single', 'married', 'divorced', 'widowed')"
    )
    op.execute(
        "CREATE TYPE medical_cert_type AS ENUM ('narco_dispensary', 'psycho_dispensary', 'form_075')"
    )
    op.execute(
        "CREATE TYPE bank_account_type AS ENUM ('standard', 'social', 'other')"
    )
    op.execute(
        "CREATE TYPE change_request_status AS ENUM ('sent', 'under_review', 'approved', 'rejected')"
    )
    op.execute(
        "CREATE TYPE change_request_section AS ENUM "
        "('basic_data', 'citizenship', 'document', 'address', 'education', 'family', "
        "'emergency_contact', 'social_info', 'medical', 'bank', 'other')"
    )

    # ------------------------------------------------------------------
    # personal_data  (1:1 with employees)
    # ------------------------------------------------------------------
    op.create_table(
        "personal_data",
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
        sa.Column("first_name_en", sa.String(100), nullable=True),
        sa.Column("last_name_en", sa.String(100), nullable=True),
        sa.Column("middle_name_en", sa.String(100), nullable=True),
        sa.Column(
            "gender",
            postgresql.ENUM("male", "female", name="gender_type", create_type=False),
            nullable=True,
        ),
        sa.Column("nationality", sa.String(100), nullable=True),
        sa.Column("place_of_birth", sa.String(255), nullable=True),
        sa.Column(
            "marital_status",
            postgresql.ENUM(
                "single", "married", "divorced", "widowed",
                name="marital_status", create_type=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "data_source",
            postgresql.ENUM("1c", "user", "hr_approved", name="data_source", create_type=False),
            nullable=False,
            server_default="1c",
        ),
        sa.Column("sync_hash", sa.String(64), nullable=True),
        sa.Column("1c_last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_personal_data_employee_id", "personal_data", ["employee_id"])
    _create_updated_at_trigger("personal_data")

    # ------------------------------------------------------------------
    # citizenship_records
    # ------------------------------------------------------------------
    op.create_table(
        "citizenship_records",
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
        ),
        sa.Column("citizenship_country", sa.String(100), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "rk_citizen", "foreign_citizen", "stateless",
                name="citizenship_status", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("iin_in_country", sa.String(20), nullable=True),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column(
            "data_source",
            postgresql.ENUM("1c", "user", "hr_approved", name="data_source", create_type=False),
            nullable=False,
            server_default="1c",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_citizenship_records_employee_id", "citizenship_records", ["employee_id"])
    _create_updated_at_trigger("citizenship_records")

    # ------------------------------------------------------------------
    # identity_documents
    # ------------------------------------------------------------------
    op.create_table(
        "identity_documents",
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
        ),
        sa.Column(
            "document_type",
            postgresql.ENUM(
                "national_id", "passport", "residence_permit", "other",
                name="identity_doc_type", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("series", sa.String(20), nullable=True),
        sa.Column("number", sa.String(50), nullable=False),
        sa.Column("issued_by", sa.String(255), nullable=False),
        sa.Column("issue_date", sa.Date, nullable=False),
        sa.Column("expiry_date", sa.Date, nullable=True),
        sa.Column("document_url", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column(
            "data_source",
            postgresql.ENUM("1c", "user", "hr_approved", name="data_source", create_type=False),
            nullable=False,
            server_default="1c",
        ),
        sa.Column("external_id_1c", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_identity_documents_employee_id", "identity_documents", ["employee_id"])
    _create_updated_at_trigger("identity_documents")

    # ------------------------------------------------------------------
    # employee_addresses
    # ------------------------------------------------------------------
    op.create_table(
        "employee_addresses",
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
        ),
        sa.Column(
            "address_type",
            postgresql.ENUM("registration", "residence", name="address_type", create_type=False),
            nullable=False,
        ),
        sa.Column("country", sa.String(100), nullable=False),
        sa.Column("region", sa.String(100), nullable=True),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("street", sa.String(255), nullable=True),
        sa.Column("house", sa.String(20), nullable=True),
        sa.Column("apartment", sa.String(20), nullable=True),
        sa.Column(
            "data_source",
            postgresql.ENUM("1c", "user", "hr_approved", name="data_source", create_type=False),
            nullable=False,
            server_default="1c",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("employee_id", "address_type", name="uq_employee_addresses_emp_type"),
    )
    op.create_index("ix_employee_addresses_employee_id", "employee_addresses", ["employee_id"])
    _create_updated_at_trigger("employee_addresses")

    # ------------------------------------------------------------------
    # education_records
    # ------------------------------------------------------------------
    op.create_table(
        "education_records",
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
        ),
        sa.Column(
            "education_type",
            postgresql.ENUM(
                "higher", "secondary", "technical", "advanced_qualification", "other",
                name="education_type", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("institution_name", sa.String(255), nullable=False),
        sa.Column("specialty", sa.String(255), nullable=True),
        sa.Column("qualification", sa.String(255), nullable=True),
        sa.Column("graduation_date", sa.Date, nullable=True),
        sa.Column("document_number", sa.String(100), nullable=True),
        sa.Column("document_url", sa.Text, nullable=True),
        sa.Column(
            "data_source",
            postgresql.ENUM("1c", "user", "hr_approved", name="data_source", create_type=False),
            nullable=False,
            server_default="1c",
        ),
        sa.Column("external_id_1c", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_education_records_employee_id", "education_records", ["employee_id"])
    _create_updated_at_trigger("education_records")

    # ------------------------------------------------------------------
    # family_members
    # ------------------------------------------------------------------
    op.create_table(
        "family_members",
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
        ),
        sa.Column(
            "member_type",
            postgresql.ENUM("child", "spouse", "ex_spouse", name="family_member_type", create_type=False),
            nullable=False,
        ),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("middle_name", sa.String(100), nullable=True),
        sa.Column("birth_date", sa.Date, nullable=True),
        # IIN is stored encrypted (Fernet) as text
        sa.Column("iin_encrypted", sa.Text, nullable=True),
        # Child fields
        sa.Column("birth_cert_number", sa.String(100), nullable=True),
        sa.Column("birth_cert_series", sa.String(50), nullable=True),
        sa.Column("birth_cert_issue_date", sa.Date, nullable=True),
        sa.Column("birth_cert_issued_by", sa.String(255), nullable=True),
        # Spouse fields
        sa.Column("spouse_status", sa.String(50), nullable=True),
        sa.Column("marriage_cert_number", sa.String(100), nullable=True),
        sa.Column("marriage_cert_issue_date", sa.Date, nullable=True),
        sa.Column("marriage_cert_org", sa.String(255), nullable=True),
        sa.Column("document_url", sa.Text, nullable=True),
        sa.Column(
            "data_source",
            postgresql.ENUM("1c", "user", "hr_approved", name="data_source", create_type=False),
            nullable=False,
            server_default="1c",
        ),
        sa.Column("external_id_1c", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_family_members_employee_id", "family_members", ["employee_id"])
    _create_updated_at_trigger("family_members")

    # ------------------------------------------------------------------
    # emergency_contacts
    # ------------------------------------------------------------------
    op.create_table(
        "emergency_contacts",
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
        ),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(32), nullable=False),
        sa.Column("address", sa.String(255), nullable=True),
        sa.Column("relationship", sa.String(100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_emergency_contacts_employee_id", "emergency_contacts", ["employee_id"])
    _create_updated_at_trigger("emergency_contacts")

    # ------------------------------------------------------------------
    # social_info  (1:1 with employees)
    # ------------------------------------------------------------------
    op.create_table(
        "social_info",
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
        sa.Column("pension_status", sa.String(100), nullable=True),
        sa.Column("has_disability", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("disability_group", sa.Integer, nullable=True),
        sa.Column("is_ww2_veteran", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("is_ww2_family", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("document_url", sa.Text, nullable=True),
        sa.Column(
            "data_source",
            postgresql.ENUM("1c", "user", "hr_approved", name="data_source", create_type=False),
            nullable=False,
            server_default="1c",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_social_info_employee_id", "social_info", ["employee_id"])
    _create_updated_at_trigger("social_info")

    # ------------------------------------------------------------------
    # medical_certificates
    # ------------------------------------------------------------------
    op.create_table(
        "medical_certificates",
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
        ),
        sa.Column(
            "cert_type",
            postgresql.ENUM(
                "narco_dispensary", "psycho_dispensary", "form_075",
                name="medical_cert_type", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("cert_number", sa.String(100), nullable=False),
        sa.Column("issue_date", sa.Date, nullable=False),
        sa.Column("expiry_date", sa.Date, nullable=True),
        sa.Column("document_url", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_medical_certificates_employee_id", "medical_certificates", ["employee_id"])
    _create_updated_at_trigger("medical_certificates")

    # ------------------------------------------------------------------
    # bank_accounts
    # ------------------------------------------------------------------
    op.create_table(
        "bank_accounts",
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
        ),
        sa.Column("bank_name", sa.String(255), nullable=False),
        # account_number is stored encrypted (Fernet) as text
        sa.Column("account_number_encrypted", sa.Text, nullable=False),
        sa.Column("bik", sa.String(20), nullable=False),
        sa.Column(
            "account_type",
            postgresql.ENUM("standard", "social", "other", name="bank_account_type", create_type=False),
            nullable=False,
            server_default="standard",
        ),
        sa.Column("holder_name", sa.String(255), nullable=False),
        sa.Column("document_url", sa.Text, nullable=True),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column(
            "data_source",
            postgresql.ENUM("1c", "user", "hr_approved", name="data_source", create_type=False),
            nullable=False,
            server_default="1c",
        ),
        sa.Column("external_id_1c", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_bank_accounts_employee_id", "bank_accounts", ["employee_id"])
    _create_updated_at_trigger("bank_accounts")

    # ------------------------------------------------------------------
    # personal_data_change_requests
    # ------------------------------------------------------------------
    op.create_table(
        "personal_data_change_requests",
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
        ),
        sa.Column(
            "section",
            postgresql.ENUM(
                "basic_data", "citizenship", "document", "address", "education",
                "family", "emergency_contact", "social_info", "medical", "bank", "other",
                name="change_request_section", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("old_value", postgresql.JSONB, nullable=True),
        sa.Column("new_value", postgresql.JSONB, nullable=False),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column("document_url", sa.Text, nullable=True),
        sa.Column(
            "hr_employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("employees.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("hr_email", sa.String(320), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "sent", "under_review", "approved", "rejected",
                name="change_request_status", create_type=False,
            ),
            nullable=False,
            server_default="sent",
        ),
        sa.Column("hr_comment", sa.Text, nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_pdcr_employee_id", "personal_data_change_requests", ["employee_id"]
    )
    op.create_index(
        "ix_pdcr_employee_status",
        "personal_data_change_requests",
        ["employee_id", "status"],
    )
    op.create_index(
        "ix_pdcr_hr_employee_status",
        "personal_data_change_requests",
        ["hr_employee_id", "status"],
    )
    _create_updated_at_trigger("personal_data_change_requests")


def downgrade() -> None:
    # Drop triggers
    for table in reversed(_NEW_TABLES):
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_updated_at ON {table}")

    # Drop indexes
    op.drop_index("ix_pdcr_hr_employee_status", table_name="personal_data_change_requests")
    op.drop_index("ix_pdcr_employee_status", table_name="personal_data_change_requests")
    op.drop_index("ix_pdcr_employee_id", table_name="personal_data_change_requests")
    op.drop_index("ix_bank_accounts_employee_id", table_name="bank_accounts")
    op.drop_index("ix_medical_certificates_employee_id", table_name="medical_certificates")
    op.drop_index("ix_social_info_employee_id", table_name="social_info")
    op.drop_index("ix_emergency_contacts_employee_id", table_name="emergency_contacts")
    op.drop_index("ix_family_members_employee_id", table_name="family_members")
    op.drop_index("ix_education_records_employee_id", table_name="education_records")
    op.drop_index("ix_employee_addresses_employee_id", table_name="employee_addresses")
    op.drop_index("ix_identity_documents_employee_id", table_name="identity_documents")
    op.drop_index("ix_citizenship_records_employee_id", table_name="citizenship_records")
    op.drop_index("ix_personal_data_employee_id", table_name="personal_data")

    # Drop tables
    for table in reversed(_NEW_TABLES):
        op.drop_table(table)

    # Drop enums
    for enum_name in reversed(_NEW_ENUMS):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")

    # NOTE: set_updated_at() function is shared; do not drop it here
    # as it may be used by other migrations.

