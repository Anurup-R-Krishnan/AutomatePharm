"""
Staff Commission Engine
Tracks sales by staff member and calculates monthly commissions.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.transaction import Invoice, User
from datetime import date

router = APIRouter()

@router.get("/staff/{user_id}/summary")
def staff_commission_summary(user_id: int, month: int = None, year: int = None, db: Session = Depends(get_db)):
    today = date.today()
    m, y = month or today.month, year or today.year
    invoices = db.query(Invoice).filter(
        Invoice.created_by == user_id,
        func.month(Invoice.created_at) == m,
        func.year(Invoice.created_at) == y
    ).all()
    total_sales = sum(i.total_amount for i in invoices)
    user = db.query(User).filter(User.id == user_id).first()
    commission_pct = user.commission_percent if user else 0
    commission_earned = total_sales * (commission_pct / 100)
    return {
        "user_id": user_id, "staff_name": user.full_name if user else "Unknown",
        "month": m, "year": y, "total_sales": round(total_sales, 2),
        "commission_percent": commission_pct, "commission_earned": round(commission_earned, 2),
        "invoice_count": len(invoices)
    }

@router.get("/all-staff/summary")
def all_staff_summary(month: int = None, year: int = None, db: Session = Depends(get_db)):
    users = db.query(User).filter(User.is_active == True).all()
    summaries = []
    for user in users:
        today = date.today()
        m, y = month or today.month, year or today.year
        invoices = db.query(Invoice).filter(
            Invoice.created_by == user.id,
            func.month(Invoice.created_at) == m,
            func.year(Invoice.created_at) == y
        ).all()
        total_sales = sum(i.total_amount for i in invoices)
        commission = total_sales * (user.commission_percent / 100)
        summaries.append({"staff": user.full_name, "sales": round(total_sales, 2), "commission": round(commission, 2)})
    return summaries
