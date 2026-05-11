from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from database import Base

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True)
    invoice_no = Column(String(30), unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    customer_name = Column(String(200))
    customer_phone = Column(String(15))
    items = Column(JSON)                  # [{medicine_id, name, qty, rate, gst, total}]
    subtotal = Column(Float)
    gst_amount = Column(Float)
    discount = Column(Float, default=0)
    total_amount = Column(Float)
    payment_mode = Column(String(20))     # cash, card, upi, credit
    payment_status = Column(String(20), default="paid")
    prescription_id = Column(Integer, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    full_name = Column(String(200))
    role = Column(String(30))             # admin, pharmacist, cashier
    hashed_password = Column(String(200))
    is_active = Column(Boolean, default=True)
    commission_percent = Column(Float, default=0.0)
