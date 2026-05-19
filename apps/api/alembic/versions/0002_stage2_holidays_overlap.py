"""Stage 2: holidays table and approved vacation overlap guard

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-18 12:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "holidays",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=False, server_default="KZ"),
        sa.UniqueConstraint("date", name="uq_holidays_date"),
    )
    op.create_index("ix_holidays_date", "holidays", ["date"])

    op.execute("""
        INSERT INTO holidays (date, name, country_code) VALUES
        ('2026-01-01', 'New Year', 'KZ'),
        ('2026-01-02', 'New Year Holiday', 'KZ'),
        ('2026-01-07', 'Orthodox Christmas', 'KZ'),
        ('2026-03-08', 'International Women''s Day', 'KZ'),
        ('2026-03-21', 'Nauryz', 'KZ'),
        ('2026-03-22', 'Nauryz', 'KZ'),
        ('2026-03-23', 'Nauryz', 'KZ'),
        ('2026-05-01', 'Unity Day', 'KZ'),
        ('2026-05-07', 'Defender''s Day', 'KZ'),
        ('2026-05-09', 'Victory Day', 'KZ'),
        ('2026-07-06', 'Capital City Day', 'KZ'),
        ('2026-08-30', 'Constitution Day', 'KZ'),
        ('2026-10-25', 'Republic Day', 'KZ'),
        ('2026-12-16', 'Independence Day', 'KZ')
        ON CONFLICT (date) DO NOTHING;
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION check_vacation_request_no_overlap()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.status = 'approved' THEN
                IF EXISTS (
                    SELECT 1 FROM vacation_requests vr
                    WHERE vr.employee_id = NEW.employee_id
                      AND vr.id <> NEW.id
                      AND vr.status = 'approved'
                      AND vr.start_date <= NEW.end_date
                      AND vr.end_date >= NEW.start_date
                ) THEN
                    RAISE EXCEPTION 'VACATION_OVERLAP'
                        USING ERRCODE = '23514';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_vacation_requests_no_overlap
        BEFORE INSERT OR UPDATE ON vacation_requests
        FOR EACH ROW EXECUTE PROCEDURE check_vacation_request_no_overlap();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_vacation_requests_no_overlap ON vacation_requests")
    op.execute("DROP FUNCTION IF EXISTS check_vacation_request_no_overlap()")
    op.drop_index("ix_holidays_date", table_name="holidays")
    op.drop_table("holidays")
