"""AI face detection event log model."""
from datetime import datetime
from ..extensions import db

class AiFaceLog(db.Model):
    __tablename__ = 'ai_face_logs'
    log_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.customer_id'), nullable=True)
    camera_id = db.Column(db.String(50), nullable=False, default='webcam')
    detected_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    confidence_score = db.Column(db.Float, nullable=True)
    action_triggered = db.Column(db.String(100), nullable=True)
    is_fraud_alert = db.Column(db.Boolean, nullable=False, default=False)

class PrescriptionOcrLog(db.Model):
    __tablename__ = 'prescription_ocr_logs'

    ocr_log_id = db.Column(db.BigInteger, primary_key=True)
    image_url = db.Column(db.Text, nullable=False)
    processed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    raw_extracted_text = db.Column(db.JSON)
    parsed_medicines = db.Column(db.JSON)
    confidence_score = db.Column(db.Numeric(5, 2))
    requires_human_verification = db.Column(db.Boolean, nullable=False, default=True)
    verified_by = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=True)
    verified_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
