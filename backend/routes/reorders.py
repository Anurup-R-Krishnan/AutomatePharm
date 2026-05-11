import json
import os
import uuid
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from ..extensions import db
from ..models.core import Item, Supplier, SupplierItem
from ..models.inventory import StockBatch
from ..models.reorder import ReorderRequest, ReorderItem

reorders_bp = Blueprint("reorders", __name__)


def _json_error(message, code=400, details=None):
    return jsonify({"error": message, "details": details}), code


def _current_stock(item_id: str) -> int:
    return int(
        db.session.query(func.coalesce(func.sum(StockBatch.current_qty), 0))
        .filter_by(item_id=item_id)
        .scalar()
        or 0
    )


def _supplier_options(item_id: str) -> list[dict]:
    rows = (
        db.session.query(SupplierItem, Supplier)
        .join(Supplier, SupplierItem.supplier_id == Supplier.supplier_id)
        .filter(
            SupplierItem.item_id == item_id,
            SupplierItem.is_active.is_(True),
            Supplier.is_active.is_(True),
        )
        .all()
    )

    return [
        {
            "supplier_id": supplier.supplier_id,
            "supplier_name": supplier.supplier_name,
            "supplier_phone": supplier.phone or "",
            "preferred": bool(supplier_item.preferred_flag),
            "min_order_qty": int(supplier_item.min_order_qty or 1),
        }
        for supplier_item, supplier in rows
    ]


def _suggest_qty(item: Item, current_stock: int, low_stock_threshold: int) -> int:
    threshold = item.reorder_level if (item.reorder_level or 0) > 0 else low_stock_threshold
    if current_stock > threshold:
        return 0
    if item.max_stock and item.max_stock > 0:
        return max(item.max_stock - current_stock, threshold - current_stock)
    return max(threshold - current_stock, 0)


def _build_message(store_name: str, supplier_name: str, items: list[dict]) -> str:
    lines = [f"Reorder Request - {store_name}", f"Supplier: {supplier_name}", "", "Items:"]
    for idx, row in enumerate(items, 1):
        lines.append(f"{idx}) {row['item_name']} | Qty: {row['qty']}")
    lines.append("")
    lines.append("Please confirm availability and ETA.")
    return "\n".join(lines)


def _trigger_n8n(payload: dict) -> dict:
    url = os.getenv("N8N_WEBHOOK_URL", "").strip()
    if not url:
        return {"status": "skipped", "detail": "N8N_WEBHOOK_URL not configured"}

    headers = {"Content-Type": "application/json"}
    token = os.getenv("N8N_WEBHOOK_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    timeout = int(os.getenv("N8N_WEBHOOK_TIMEOUT", "15"))
    data = json.dumps(payload).encode("utf-8")

    try:
        req = Request(url, data=data, headers=headers, method="POST")
        with urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return {"status": "sent", "code": response.status, "response": body}
    except HTTPError as err:
        return {"status": "failed", "code": err.code, "detail": err.read().decode("utf-8")}
    except URLError as err:
        return {"status": "failed", "detail": str(err)}


@reorders_bp.route("/api/reorders", methods=["GET"])
def list_reorders():
    status = request.args.get("status")
    supplier_id = request.args.get("supplier_id")

    query = ReorderRequest.query
    if status:
        query = query.filter(func.lower(ReorderRequest.status) == status.lower())
    if supplier_id:
        try:
            query = query.filter(ReorderRequest.supplier_id == int(supplier_id))
        except ValueError:
            return _json_error("Invalid supplier_id", 400)

    rows = query.order_by(ReorderRequest.reorder_id.desc()).all()
    payload = []
    for row in rows:
        supplier = Supplier.query.get(row.supplier_id)
        payload.append(
            {
                "reorder_id": row.reorder_id,
                "supplier_id": row.supplier_id,
                "supplier_name": supplier.supplier_name if supplier else "",
                "status": row.status,
                "source": row.source,
                "channel": row.channel,
                "total_items": row.total_items,
                "requested_at": row.requested_at.isoformat() + "Z",
                "sent_at": row.sent_at.isoformat() + "Z" if row.sent_at else None,
            }
        )

    return jsonify(payload)


@reorders_bp.route("/api/reorders/low-stock", methods=["GET"])
def low_stock_reorders():
    low_stock_threshold = int(request.args.get("low_stock", 15))
    items = Item.query.filter(Item.is_active.is_(True)).order_by(Item.item_name).all()

    payload = []
    for item in items:
        stock = _current_stock(item.item_id)
        threshold = item.reorder_level if (item.reorder_level or 0) > 0 else low_stock_threshold
        if stock > threshold:
            continue

        payload.append(
            {
                "item_id": item.item_id,
                "item_name": item.item_name,
                "current_stock": stock,
                "reorder_level": int(item.reorder_level or threshold),
                "max_stock": int(item.max_stock or 0),
                "suggested_qty": _suggest_qty(item, stock, low_stock_threshold),
                "suppliers": _supplier_options(item.item_id),
            }
        )

    return jsonify({"low_stock": payload, "config": {"low_stock": low_stock_threshold}})


@reorders_bp.route("/api/reorders/request", methods=["POST"])
def create_reorder_request():
    data = request.get_json(silent=True) or {}
    items = data.get("items", [])
    if not items:
        return _json_error("Missing required field: items", 400)

    source = str(data.get("source", "MANUAL")).upper()
    if source not in {"MANUAL", "SCHEDULED"}:
        return _json_error("Invalid source", 400)

    requested_by = data.get("requested_by")
    if requested_by:
        try:
            requested_by = uuid.UUID(str(requested_by))
        except ValueError:
            return _json_error("Invalid requested_by UUID", 400)

    store_name = os.getenv("PHARMACY_STORE_NAME", "Selvam Medicals")
    trigger_n8n = bool(data.get("trigger_n8n", True))

    grouped: dict[int, list[dict]] = {}
    for row in items:
        try:
            supplier_id = int(row.get("supplier_id"))
        except (TypeError, ValueError):
            return _json_error("Invalid supplier_id", 400)

        item_id = str(row.get("item_id", "")).strip()
        if not item_id:
            return _json_error("Missing item_id", 400)

        try:
            qty = int(row.get("qty"))
        except (TypeError, ValueError):
            return _json_error("Invalid qty", 400)

        if qty <= 0:
            return _json_error("qty must be > 0", 400)

        grouped.setdefault(supplier_id, []).append(
            {
                "item_id": item_id,
                "qty": qty,
                "qty_rule": str(row.get("qty_rule", "CUSTOM")).upper(),
            }
        )

    responses = []
    n8n_results = []

    try:
        for supplier_id, group_items in grouped.items():
            supplier = Supplier.query.get(supplier_id)
            if not supplier:
                return _json_error("Supplier not found", 404, {"supplier_id": supplier_id})

            reorder = ReorderRequest(
                supplier_id=supplier_id,
                requested_by=requested_by,
                source=source,
                status="PENDING",
                channel="WHATSAPP",
            )
            db.session.add(reorder)
            db.session.flush()

            message_items = []
            for item_row in group_items:
                item = Item.query.get(item_row["item_id"])
                if not item:
                    return _json_error("Item not found", 404, {"item_id": item_row["item_id"]})

                stock = _current_stock(item.item_id)
                supplier_item = SupplierItem.query.filter_by(
                    supplier_id=supplier_id, item_id=item.item_id
                ).first()

                reorder_item = ReorderItem(
                    reorder_id=reorder.reorder_id,
                    item_id=item.item_id,
                    supplier_item_id=supplier_item.supplier_item_id if supplier_item else None,
                    requested_qty=item_row["qty"],
                    current_stock=stock,
                    reorder_level=int(item.reorder_level or 0),
                    max_stock=item.max_stock,
                    qty_rule=item_row["qty_rule"] if item_row["qty_rule"] in {"CUSTOM", "SUGGESTED"} else "CUSTOM",
                )
                db.session.add(reorder_item)

                message_items.append(
                    {"item_name": item.item_name, "qty": item_row["qty"]}
                )

            reorder.total_items = len(message_items)
            reorder.message = _build_message(store_name, supplier.supplier_name, message_items)
            db.session.flush()

            responses.append(
                {
                    "reorder_id": reorder.reorder_id,
                    "supplier_id": supplier.supplier_id,
                    "supplier_name": supplier.supplier_name,
                    "status": reorder.status,
                    "message": reorder.message,
                }
            )

            if trigger_n8n:
                payload = {
                    "reorder_id": reorder.reorder_id,
                    "supplier_id": supplier.supplier_id,
                    "supplier_name": supplier.supplier_name,
                    "supplier_phone": supplier.phone or "",
                    "message": reorder.message,
                    "items": message_items,
                    "source": reorder.source,
                }
                n8n_results.append(
                    {"reorder_id": reorder.reorder_id, "n8n": _trigger_n8n(payload)}
                )

        db.session.commit()
        return jsonify({"status": "success", "reorders": responses, "n8n": n8n_results})

    except Exception as err:
        db.session.rollback()
        return _json_error("Failed to create reorder request", 500, str(err))


@reorders_bp.route("/api/reorders/status", methods=["POST"])
def update_reorder_status():
    data = request.get_json(silent=True) or {}
    reorder_id = data.get("reorder_id")
    status = str(data.get("status", "")).upper()

    if not reorder_id:
        return _json_error("Missing reorder_id", 400)
    if status not in {"SENT", "FAILED", "CONFIRMED"}:
        return _json_error("Invalid status", 400)

    try:
        reorder = ReorderRequest.query.get(int(reorder_id))
    except (ValueError, TypeError):
        reorder = None

    if not reorder:
        return _json_error("Reorder not found", 404)

    reorder.status = status
    reorder.provider_message_id = data.get("provider_message_id") or reorder.provider_message_id
    reorder.error_message = data.get("error_message") or reorder.error_message

    now = datetime.utcnow()
    if status == "SENT":
        reorder.sent_at = now
    if status == "CONFIRMED":
        reorder.confirmed_at = now

    db.session.commit()
    return jsonify({"status": "success"})
