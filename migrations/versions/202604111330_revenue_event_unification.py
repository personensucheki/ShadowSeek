"""
Revision ID: 202604111330
Revises: 202604111201
Create Date: 2026-04-11
"""

from alembic import op
import sqlalchemy as sa


revision = "202604111330"
down_revision = "202604111201"
branch_labels = None
depends_on = None


def upgrade():
    # Prüfe, ob die Spalte bereits existiert
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("einnahme_info")]
    if "platform" not in columns:
        op.add_column("einnahme_info", sa.Column("platform", sa.String(length=32), nullable=True))
    if "username" not in columns:
        op.add_column("einnahme_info", sa.Column("username", sa.String(length=128), nullable=True))
    if "display_name" not in columns:
        op.add_column("einnahme_info", sa.Column("display_name", sa.String(length=128), nullable=True))
    if "estimated_revenue" not in columns:
        op.add_column("einnahme_info", sa.Column("estimated_revenue", sa.Float(), nullable=True))
    if "currency" not in columns:
        op.add_column("einnahme_info", sa.Column("currency", sa.String(length=16), nullable=True))
    if "captured_at" not in columns:
        op.add_column("einnahme_info", sa.Column("captured_at", sa.DateTime(), nullable=True))
    if "source" not in columns:
        op.add_column("einnahme_info", sa.Column("source", sa.String(length=128), nullable=True))
    if "confidence" not in columns:
        op.add_column("einnahme_info", sa.Column("confidence", sa.Float(), nullable=True))

    op.execute("UPDATE einnahme_info SET platform = lower(substr(typ, 1, instr(typ, '_') - 1)) WHERE typ LIKE '%_%'")
    op.execute("UPDATE einnahme_info SET platform = lower(typ) WHERE (platform IS NULL OR platform = '') AND typ IS NOT NULL")
    op.execute("UPDATE einnahme_info SET username = COALESCE(NULLIF(trim(quelle), ''), 'unknown')")
    op.execute("UPDATE einnahme_info SET display_name = username WHERE display_name IS NULL OR trim(display_name) = ''")
    op.execute("UPDATE einnahme_info SET estimated_revenue = betrag WHERE estimated_revenue IS NULL")
    op.execute("UPDATE einnahme_info SET currency = COALESCE(NULLIF(waehrung, ''), 'EUR')")
    op.execute("UPDATE einnahme_info SET captured_at = zeitpunkt WHERE captured_at IS NULL")
    op.execute("UPDATE einnahme_info SET source = 'scraper' WHERE source IS NULL OR trim(source) = ''")
    op.execute("UPDATE einnahme_info SET confidence = 0.7 WHERE confidence IS NULL")

    # Nur für Nicht-SQLite: Unique Constraint anlegen
    if conn.dialect.name != 'sqlite':
        op.create_unique_constraint(
            "uq_revenue_event",
            "einnahme_info",
            ["platform", "username", "captured_at", "source"],
        )


def downgrade():
    op.drop_constraint("uq_revenue_event", "einnahme_info", type_="unique")
    op.drop_column("einnahme_info", "confidence")
    op.drop_column("einnahme_info", "source")
    op.drop_column("einnahme_info", "captured_at")
    op.drop_column("einnahme_info", "currency")
    op.drop_column("einnahme_info", "estimated_revenue")
    op.drop_column("einnahme_info", "display_name")
    op.drop_column("einnahme_info", "username")
    op.drop_column("einnahme_info", "platform")
