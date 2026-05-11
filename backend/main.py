from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from modules.billing import router as billing_router
from modules.inventory import router as inventory_router
from modules.supplier import router as supplier_router
from modules.crm import router as crm_router
from modules.reports import router as reports_router
from modules.security import router as security_router

app = FastAPI(title="Selvam Medicals ERP", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(billing_router, prefix="/api/billing", tags=["Billing"])
app.include_router(inventory_router, prefix="/api/inventory", tags=["Inventory"])
app.include_router(supplier_router, prefix="/api/supplier", tags=["Supplier"])
app.include_router(crm_router, prefix="/api/crm", tags=["CRM"])
app.include_router(reports_router, prefix="/api/reports", tags=["Reports"])
app.include_router(security_router, prefix="/api/security", tags=["Security"])

@app.get("/")
def root():
    return {"message": "Selvam Medicals API Running"}
