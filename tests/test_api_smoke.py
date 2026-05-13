from __future__ import annotations

from datetime import datetime
from uuid import uuid4


def unique_id(prefix: str, length: int = 8) -> str:
    return f"{prefix}{uuid4().hex[:length]}"


def get_json(response):
    payload = response.get_json(silent=True)
    assert payload is not None, response.data.decode("utf-8", errors="replace")
    return payload


def find_item(items, key: str, value):
    for item in items:
        if item.get(key) == value:
            return item
    return None


def test_core_endpoints(client):
    health = client.get("/api/health")
    assert health.status_code == 200
    health_body = get_json(health)
    assert health_body["status"] == "ok"
    assert health_body["database"] == "postgres"
    assert "medicines" in health_body
    assert "bills" in health_body

    backup = client.get("/api/backup")
    assert backup.status_code == 410
    backup_body = get_json(backup)
    assert backup_body["status"] == "error"


def test_inventory_smoke(client):
    medicine_id = unique_id("m", 9)
    medicine_name = f"Smoke Medicine {medicine_id[-4:]}"
    shelf_name = f"SMK{unique_id('', 7)}"

    shelf_create = client.post(
        "/api/shelves",
        json={"name": shelf_name, "status": "Active"},
    )
    assert shelf_create.status_code == 200
    assert get_json(shelf_create)["status"] == "success"

    medicines_before = client.get("/api/medicines")
    assert medicines_before.status_code == 200
    assert isinstance(get_json(medicines_before), list)

    medicine_create = client.post(
        "/api/medicines",
        json={
            "id": medicine_id,
            "n": medicine_name,
            "g": "Paracetamol",
            "c": "Tablet",
            "p": 30,
            "s": 50,
            "batch": "B101",
            "expiry": "2027-12-31",
            "p_rate": 20,
            "p_packing": "1x10",
            "s_packing": "1x10",
            "p_gst": 5,
            "s_gst": 5,
            "disc": 0,
            "offer": "",
            "reorder": 10,
            "max_qty": 200,
            "shelf_id": shelf_name[:10].upper().replace(" ", "_"),
        },
    )
    assert medicine_create.status_code == 200
    assert get_json(medicine_create)["status"] == "success"

    medicines_after = client.get("/api/medicines")
    assert medicines_after.status_code == 200
    medicine_list = get_json(medicines_after)
    created_medicine = find_item(medicine_list, "id", medicine_id)
    assert created_medicine is not None
    assert created_medicine["n"] == medicine_name

    alerts = client.get("/api/medicines/alerts?low_stock=15&expiry_days=90")
    assert alerts.status_code == 200
    alerts_body = get_json(alerts)
    assert "low_stock" in alerts_body
    assert "expiring_soon" in alerts_body

    shelves = client.get("/api/shelves")
    assert shelves.status_code == 200
    shelf_list = get_json(shelves)
    created_shelf = find_item(shelf_list, "name", shelf_name)
    assert created_shelf is not None

    shelf_delete = client.delete(f"/api/shelves/{created_shelf['id']}")
    assert shelf_delete.status_code == 200
    assert get_json(shelf_delete)["status"] == "success"

    medicine_delete = client.delete(f"/api/medicines/{medicine_id}")
    assert medicine_delete.status_code == 200
    assert get_json(medicine_delete)["status"] == "success"


def test_bill_lifecycle(client):
    medicine_id = unique_id("m", 9)
    medicine_name = f"Bill Medicine {medicine_id[-4:]}"

    medicine_create = client.post(
        "/api/medicines",
        json={
            "id": medicine_id,
            "n": medicine_name,
            "g": "Paracetamol",
            "c": "Tablet",
            "p": 30,
            "s": 25,
            "batch": "B102",
            "expiry": "2027-12-31",
            "p_rate": 18,
            "p_packing": "1x10",
            "s_packing": "1x10",
            "p_gst": 5,
            "s_gst": 5,
            "disc": 0,
            "offer": "",
            "reorder": 10,
            "max_qty": 200,
            "shelf_id": "MAIN",
        },
    )
    assert medicine_create.status_code == 200

    bill_create = client.post(
        "/api/bills",
        json={
            "cust": "Walk-in",
            "phone": "",
            "pay": "cash",
            "sub": 60,
            "disc": 0,
            "tax": 3,
            "total": 63,
            "doctor": "Self",
            "items": [
                {
                    "id": medicine_id,
                    "n": medicine_name,
                    "p": 30,
                    "qty": 2,
                }
            ],
        },
    )
    assert bill_create.status_code == 200
    bill_body = get_json(bill_create)
    assert bill_body["status"] == "success"
    bill_id = bill_body["id"]

    bill_get = client.get(f"/api/bills/{bill_id}")
    assert bill_get.status_code == 200
    bill_get_body = get_json(bill_get)
    assert bill_get_body["id"] == bill_id
    assert isinstance(bill_get_body["items"], list)

    bill_update = client.patch(
        f"/api/bills/{bill_id}",
        json={"sub": 70, "disc": 2, "tax": 3.4, "total": 71.4},
    )
    assert bill_update.status_code == 200
    updated_bill = get_json(bill_update)
    assert updated_bill["id"] == bill_id

    gst_report = client.get("/api/reports/gst")
    assert gst_report.status_code == 200
    gst_body = get_json(gst_report)
    assert "total_sales" in gst_body
    assert "net_revenue" in gst_body

    bill_delete = client.delete(f"/api/bills/{bill_id}")
    assert bill_delete.status_code == 200
    assert get_json(bill_delete)["status"] == "success"


def test_billing_mockup_backends(client):
    medicine_id = unique_id("m", 9)
    medicine_name = f"Cancel Medicine {medicine_id[-4:]}"

    med_create = client.post(
        "/api/medicines",
        json={
            "id": medicine_id,
            "n": medicine_name,
            "g": "Paracetamol",
            "c": "Tablet",
            "p": 55,
            "s": 40,
            "batch": "B220",
            "expiry": "2027-12-31",
            "p_rate": 33,
            "p_packing": "1x10",
            "s_packing": "1x10",
            "p_gst": 5,
            "s_gst": 5,
            "disc": 0,
            "offer": "",
            "reorder": 10,
            "max_qty": 200,
            "shelf_id": "MAIN",
        },
    )
    assert med_create.status_code == 200

    bill_create = client.post(
        "/api/bills",
        json={
            "cust": "Cancel Flow Customer",
            "phone": "9000000010",
            "pay": "cash",
            "sub": 110,
            "disc": 0,
            "tax": 5.5,
            "total": 115.5,
            "doctor": "Self",
            "items": [{"id": medicine_id, "n": medicine_name, "p": 55, "qty": 2}],
        },
    )
    assert bill_create.status_code == 200
    bill_id = get_json(bill_create)["id"]

    debit_note = client.post(
        "/api/billing/vouchers",
        json={
            "type": "debit_note",
            "voucher_no": unique_id("DN-", 6),
            "voucher_date": "2026-05-12",
            "customer_code": "1",
            "amount": 150.75,
            "remarks": "Damage adjustment",
        },
    )
    assert debit_note.status_code == 200
    debit_note_body = get_json(debit_note)
    assert debit_note_body["status"] == "success"
    assert debit_note_body["voucher"]["type"] == "debit_note"

    receipt_credit = client.post(
        "/api/billing/vouchers",
        json={
            "type": "sales_receipt_credit",
            "voucher_no": unique_id("RC-", 6),
            "voucher_date": "2026-05-12",
            "account_date": "2026-05-12",
            "reference_no": "REF-01",
            "linked_bill_id": bill_id,
            "account_name": "Customer Receipt",
            "party_name": "Cancel Flow Customer",
            "payment_type": "cash",
            "amount": 115.5,
            "remarks": "Receipt against bill",
        },
    )
    assert receipt_credit.status_code == 200
    receipt_credit_body = get_json(receipt_credit)
    assert receipt_credit_body["voucher"]["type"] == "sales_receipt_credit"

    voucher_list = client.get("/api/billing/vouchers?type=debit_note")
    assert voucher_list.status_code == 200
    assert isinstance(get_json(voucher_list), list)

    cancel_preview = client.get(f"/api/bills/{bill_id}/cancel-preview")
    assert cancel_preview.status_code == 200
    cancel_preview_body = get_json(cancel_preview)
    assert cancel_preview_body["id"] == bill_id
    assert isinstance(cancel_preview_body["items"], list)
    assert cancel_preview_body["items"][0]["item_code"] == medicine_id

    cancel_bill = client.post(
        f"/api/bills/{bill_id}/cancel",
        json={"reason": "Customer requested void"},
    )
    assert cancel_bill.status_code == 200
    cancel_bill_body = get_json(cancel_bill)
    assert cancel_bill_body["status"] == "success"
    assert cancel_bill_body["id"] == bill_id


def test_customer_family_account_flow(client):
    family_head_name = f"Family Head {unique_id('', 6)}"
    family_member_name = f"Family Member {unique_id('', 6)}"

    head_create = client.post(
        "/api/customers",
        json={
            "name": family_head_name,
            "phone": "9000000101",
            "address": "Main Home",
        },
    )
    assert head_create.status_code == 200

    member_create = client.post(
        "/api/customers",
        json={
            "name": family_member_name,
            "phone": "9000000102",
            "address": "Main Home",
        },
    )
    assert member_create.status_code == 200

    customer_list = get_json(client.get("/api/customers"))
    head = find_item(customer_list, "name", family_head_name)
    member = find_item(customer_list, "name", family_member_name)
    assert head is not None
    assert member is not None

    link_member = client.post(
        "/api/customers",
        json={
            "id": member["id"],
            "name": family_member_name,
            "phone": "9000000102",
            "address": "Main Home",
            "family_head_id": head["id"],
            "family_relation": "Child",
        },
    )
    assert link_member.status_code == 200

    customer_list = get_json(client.get("/api/customers"))
    head = find_item(customer_list, "name", family_head_name)
    member = find_item(customer_list, "name", family_member_name)
    assert head["family_head_id"] == head["id"]
    assert member["family_head_id"] == head["id"]
    assert head["family_member_count"] == 2
    assert member["family_member_count"] == 2

    medicine_id = unique_id("m", 9)
    medicine_name = f"Family Medicine {medicine_id[-4:]}"

    med_create = client.post(
        "/api/medicines",
        json={
            "id": medicine_id,
            "n": medicine_name,
            "g": "Paracetamol",
            "c": "Tablet",
            "p": 50,
            "s": 40,
            "batch": "FAM100",
            "expiry": "2027-12-31",
            "p_rate": 30,
            "p_packing": "1x10",
            "s_packing": "1x10",
            "p_gst": 5,
            "s_gst": 5,
            "disc": 0,
            "offer": "",
            "reorder": 10,
            "max_qty": 200,
            "shelf_id": "MAIN",
        },
    )
    assert med_create.status_code == 200

    bill_create = client.post(
        "/api/bills",
        json={
            "cust": family_member_name,
            "phone": "9000000102",
            "pay": "cash",
            "sub": 100,
            "disc": 0,
            "tax": 0,
            "total": 100,
            "doctor": "Self",
            "items": [{"id": medicine_id, "n": medicine_name, "p": 50, "qty": 2}],
        },
    )
    assert bill_create.status_code == 200
    bill_id = get_json(bill_create)["id"]

    payment = client.post(
        f"/api/customers/{head['id']}/payment",
        json={"amount": 30, "description": "Family payment"},
    )
    assert payment.status_code == 200

    family_ledger = client.get(f"/api/customers/{head['id']}/ledger")
    assert family_ledger.status_code == 200
    ledger_rows = get_json(family_ledger)
    assert len(ledger_rows) >= 2
    assert any(row["ref_id"] == bill_id for row in ledger_rows)
    assert any("Family payment" in row["description"] for row in ledger_rows)
    assert ledger_rows[-1]["balance"] == 70.0

    family_summary = client.get(f"/api/customers/{head['id']}/family")
    assert family_summary.status_code == 200
    family_summary_body = get_json(family_summary)
    assert family_summary_body["family_member_count"] == 2
    assert family_summary_body["summary"]["balance"] == 70.0


def test_finance_accounting_apis(client):
    supplier_name = f"Finance Supplier {unique_id('', 6)}"
    purchase_response = client.post(
        "/api/purchases",
        json={
            "supplier": supplier_name,
            "amount": 480.0,
            "date": "13/05/2026",
            "items": "Finance Item",
            "batch": "FIN100",
            "expiry": "2027-12-31",
        },
    )
    assert purchase_response.status_code == 200

    supplier_list = get_json(client.get("/api/suppliers"))
    supplier = find_item(supplier_list, "name", supplier_name)
    assert supplier is not None

    expense_response = client.post(
        "/api/finance/expenses",
        json={
            "expense_date": "2026-05-13",
            "category": "Rent",
            "amount": 2500.0,
            "description": "Monthly shop rent",
            "voucher_no": "EXP-001",
            "is_gst_applicable": False,
        },
    )
    assert expense_response.status_code == 200
    expense_body = get_json(expense_response)
    assert expense_body["status"] == "success"

    summary = get_json(client.get("/api/finance/summary?start_date=2026-05-01&end_date=2026-05-31"))
    assert "sales_total" in summary
    assert "expense_total" in summary
    assert "gross_profit" in summary
    assert "net_profit" in summary
    assert "daily_sales" in summary

    daily_sales = get_json(client.get("/api/finance/daily-sales?start_date=2026-05-01&end_date=2026-05-31"))
    assert isinstance(daily_sales, list)

    profit_loss = get_json(client.get("/api/finance/profit-loss?start_date=2026-05-01&end_date=2026-05-31"))
    assert "gross_profit" in profit_loss
    assert "net_profit" in profit_loss

    payables = get_json(client.get("/api/finance/supplier-payables?start_date=2026-05-01&end_date=2026-05-31"))
    assert isinstance(payables, list)
    assert any(row["supplier_name"] == supplier_name for row in payables)

    payment_response = client.post(
        "/api/finance/supplier-payments",
        json={
            "supplier_id": supplier["id"],
            "amount": 50.0,
            "payment_date": "2026-05-13",
            "remarks": "Partial payment",
        },
    )
    assert payment_response.status_code == 200
    payment_body = get_json(payment_response)
    assert payment_body["status"] == "success"


def test_purchases_and_masters_smoke(client):
    supplier_name = f"Smoke Supplier {unique_id('', 6)}"
    customer_name = f"Smoke Customer {unique_id('', 6)}"
    doctor_name = f"Dr Smoke {unique_id('', 4)}"
    medicine_id = unique_id("m", 9)
    medicine_name = f"Purchase Medicine {medicine_id[-4:]}"

    client.post(
        "/api/medicines",
        json={
            "id": medicine_id,
            "n": medicine_name,
            "g": "Paracetamol",
            "c": "Tablet",
            "p": 30,
            "s": 20,
            "batch": "B103",
            "expiry": "2027-12-31",
            "p_rate": 18,
            "p_packing": "1x10",
            "s_packing": "1x10",
            "p_gst": 5,
            "s_gst": 5,
            "disc": 0,
            "offer": "",
            "reorder": 10,
            "max_qty": 200,
            "shelf_id": "MAIN",
        },
    )

    supplier_create = client.post(
        "/api/suppliers",
        json={"name": supplier_name, "phone": "9000000001", "gst": "", "status": "Active"},
    )
    assert supplier_create.status_code == 200
    assert get_json(supplier_create)["status"] == "success"

    supplier_list = get_json(client.get("/api/suppliers"))
    supplier_row = find_item(supplier_list, "name", supplier_name)
    assert supplier_row is not None
    supplier_id = supplier_row["id"]

    customer_create = client.post(
        "/api/customers",
        json={"name": customer_name, "phone": "9000000002", "address": "Sample Address", "balance": 100},
    )
    assert customer_create.status_code == 200
    assert get_json(customer_create)["status"] == "success"

    customer_list = get_json(client.get("/api/customers"))
    customer_row = find_item(customer_list, "name", customer_name)
    assert customer_row is not None
    customer_id = customer_row["id"]

    doctor_create = client.post(
        "/api/doctors",
        json={"name": doctor_name, "specialty": "General", "hospital": "Smoke Hospital", "phone": "9000000003"},
    )
    assert doctor_create.status_code == 200
    assert get_json(doctor_create)["status"] == "success"

    doctor_list = get_json(client.get("/api/doctors"))
    doctor_row = find_item(doctor_list, "name", doctor_name)
    assert doctor_row is not None
    doctor_id = doctor_row["id"]

    purchase_create = client.post(
        "/api/purchases",
        json={
            "id": f"P-{int(uuid4().hex[:6], 16)}",
            "supplier": supplier_name,
            "items": medicine_name,
            "amount": 1000,
            "date": datetime.utcnow().strftime("%d/%m/%Y"),
            "status": "Received",
            "batch": "B103",
            "expiry": "2027-12-31",
            "photo": "",
        },
    )
    assert purchase_create.status_code == 200
    assert get_json(purchase_create)["status"] == "success"

    purchases = get_json(client.get("/api/purchases"))
    assert isinstance(purchases, list)
    assert find_item(purchases, "supplier", supplier_name) is not None

    customer_ledger = client.get(f"/api/customers/{customer_id}/ledger")
    assert customer_ledger.status_code == 200
    assert isinstance(get_json(customer_ledger), list)

    payment = client.post(
        f"/api/customers/{customer_id}/payment",
        json={"amount": 25, "description": "Smoke payment"},
    )
    assert payment.status_code == 200
    payment_body = get_json(payment)
    assert payment_body["status"] == "success"
    assert "new_balance" in payment_body

    doctor_delete = client.delete(f"/api/doctors/{doctor_id}")
    assert doctor_delete.status_code == 200


def test_communications_and_sms_smoke(client):
    comm_name = f"Comm Template {unique_id('', 6)}"
    sms_name = f"SMS Template {unique_id('', 6)}"
    message_id = unique_id("sms-", 8)

    comm_list = client.get("/api/communications/templates")
    assert comm_list.status_code == 200
    assert isinstance(get_json(comm_list), list)

    comm_create = client.post(
        "/api/communications/templates",
        json={"name": comm_name, "content": "Hello {{customer_name}}", "is_active": 1},
    )
    assert comm_create.status_code == 200
    comm_body = get_json(comm_create)
    assert comm_body["status"] == "success"
    comm_id = comm_body["id"]

    comm_update = client.put(
        f"/api/communications/templates/{comm_id}",
        json={"name": f"{comm_name} Updated", "content": "Updated content", "is_active": 1},
    )
    assert comm_update.status_code == 200
    assert get_json(comm_update)["status"] == "success"

    comm_logs = client.get("/api/communications/logs")
    assert comm_logs.status_code == 200
    assert isinstance(get_json(comm_logs), list)

    comm_delete = client.delete(f"/api/communications/templates/{comm_id}")
    assert comm_delete.status_code == 200
    assert get_json(comm_delete)["status"] == "success"

    sms_templates = client.get("/api/sms/templates")
    assert sms_templates.status_code == 200
    assert isinstance(get_json(sms_templates), list)

    sms_template_create = client.post(
        "/api/sms/templates",
        json={
            "id": sms_name,
            "name": sms_name,
            "body": "Hello {customer_name}, your bill is ready.",
            "message_type": "custom",
            "active": True,
        },
    )
    assert sms_template_create.status_code == 201
    sms_template_body = get_json(sms_template_create)
    assert sms_template_body["id"] == sms_name

    sms_template_update = client.patch(
        f"/api/sms/templates/{sms_name}",
        json={"name": f"{sms_name} Updated", "body": "Updated body", "active": True},
    )
    assert sms_template_update.status_code == 200
    assert get_json(sms_template_update)["id"] == sms_name

    sms_message_create = client.post(
        "/api/sms/messages",
        json={
            "id": message_id,
            "recipient_phone": "9000000002",
            "customer_id": "1",
            "customer_name": "Smoke Customer",
            "bill_id": "1",
            "template_id": sms_name,
            "auto_send": False,
            "body": "Test SMS body",
        },
    )
    assert sms_message_create.status_code == 201
    sms_message_body = get_json(sms_message_create)
    assert sms_message_body["id"] == message_id
    assert sms_message_body["send_status"] == "queued"

    sms_messages = client.get("/api/sms/messages")
    assert sms_messages.status_code == 200
    sms_message_list = get_json(sms_messages)
    assert find_item(sms_message_list, "id", message_id) is not None

    sms_message_update = client.patch(
        f"/api/sms/messages/{message_id}",
        json={"body": "Updated SMS body", "send_status": "queued"},
    )
    assert sms_message_update.status_code == 200
    assert get_json(sms_message_update)["id"] == message_id

    sms_message_retry = client.post(f"/api/sms/messages/{message_id}/retry")
    assert sms_message_retry.status_code == 200
    assert get_json(sms_message_retry)["id"] == message_id

    sms_message_send = client.post(f"/api/sms/messages/{message_id}/send")
    assert sms_message_send.status_code == 200
    assert get_json(sms_message_send)["id"] == message_id

    sms_by_customer = client.get("/api/sms/messages/by-customer/1")
    assert sms_by_customer.status_code == 200
    assert isinstance(get_json(sms_by_customer), list)

    sms_by_bill = client.get("/api/sms/messages/by-bill/1")
    assert sms_by_bill.status_code == 200
    assert isinstance(get_json(sms_by_bill), list)

    sms_template_delete = client.delete(f"/api/sms/templates/{sms_name}")
    assert sms_template_delete.status_code == 200
    assert get_json(sms_template_delete)["status"] == "success"
