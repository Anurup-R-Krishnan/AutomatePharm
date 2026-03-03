from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.medicine import Medicine
from datetime import date, timedelta

router = APIRouter()

@router.get("/")
def list_medicines(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Medicine).filter(Medicine.is_active == True).offset(skip).limit(limit).all()

@router.post("/add")
def add_medicine(med_data: dict, db: Session = Depends(get_db)):
    med = Medicine(**med_data)
    db.add(med)
    db.commit()
    db.refresh(med)
    return med

@router.put("/{med_id}")
def update_medicine(med_id: int, med_data: dict, db: Session = Depends(get_db)):
    med = db.query(Medicine).filter(Medicine.id == med_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found")
    for key, val in med_data.items():
        setattr(med, key, val)
    db.commit()
    return med

@router.get("/low-stock")
def low_stock_alert(db: Session = Depends(get_db)):
    items = db.query(Medicine).filter(Medicine.stock_qty <= Medicine.reorder_level).all()
    return {"count": len(items), "items": items}

@router.get("/expiry-alert")
def expiry_alert(days: int = 90, db: Session = Depends(get_db)):
    cutoff = date.today() + timedelta(days=days)
    items = db.query(Medicine).filter(Medicine.expiry_date <= cutoff, Medicine.stock_qty > 0).all()
    return {"count": len(items), "items": items}

@router.get("/search")
def search_medicine(q: str, db: Session = Depends(get_db)):
    results = db.query(Medicine).filter(
        (Medicine.name.ilike(f"%{q}%")) | (Medicine.generic_name.ilike(f"%{q}%")) |
        (Medicine.barcode == q)
    ).all()
    return results
