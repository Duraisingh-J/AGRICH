"""Add blockchain events durability table.

Revision ID: 0002_blockchain_events
Revises: 0001_initial
Create Date: 2026-02-27
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_blockchain_events"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create durable blockchain events table."""

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    event_status_enum = postgresql.ENUM(
        "pending",
        "processing",
        "completed",
        "failed",
        name="blockchain_event_status",
        create_type=True,
    )
    event_status_enum.create(bind, checkfirst=True)

    if not inspector.has_table("blockchain_events"):
        op.create_table(
            "blockchain_events",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("event_name", sa.String(length=80), nullable=False),
            sa.Column("tx_hash", sa.String(length=100), nullable=False),
            sa.Column("log_index", sa.Integer(), nullable=False),
            sa.Column("block_number", sa.Integer(), nullable=False),
            sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column(
                "status",
                postgresql.ENUM(
                    "pending",
                    "processing",
                    "completed",
                    "failed",
                    name="blockchain_event_status",
                    create_type=False,
                ),
                nullable=False,
            ),
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_error", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("tx_hash", "log_index", name="uq_blockchain_events_tx_log"),
        )

    op.execute("CREATE INDEX IF NOT EXISTS ix_blockchain_events_status ON blockchain_events (status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_blockchain_events_block_number ON blockchain_events (block_number)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_blockchain_events_next_retry_at ON blockchain_events (next_retry_at)")


def downgrade() -> None:
    """Drop blockchain events durability table."""

    op.drop_index("ix_blockchain_events_next_retry_at", table_name="blockchain_events")
    op.drop_index("ix_blockchain_events_block_number", table_name="blockchain_events")
    op.drop_index("ix_blockchain_events_status", table_name="blockchain_events")
    op.drop_table("blockchain_events")
    sa.Enum(name="blockchain_event_status").drop(op.get_bind(), checkfirst=True)
