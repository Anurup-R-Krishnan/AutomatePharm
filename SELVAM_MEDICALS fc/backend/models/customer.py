from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date
from sqlalchemy.sql import func
from database import Base

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(15), unique=True, index=True)
    email = Column(String(100))
    address = Column(String(500))
    dob = Column(Date)
    gender = Column(String(10))
    loyalty_points = Column(Float, default=0.0)
    total_purchases = Column(Float, default=0.0)
    credit_limit = Column(Float, default=0.0)
    outstanding_balance = Column(Float, default=0.0)
    face_encoding = Column(String(5000))   # stored JSON of face vector
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
