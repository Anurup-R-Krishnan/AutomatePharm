from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from ..extensions import db


class ReorderRequest(db.Model):
    __tablename__ = "reorder_requests"

    reorder_id = db.Column(db.BigInteger, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.supplier_id"), nullable=False)
    requested_by = db.Column(UUID(as_uuid=True), db.ForeignKey("users.user_id"))
    source = db.Column(db.String(20), nullable=False, default="MANUAL")
    status = db.Column(db.String(20), nullable=False, default="PENDING")
    channel = db.Column(db.String(20), nullable=False, default="WHATSAPP")
    message = db.Column(db.Text)
    provider_message_id = db.Column(db.String(100))
    error_message = db.Column(db.Text)
    total_items = db.Column(db.Integer, nullable=False, default=0)
    requested_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime)
    confirmed_at = db.Column(db.DateTime)

    items = db.relationship("ReorderItem", back_populates="reorder", lazy="dynamic")

    __table_args__ = (
        db.CheckConstraint(
            "source IN ('MANUAL','SCHEDULED')",
            name="reorder_source_check",
        ),
        db.CheckConstraint(
            "status IN ('PENDING','SENT','FAILED','CONFIRMED')",
            name="reorder_status_check",
        ),
        db.CheckConstraint(
            "channel IN ('WHATSAPP')",
            name="reorder_channel_check",
        ),
    )


class ReorderItem(db.Model):
    __tablename__ = "reorder_items"

    reorder_item_id = db.Column(db.BigInteger, primary_key=True)
    reorder_id = db.Column(db.BigInteger, db.ForeignKey("reorder_requests.reorder_id"), nullable=False)
    item_id = db.Column(db.String(10), db.ForeignKey("items.item_id"), nullable=False)
    supplier_item_id = db.Column(db.Integer, db.ForeignKey("supplier_items.supplier_item_id"))
    requested_qty = db.Column(db.Integer, nullable=False)
    current_stock = db.Column(db.Integer, nullable=False, default=0)
    reorder_level = db.Column(db.Integer, nullable=False, default=0)
    max_stock = db.Column(db.Integer)
    qty_rule = db.Column(db.String(20), nullable=False, default="CUSTOM")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    reorder = db.relationship("ReorderRequest", back_populates="items")

    __table_args__ = (
        db.CheckConstraint("requested_qty > 0", name="reorder_qty_positive"),
        db.CheckConstraint(
            "qty_rule IN ('CUSTOM','SUGGESTED')",
            name="reorder_qty_rule_check",
        ),
    )
