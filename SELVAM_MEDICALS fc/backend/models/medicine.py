from sqlalchemy import Column, Integer, String, Float, Date, Boolean, DateTime
from sqlalchemy.sql import func
from database import Base

class Medicine(Base):
    __tablename__ = "medicines"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    generic_name = Column(String(200))
    brand = Column(String(100))
    batch_no = Column(String(50))
    barcode = Column(String(100), unique=True, index=True)
    category = Column(String(50))         # tablet, syrup, injection, etc.
    hsn_code = Column(String(20))
    mrp = Column(Float, nullable=False)
    purchase_price = Column(Float)
    selling_price = Column(Float)
    gst_percent = Column(Float, default=12.0)
    stock_qty = Column(Integer, default=0)
    reorder_level = Column(Integer, default=10)
    reorder_qty = Column(Integer, default=50)
    expiry_date = Column(Date)
    manufacturer = Column(String(200))
    rack_location = Column(String(20))
    requires_prescription = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
