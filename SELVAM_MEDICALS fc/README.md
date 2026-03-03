# 💊 Selvam Medicals — Medical Shop Management System

A full-stack AI-powered medical shop ERP with billing, inventory, CRM, face recognition, and automated reordering.

## 🏗️ Tech Stack
- **Backend**: FastAPI (Python) + SQLAlchemy + SQLite/PostgreSQL
- **Frontend**: Vanilla HTML/CSS/JS
- **AI/ML**: OpenCV, DeepFace, Tesseract OCR, YOLOv8
- **Automation**: Celery + Schedule + Twilio

## 🚀 Quick Start

### 1. Install dependencies
```bash
cd SELVAM_MEDICALS/backend
pip install -r ../requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Start the backend
```bash
cd backend
python main.py
# OR
uvicorn main:app --reload --port 8000
```

### 4. Open the frontend
```bash
# Open in browser:
frontend/index.html
```

## 📋 Modules

| Module | Description |
|--------|-------------|
| 🧾 Billing | GST invoicing, multi-payment modes |
| 📦 Inventory | Stock management, expiry alerts, barcode |
| 🤝 Supplier | Supplier management, purchase orders |
| 👥 CRM | Customer profiles, loyalty points, purchase history |
| 📊 Reports | Daily/monthly sales, GST reports, top medicines |
| 🤖 ML Engine | Demand forecasting, smart reorder suggestions |
| 📷 AI Camera | Face recognition, prescription OCR, strip detection |
| 🔄 Reorder Engine | Auto-triggered purchase orders |
| 💰 Commission | Staff sales tracking & commission calculation |
| 🔐 Security | JWT auth, role-based access (Admin/Pharmacist/Cashier) |

## 🔒 Default Roles
- **admin** — Full access
- **pharmacist** — Billing + Inventory + Reports
- **cashier** — Billing only

## 📁 Project Structure
```
SELVAM_MEDICALS/
├── backend/         FastAPI application
│   ├── modules/     Feature modules (billing, inventory, etc.)
│   └── models/      SQLAlchemy database models
├── frontend/        HTML/CSS/JS UI
├── ai_models/       Face recognition, OCR, strip detection
├── automation/      Auto-order daemon
└── reports_output/  Generated reports
```
