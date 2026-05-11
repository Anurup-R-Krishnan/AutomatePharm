from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.customer import Customer
from models.transaction import Invoice

router = APIRouter()

@router.get("/customers")
def list_customers(db: Session = Depends(get_db)):
    return db.query(Customer).filter(Customer.is_active == True).all()

@router.post("/customers/add")
def add_customer(data: dict, db: Session = Depends(get_db)):
    cust = Customer(**data)
    db.add(cust)
    db.commit()
    return cust

@router.get("/customers/{customer_id}/history")
def purchase_history(customer_id: int, db: Session = Depends(get_db)):
    invoices = db.query(Invoice).filter(Invoice.customer_id == customer_id).order_by(Invoice.created_at.desc()).all()
    return {"customer_id": customer_id, "total_invoices": len(invoices), "invoices": invoices}

@router.post("/customers/{customer_id}/loyalty/redeem")
def redeem_loyalty(customer_id: int, points: float, db: Session = Depends(get_db)):
    cust = db.query(Customer).filter(Customer.id == customer_id).first()
    if cust.loyalty_points < points:
        return {"error": "Insufficient points"}
    cust.loyalty_points -= points
    db.commit()
    return {"remaining_points": cust.loyalty_points, "redeemed": points}
