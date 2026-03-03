"""
Distributor Auto-Order Automation
Automatically sends purchase orders to distributors via Email / WhatsApp
when stock hits the reorder level.
"""
import schedule, time, smtplib, httpx
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend"))

from database import SessionLocal
from models.medicine import Medicine
from config import settings

def get_low_stock_items():
    db = SessionLocal()
    items = db.query(Medicine).filter(Medicine.stock_qty <= Medicine.reorder_level, Medicine.is_active == True).all()
    db.close()
    return items

def send_email_order(supplier_email: str, items: list):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Purchase Order Request — {datetime.now().strftime('%d/%m/%Y')}"
    msg["From"] = settings.SMTP_USER
    msg["To"] = supplier_email

    html_rows = "".join(f"<tr><td>{i.name}</td><td>{i.batch_no}</td><td>{i.reorder_qty}</td></tr>" for i in items)
    html_body = f"""
    <html><body>
    <h2>Selvam Medicals — Automatic Purchase Order</h2>
    <p>Please arrange the following medicines at your earliest convenience:</p>
    <table border="1" cellpadding="6">
      <tr><th>Medicine Name</th><th>Batch</th><th>Qty Required</th></tr>
      {html_rows}
    </table>
    <br><p>This is an auto-generated order. Contact us for any clarification.</p>
    <p><b>{settings.SHOP_NAME}</b><br>{settings.SHOP_PHONE}</p>
    </body></html>"""

    msg.attach(MIMEText(html_body, "html"))
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.sendmail(settings.SMTP_USER, supplier_email, msg.as_string())
        print(f"[AUTO-ORDER] Email sent to {supplier_email}")
    except Exception as e:
        print(f"[AUTO-ORDER] Email failed: {e}")

def send_whatsapp_order(phone: str, items: list):
    """Send WhatsApp message via Twilio"""
    item_list = "\n".join(f"• {i.name} x {i.reorder_qty}" for i in items)
    message = f"*{settings.SHOP_NAME} — Purchase Order*\nDate: {datetime.now().strftime('%d/%m/%Y')}\n\n{item_list}\n\nPlease confirm availability."
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_SID, settings.TWILIO_TOKEN)
        client.messages.create(from_=f"whatsapp:{settings.TWILIO_FROM}", to=f"whatsapp:{phone}", body=message)
        print(f"[AUTO-ORDER] WhatsApp sent to {phone}")
    except Exception as e:
        print(f"[AUTO-ORDER] WhatsApp failed: {e}")

def run_auto_order():
    print(f"[{datetime.now()}] Running auto-reorder check...")
    low_items = get_low_stock_items()
    if not low_items:
        print("[AUTO-ORDER] All stock levels OK. No orders needed.")
        return
    print(f"[AUTO-ORDER] Found {len(low_items)} items to reorder.")
    # Group by supplier and send individual orders
    # For demo: send all to a single configured email
    if settings.SMTP_USER:
        send_email_order(settings.SMTP_USER, low_items)

# Schedule: runs every day at 8:00 AM
schedule.every().day.at("08:00").do(run_auto_order)

if __name__ == "__main__":
    print("Selvam Medicals — Auto-Order Daemon Started")
    run_auto_order()  # Run once on startup
    while True:
        schedule.run_pending()
        time.sleep(60)
