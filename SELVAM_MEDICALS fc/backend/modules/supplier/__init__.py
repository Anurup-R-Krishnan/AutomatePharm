from fastapi import APIRouter, Depends
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.sql import func
from database import get_db, Base
from sqlalchemy.orm import Session

class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    contact_person = Column(String(100))
    phone = Column(String(15))
    email = Column(String(100))
    address = Column(String(500))
    gst_no = Column(String(20))
    drug_license = Column(String(50))
    payment_terms = Column(Integer, default=30)  # days
    medicines_supplied = Column(JSON)            # list of medicine IDs
    outstanding_amount = Column(Float, default=0.0)
    created_at = Column(DateTime, server_default=func.now())

router = APIRouter()

@router.get("/")
def list_suppliers(db: Session = Depends(get_db)):
    return db.query(Supplier).all()

@router.post("/add")
def add_supplier(data: dict, db: Session = Depends(get_db)):
    supplier = Supplier(**data)
    db.add(supplier)
    db.commit()
    return supplier
