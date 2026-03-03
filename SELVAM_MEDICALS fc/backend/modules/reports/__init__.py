from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.transaction import Invoice
from models.medicine import Medicine
from datetime import date, timedelta

router = APIRouter()

@router.get("/daily-sales")
def daily_sales(target_date: str = None, db: Session = Depends(get_db)):
    d = date.fromisoformat(target_date) if target_date else date.today()
    invoices = db.query(Invoice).filter(func.date(Invoice.created_at) == d).all()
    total = sum(i.total_amount for i in invoices)
    return {"date": str(d), "invoice_count": len(invoices), "total_sales": total, "invoices": invoices}

@router.get("/monthly-sales")
def monthly_sales(year: int = None, month: int = None, db: Session = Depends(get_db)):
    today = date.today()
    y, m = year or today.year, month or today.month
    invoices = db.query(Invoice).filter(
        func.year(Invoice.created_at) == y, func.month(Invoice.created_at) == m
    ).all()
    return {"year": y, "month": m, "total": sum(i.total_amount for i in invoices), "count": len(invoices)}

@router.get("/gst-report")
def gst_report(from_date: str, to_date: str, db: Session = Depends(get_db)):
    invoices = db.query(Invoice).filter(
        Invoice.created_at >= from_date, Invoice.created_at <= to_date
    ).all()
    total_gst = sum(i.gst_amount for i in invoices)
    return {"from": from_date, "to": to_date, "total_gst_collected": total_gst, "invoice_count": len(invoices)}

@router.get("/top-medicines")
def top_medicines(days: int = 30, limit: int = 10, db: Session = Depends(get_db)):
    cutoff = date.today() - timedelta(days=days)
    invoices = db.query(Invoice).filter(Invoice.created_at >= str(cutoff)).all()
    med_count = {}
    for inv in invoices:
        for item in (inv.items or []):
            name = item.get("name", "")
            med_count[name] = med_count.get(name, 0) + item.get("qty", 0)
    sorted_meds = sorted(med_count.items(), key=lambda x: x[1], reverse=True)[:limit]
    return {"top_medicines": [{"name": k, "qty_sold": v} for k, v in sorted_meds]}
