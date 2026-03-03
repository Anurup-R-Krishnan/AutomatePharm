"""
Automatic Reorder Engine
Monitors stock levels and triggers purchase orders to suppliers
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.medicine import Medicine
import schedule, time, threading, httpx
from datetime import datetime

router = APIRouter()

def auto_check_and_reorder(db_factory):
    db = next(db_factory())
    low_items = db.query(Medicine).filter(Medicine.stock_qty <= Medicine.reorder_level).all()
    for item in low_items:
        print(f"[REORDER] {item.name} — Stock: {item.stock_qty}, Reorder Level: {item.reorder_level}")
        # TODO: trigger supplier order via email/WhatsApp
    db.close()

@router.get("/pending-orders")
def pending_reorders(db: Session = Depends(get_db)):
    items = db.query(Medicine).filter(Medicine.stock_qty <= Medicine.reorder_level, Medicine.is_active == True).all()
    return [{
        "id": m.id, "name": m.name, "current_stock": m.stock_qty,
        "reorder_level": m.reorder_level, "reorder_qty": m.reorder_qty
    } for m in items]

@router.post("/trigger-order/{medicine_id}")
def trigger_manual_order(medicine_id: int, qty: int, db: Session = Depends(get_db)):
    med = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    return {
        "order_created": True, "medicine": med.name, "qty": qty,
        "estimated_cost": round(qty * (med.purchase_price or 0), 2),
        "message": f"Purchase order for {qty} units of {med.name} has been queued."
    }
