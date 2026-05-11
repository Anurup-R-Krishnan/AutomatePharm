"""add reorder tables

Revision ID: c3b9c76e8e2d
Revises: e37895a1a06d
Create Date: 2026-05-11 22:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "c3b9c76e8e2d"
down_revision = "e37895a1a06d"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "reorder_requests",
        sa.Column("reorder_id", sa.BigInteger(), primary_key=True),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source", sa.String(length=20), nullable=False, server_default="MANUAL"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("channel", sa.String(length=20), nullable=False, server_default="WHATSAPP"),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("provider_message_id", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("total_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("requested_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.supplier_id"]),
        sa.ForeignKeyConstraint(["requested_by"], ["users.user_id"]),
        sa.CheckConstraint(
            "source IN ('MANUAL','SCHEDULED')",
            name="reorder_source_check",
        ),
        sa.CheckConstraint(
            "status IN ('PENDING','SENT','FAILED','CONFIRMED')",
            name="reorder_status_check",
        ),
        sa.CheckConstraint(
            "channel IN ('WHATSAPP')",
            name="reorder_channel_check",
        ),
    )

    op.create_table(
        "reorder_items",
        sa.Column("reorder_item_id", sa.BigInteger(), primary_key=True),
        sa.Column("reorder_id", sa.BigInteger(), nullable=False),
        sa.Column("item_id", sa.String(length=10), nullable=False),
        sa.Column("supplier_item_id", sa.Integer(), nullable=True),
        sa.Column("requested_qty", sa.Integer(), nullable=False),
        sa.Column("current_stock", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reorder_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_stock", sa.Integer(), nullable=True),
        sa.Column("qty_rule", sa.String(length=20), nullable=False, server_default="CUSTOM"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["reorder_id"], ["reorder_requests.reorder_id"]),
        sa.ForeignKeyConstraint(["item_id"], ["items.item_id"]),
        sa.ForeignKeyConstraint(["supplier_item_id"], ["supplier_items.supplier_item_id"]),
        sa.CheckConstraint("requested_qty > 0", name="reorder_qty_positive"),
        sa.CheckConstraint(
            "qty_rule IN ('CUSTOM','SUGGESTED')",
            name="reorder_qty_rule_check",
        ),
    )


def downgrade():
    op.drop_table("reorder_items")
    op.drop_table("reorder_requests")
