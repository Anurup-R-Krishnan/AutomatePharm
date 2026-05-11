"""
AI Camera Module
- Face recognition for returning customers
- Prescription OCR scanning
- Medicine strip detection via barcode/YOLO
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.customer import Customer
import numpy as np
import json
import io

router = APIRouter()

# ─── Face Recognition ─────────────────────────────────────────────────────────
@router.post("/face/register/{customer_id}")
async def register_face(customer_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        import face_recognition
        contents = await file.read()
        img_array = np.frombuffer(contents, np.uint8)
        import cv2
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb)
        if not encodings:
            raise HTTPException(status_code=400, detail="No face detected in image")
        cust = db.query(Customer).filter(Customer.id == customer_id).first()
        if not cust:
            raise HTTPException(status_code=404, detail="Customer not found")
        cust.face_encoding = json.dumps(encodings[0].tolist())
        db.commit()
        return {"message": "Face registered successfully", "customer_id": customer_id}
    except ImportError:
        raise HTTPException(status_code=501, detail="face_recognition library not installed")

@router.post("/face/identify")
async def identify_customer(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        import face_recognition
        contents = await file.read()
        img_array = np.frombuffer(contents, np.uint8)
        import cv2
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        unknown_encodings = face_recognition.face_encodings(rgb)
        if not unknown_encodings:
            return {"identified": False, "message": "No face detected"}
        unknown_enc = unknown_encodings[0]
        customers = db.query(Customer).filter(Customer.face_encoding.isnot(None)).all()
        for cust in customers:
            known_enc = np.array(json.loads(cust.face_encoding))
            match = face_recognition.compare_faces([known_enc], unknown_enc, tolerance=0.5)
            if match[0]:
                return {"identified": True, "customer_id": cust.id, "customer_name": cust.name,
                        "loyalty_points": cust.loyalty_points}
        return {"identified": False, "message": "Customer not found in database"}
    except ImportError:
        raise HTTPException(status_code=501, detail="face_recognition library not installed")

# ─── Prescription OCR ─────────────────────────────────────────────────────────
@router.post("/prescription/scan")
async def scan_prescription(file: UploadFile = File(...)):
    try:
        import pytesseract
        from PIL import Image, ImageEnhance, ImageFilter
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))
        img = img.convert("L")
        img = ImageEnhance.Contrast(img).enhance(2.0)
        img = img.filter(ImageFilter.SHARPEN)
        text = pytesseract.image_to_string(img)
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        return {"raw_text": text, "lines": lines, "medicine_count_estimate": len(lines)}
    except ImportError:
        raise HTTPException(status_code=501, detail="pytesseract not installed")

# ─── Barcode / Strip Scanner ───────────────────────────────────────────────────
@router.post("/barcode/scan")
async def scan_barcode(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        import cv2
        from models.medicine import Medicine
        contents = await file.read()
        img_array = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        detector = cv2.QRCodeDetector()
        val, _, _ = detector.detectAndDecode(img)
        if val:
            med = db.query(Medicine).filter(Medicine.barcode == val).first()
            if med:
                return {"barcode": val, "found": True, "medicine": {"id": med.id, "name": med.name,
                        "mrp": med.mrp, "stock": med.stock_qty}}
            return {"barcode": val, "found": False}
        return {"barcode": None, "found": False, "message": "No barcode detected"}
    except ImportError:
        raise HTTPException(status_code=501, detail="opencv not installed")
