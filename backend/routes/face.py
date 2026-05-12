"""Face detection routes — register and identify."""
import json
import math
from datetime import datetime

from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models.core import Customer
from ..models.ai import AiFaceLog

face_bp = Blueprint("face", __name__)


def _cosine_distance(a, b):
    """Lower = more similar. 0 = identical."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 1.0
    return 1 - (dot / (mag_a * mag_b))


def _json_error(message, code=400):
    return jsonify({"status": "error", "message": message}), code


@face_bp.route("/api/face/register", methods=["POST"])
def register_face():
    """Save face descriptor to a customer record."""
    data = request.get_json(silent=True) or {}
    customer_id = data.get("customer_id")
    descriptor = data.get("descriptor")  # list of 128 floats

    if not customer_id:
        return _json_error("customer_id required")
    if not descriptor or len(descriptor) != 128:
        return _json_error("descriptor must be list of 128 floats")

    customer = Customer.query.get(customer_id)
    if not customer:
        return _json_error("Customer not found", 404)

    from sqlalchemy.orm.attributes import flag_modified
    customer.face_embedding = descriptor
    customer.last_face_scan_at = datetime.utcnow()
    flag_modified(customer, "face_embedding")
    db.session.commit()

    return jsonify({
        "status": "success",
        "customer_id": customer_id,
        "message": "Face registered"
    })


@face_bp.route("/api/face/identify", methods=["POST"])
def identify_face():
    """Match incoming descriptor against all stored embeddings."""
    data = request.get_json(silent=True) or {}
    descriptor = data.get("descriptor")  # list of 128 floats
    threshold = float(data.get("threshold", 0.45))

    if not descriptor or len(descriptor) != 128:
        return _json_error("descriptor must be list of 128 floats")

    customers = Customer.query.filter(
        Customer.face_embedding.isnot(None),
        Customer.is_active == True
    ).all()

    if not customers:
        return jsonify({"status": "no_match", "message": "No faces registered"})

    best_match = None
    best_distance = 1.0

    for customer in customers:
        stored = customer.face_embedding
        if not stored or len(stored) != 128:
            continue
        dist = _cosine_distance(descriptor, stored)
        if dist < best_distance:
            best_distance = dist
            best_match = customer

    if best_match and best_distance <= threshold:
        # log the recognition event
        log = AiFaceLog(
            customer_id=best_match.customer_id,
            confidence_score=round(1 - best_distance, 4),
            action_triggered="identified",
            detected_at=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            "status": "match",
            "customer": {
                "id": best_match.customer_id,
                "name": best_match.customer_name,
                "phone": best_match.phone or "",
                "balance": float(best_match.outstanding_balance or 0)
            },
            "confidence": round(1 - best_distance, 4),
            "distance": round(best_distance, 4)
        })

    return jsonify({
        "status": "no_match",
        "message": "No customer matched",
        "distance": round(best_distance, 4)
    })


@face_bp.route("/api/face/logs", methods=["GET"])
def get_face_logs():
    """Return recent face recognition events."""
    logs = AiFaceLog.query.order_by(
        AiFaceLog.detected_at.desc()
    ).limit(50).all()

    return jsonify([
        {
            "log_id": l.log_id,
            "customer_id": l.customer_id,
            "confidence": l.confidence_score,
            "action": l.action_triggered,
            "detected_at": l.detected_at.isoformat() + "Z",
            "fraud_alert": l.is_fraud_alert
        }
        for l in logs
    ])
