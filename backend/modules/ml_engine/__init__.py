"""
ML Engine - Demand Forecasting & Smart Reorder Suggestions
Uses historical sales data to predict future demand.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.transaction import Invoice
from models.medicine import Medicine
from datetime import date, timedelta
from collections import defaultdict
import math

router = APIRouter()

def calculate_avg_daily_sales(medicine_id: int, db: Session, days: int = 90) -> float:
    cutoff = date.today() - timedelta(days=days)
    invoices = db.query(Invoice).filter(Invoice.created_at >= str(cutoff)).all()
    total_qty = 0
    for inv in invoices:
        for item in (inv.items or []):
            if item.get("medicine_id") == medicine_id:
                total_qty += item.get("qty", 0)
    return total_qty / days

@router.get("/demand-forecast/{medicine_id}")
def demand_forecast(medicine_id: int, days_ahead: int = 30, db: Session = Depends(get_db)):
    avg_daily = calculate_avg_daily_sales(medicine_id, db)
    forecasted_qty = math.ceil(avg_daily * days_ahead * 1.15)  # 15% safety buffer
    med = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    return {
        "medicine_id": medicine_id,
        "medicine_name": med.name if med else "Unknown",
        "avg_daily_sales": round(avg_daily, 2),
        "forecast_days": days_ahead,
        "forecasted_demand": forecasted_qty,
        "current_stock": med.stock_qty if med else 0,
        "suggested_order_qty": max(0, forecasted_qty - (med.stock_qty if med else 0))
    }

@router.get("/smart-reorder-list")
def smart_reorder_list(db: Session = Depends(get_db)):
    medicines = db.query(Medicine).filter(Medicine.is_active == True).all()
    reorder_list = []
    for med in medicines:
        avg_daily = calculate_avg_daily_sales(med.id, db)
        days_of_stock = (med.stock_qty / avg_daily) if avg_daily > 0 else 999
        if days_of_stock < 30:
            reorder_list.append({
                "id": med.id, "name": med.name, "current_stock": med.stock_qty,
                "avg_daily_sales": round(avg_daily, 2),
                "days_of_stock_remaining": round(days_of_stock, 1),
                "suggested_order": math.ceil(avg_daily * 45)
            })
    reorder_list.sort(key=lambda x: x["days_of_stock_remaining"])
    return {"items": reorder_list, "count": len(reorder_list)}
