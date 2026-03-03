from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.transaction import Invoice
from models.medicine import Medicine
from datetime import datetime
import uuid

router = APIRouter()

@router.post("/create")
def create_invoice(invoice_data: dict, db: Session = Depends(get_db)):
    """Create a new billing invoice with GST calculation"""
    invoice_no = f"SM-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    items = invoice_data.get("items", [])
    subtotal = 0
    gst_total = 0
    processed_items = []

    for item in items:
        med = db.query(Medicine).filter(Medicine.id == item["medicine_id"]).first()
        if not med:
            raise HTTPException(status_code=404, detail=f"Medicine {item['medicine_id']} not found")
        if med.stock_qty < item["qty"]:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {med.name}")

        rate = med.selling_price
        qty = item["qty"]
        item_total = rate * qty
        gst = item_total * (med.gst_percent / 100)
        subtotal += item_total
        gst_total += gst

        med.stock_qty -= qty
        processed_items.append({
            "medicine_id": med.id, "name": med.name, "batch": med.batch_no,
            "qty": qty, "rate": rate, "gst_percent": med.gst_percent,
            "gst_amount": round(gst, 2), "total": round(item_total + gst, 2)
        })

    discount = invoice_data.get("discount", 0)
    total = subtotal + gst_total - discount

    inv = Invoice(
        invoice_no=invoice_no,
        customer_name=invoice_data.get("customer_name", "Walk-in Customer"),
        customer_phone=invoice_data.get("customer_phone", ""),
        items=processed_items,
        subtotal=round(subtotal, 2),
        gst_amount=round(gst_total, 2),
        discount=discount,
        total_amount=round(total, 2),
        payment_mode=invoice_data.get("payment_mode", "cash"),
        payment_status="paid"
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return {"invoice_no": invoice_no, "total": total, "invoice_id": inv.id}

@router.get("/{invoice_id}")
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return inv
