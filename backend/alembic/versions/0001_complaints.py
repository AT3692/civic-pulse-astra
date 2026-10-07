"""Create complaints with domain constraints and query indexes."""

import sqlalchemy as sa

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "complaints",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("location", sa.String(200), nullable=False),
        sa.Column("reporter_contact", sa.String(254)),
        sa.Column(
            "category",
            sa.Enum("water", "electricity", "sanitation", "roads", "streetlights", "other", name="category"),
            nullable=False,
        ),
        sa.Column("priority", sa.Enum("high", "normal", "low", name="priority"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("open", "in_progress", "resolved", "rejected", name="status"),
            nullable=False,
            server_default="open",
        ),
        sa.Column("ai_summary", sa.String(140)),
        sa.Column("triaged_by", sa.String(40), nullable=False),
        sa.Column("triage_latency_ms", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("length(text) BETWEEN 10 AND 2000", name="ck_text_length"),
        sa.CheckConstraint("length(location) BETWEEN 3 AND 200", name="ck_location_length"),
        sa.CheckConstraint("triage_latency_ms >= 0", name="ck_latency"),
    )
    op.create_index("ix_complaints_status_priority", "complaints", ["status", "priority"])
    op.create_index("ix_complaints_created_at", "complaints", ["created_at"])


def downgrade():
    op.drop_table("complaints")
    for name in ("status", "priority", "category"):
        sa.Enum(name=name).drop(op.get_bind(), checkfirst=True)
