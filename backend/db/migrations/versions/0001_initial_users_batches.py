"""Initial users and batches schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-02-27
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial users and batches tables."""

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    user_role_enum = postgresql.ENUM(
        "farmer",
        "distributor",
        "retailer",
        "consumer",
        name="user_role",
        create_type=True,
    )
    batch_status_enum = postgresql.ENUM(
        "created",
        "in_transit",
        "delivered",
        "received",
        "rejected",
        name="batch_status",
        create_type=True,
    )
    user_role_enum.create(bind, checkfirst=True)
    batch_status_enum.create(bind, checkfirst=True)

    if not inspector.has_table("users"):
        op.create_table(
            "users",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("phone", sa.String(length=20), nullable=False),
            sa.Column(
                "role",
                postgresql.ENUM(
                    "farmer",
                    "distributor",
                    "retailer",
                    "consumer",
                    name="user_role",
                    create_type=False,
                ),
                nullable=False,
            ),
            sa.Column("aadhaar_hash", sa.String(length=64), nullable=False),
            sa.Column("wallet_address", sa.String(length=42), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("is_verified", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("email"),
            sa.UniqueConstraint("phone"),
            sa.UniqueConstraint("wallet_address"),
        )

    op.execute("CREATE INDEX IF NOT EXISTS ix_users_email ON users (email)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_wallet_address ON users (wallet_address)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_aadhaar_hash ON users (aadhaar_hash)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_role ON users (role)")

    if not inspector.has_table("batches"):
        op.create_table(
            "batches",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("batch_code", sa.String(length=40), nullable=False),
            sa.Column("farmer_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("current_owner_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("crop_type", sa.String(length=120), nullable=False),
            sa.Column("quantity", sa.String(length=50), nullable=False),
            sa.Column("ipfs_metadata_cid", sa.String(length=120), nullable=False),
            sa.Column("blockchain_tx_hash", sa.String(length=100), nullable=True),
            sa.Column(
                "status",
                postgresql.ENUM(
                    "created",
                    "in_transit",
                    "delivered",
                    "received",
                    "rejected",
                    name="batch_status",
                    create_type=False,
                ),
                nullable=False,
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["current_owner_id"], ["users.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["farmer_id"], ["users.id"], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("batch_code"),
        )

    op.execute("CREATE INDEX IF NOT EXISTS ix_batches_batch_code ON batches (batch_code)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_batches_farmer_id ON batches (farmer_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_batches_current_owner_id ON batches (current_owner_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_batches_status ON batches (status)")


def downgrade() -> None:
    """Drop initial users and batches schema."""

    op.drop_index("ix_batches_status", table_name="batches")
    op.drop_index("ix_batches_current_owner_id", table_name="batches")
    op.drop_index("ix_batches_farmer_id", table_name="batches")
    op.drop_index("ix_batches_batch_code", table_name="batches")
    op.drop_table("batches")

    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ix_users_aadhaar_hash", table_name="users")
    op.drop_index("ix_users_wallet_address", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    sa.Enum(name="batch_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="user_role").drop(op.get_bind(), checkfirst=True)
