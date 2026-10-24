"""
Natura Siberica Enterprise AI Platform - Core REST API.
Production FastAPI Gateway exposing Demand MRP, Legal Compliance, and Secure On-Premise RAG.
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from pathlib import Path
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from config.settings import get_settings
from agents.demand_forecast_mrp import (
    BOMItem,
    DemandForecaster,
    EconometricDemandForecaster,
    FinishedProduct,
    ForecastRequest,
    InvenTreeClient,
    MRPExcelExporter,
    ProcurementBudgetOptimizer,
    ProcurementPlan,
    ProductionMRPEngine,
)
from agents.demand_forecast_mrp.runner import build_flagship_product
from agents.legal_compliance import (
    AuditReport,
    ContractClause,
    ContractParser,
    LegalDocxExporter,
    LegalComplianceAuditor,
)
from agents.secure_enterprise_rag import (
    DataClassification,
    DepartmentAccess,
    DocumentChunk,
    EnterprisePrivacyGuard,
    SearchResultItem,
    SecureQdrantStore,
)
from agents.secure_enterprise_rag.runner import seed_knowledge_base

# Initialize FastAPI App
app = FastAPI(
    title="Natura Siberica Enterprise AI Platform",
    description=(
        "Production AI Agents for Organic FMCG Manufacturing:\n"
        "1. **Demand Forecasting & InvenTree MRP**: Econometric time-series demand, scrap-adjusted BOM explosion, lot sizing.\n"
        "2. **Legal Risk & Due Diligence**: Automated compliance with GK RF (art. 330, 333, 1465), TR TS 009/2011, and 381-FZ.\n"
        "3. **Secure On-Premise RAG Proxy**: 152-FZ cryptographic PII and secret cosmetic formula sanitization."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singletons
settings = get_settings()
forecaster = DemandForecaster(default_service_level=0.95)
mrp_engine = ProductionMRPEngine(forecaster=forecaster)
inventree = InvenTreeClient()
auditor = LegalComplianceAuditor()
privacy_guard = EnterprisePrivacyGuard()
qdrant_store = SecureQdrantStore()

# Seed default documents on startup
seed_knowledge_base(qdrant_store)

# Global in-memory cache for latest generated reports to serve downloads
LATEST_MRP_PLAN: Optional[ProcurementPlan] = None
LATEST_AUDIT_REPORT: Optional[AuditReport] = None
OUTPUT_DIR = Path("./artifacts_generated")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# --- Schemas ---

class SystemManifest(BaseModel):
    service: str = "Natura Siberica Enterprise AI Core"
    status: str = "OPERATIONAL"
    compliance: str = "152-FZ / 98-FZ On-Premise Localized"
    erp_integration: str = "InvenTree REST API Gateway"
    vector_database: str = "Local Qdrant Daemon (HNSW Cosine)"
    econometrics_framework: str = "MGIMO Time Series (STL + SARIMAX + SciPy Simplex)"
    active_agents: List[str]


class EconometricForecastRequest(BaseModel):
    horizon_weeks: int = Field(default=4, ge=1, le=52)
    promo_discount_pct: float = Field(default=25.0, ge=0.0, le=100.0)


class BudgetOptimizationRequest(BaseModel):
    budget_limit_rub: float = Field(gt=100000.0, description="Available procurement budget in RUB")


class LegalAuditRequest(BaseModel):
    contract_title: str = Field(default="Договор поставки в розничную сеть")
    contract_text: str = Field(description="Raw text of the agreement or clauses")


class RAGSearchRequest(BaseModel):
    query: str
    user_department: DepartmentAccess = DepartmentAccess.RD_LABORATORY
    top_k: int = Field(default=3, ge=1, le=10)


class RAGDeanonymizeRequest(BaseModel):
    sanitized_text: str


# --- Endpoints ---

@app.get("/", response_model=SystemManifest, tags=["System Health"])
def root_manifest():
    return SystemManifest(
        active_agents=[
            "Demand Forecasting & InvenTree MRP Agent",
            "Legal Risk & Contract Compliance Agent (GK RF / TR TS 009)",
            "Secure Enterprise RAG & Cryptographic Privacy Vault (152-FZ)"
        ]
    )


@app.get("/health", tags=["System Health"])
def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}


# --- Agent 1: Demand & MRP Endpoints ---

@app.post("/api/v1/mrp/calculate", response_model=ProcurementPlan, tags=["1. Demand Forecasting & MRP"])
def calculate_mrp(request: ForecastRequest):
    """
    Computes econometric demand forecast and BOM explosion against InvenTree warehouse stock.
    Generates downloadable Excel procurement plan.
    """
    global LATEST_MRP_PLAN
    product = build_flagship_product()
    
    # 1. Forecast
    forecast_res = forecaster.forecast_product_demand(product, request)
    
    # 2. Stock levels from InvenTree
    part_codes = [b.code for b in product.bom]
    stock_levels = inventree.get_stock_levels(part_codes)
    
    # 3. MRP Run
    plan = mrp_engine.generate_procurement_plan(product, forecast_res, stock_levels)
    LATEST_MRP_PLAN = plan
    
    # Pre-generate Excel
    excel_path = OUTPUT_DIR / f"MRP_Plan_{plan.sku}.xlsx"
    MRPExcelExporter.export_to_file(plan, excel_path)
    
    return plan


@app.get("/api/v1/mrp/export-excel", tags=["1. Demand Forecasting & MRP"])
def download_mrp_excel():
    """Downloads the generated Excel procurement plan (.xlsx)."""
    global LATEST_MRP_PLAN
    if not LATEST_MRP_PLAN:
        # Generate default run if not yet executed
        product = build_flagship_product()
        req = ForecastRequest(product_sku=product.sku, planned_baseline_units=50000, channel_promo_lift_pct=25.0)
        LATEST_MRP_PLAN = mrp_engine.generate_procurement_plan(
            product,
            forecaster.forecast_product_demand(product, req),
            inventree.get_stock_levels([b.code for b in product.bom])
        )
    
    excel_path = OUTPUT_DIR / f"MRP_Plan_{LATEST_MRP_PLAN.sku}.xlsx"
    MRPExcelExporter.export_to_file(LATEST_MRP_PLAN, excel_path)
    return FileResponse(
        path=str(excel_path),
        filename=f"MRP_Plan_Natura_Siberica_{LATEST_MRP_PLAN.sku}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.post("/api/v1/mrp/econometric-forecast", tags=["1. Demand Forecasting & MRP"])
def run_econometric_forecast(request: EconometricForecastRequest):
    """
    Executes STL time-series decomposition and SARIMAX econometric modeling (MGIMO standard).
    Quantifies promotional elasticity and forward demand confidence bounds.
    """
    forecaster_ml = EconometricDemandForecaster()
    stl_results = forecaster_ml.decompose_stl()
    sarimax_results = forecaster_ml.forecast_sarimax(
        horizon_weeks=request.horizon_weeks,
        planned_promo_discount_pct=request.promo_discount_pct
    )
    return {
        "framework": "MGIMO Econometrics (Artamonov Time Series Methodology)",
        "stl_decomposition": {
            "trend_direction": stl_results["trend_direction"],
            "seasonal_amplitude_pct": stl_results["seasonal_amplitude_pct"],
        },
        "sarimax_model": sarimax_results
    }


@app.post("/api/v1/mrp/optimize-budget", tags=["1. Demand Forecasting & MRP"])
def optimize_procurement_budget(request: BudgetOptimizationRequest):
    """
    Solves Linear Programming (LP) Simplex optimization via scipy.optimize.linprog.
    Finds mathematically optimal raw material procurement allocation under finance budget caps.
    """
    global LATEST_MRP_PLAN
    if not LATEST_MRP_PLAN:
        product = build_flagship_product()
        req = ForecastRequest(product_sku=product.sku, planned_baseline_units=50000, channel_promo_lift_pct=25.0)
        LATEST_MRP_PLAN = mrp_engine.generate_procurement_plan(
            product,
            forecaster.forecast_product_demand(product, req),
            inventree.get_stock_levels([b.code for b in product.bom])
        )
    
    product = build_flagship_product()
    opt_result = ProcurementBudgetOptimizer.optimize_procurement_under_budget_cap(
        product=product,
        unconstrained_plan=LATEST_MRP_PLAN.requirements,
        budget_cap_rub=request.budget_limit_rub
    )
    return opt_result


# --- Agent 2: Legal Risk & Contract Compliance Endpoints ---

@app.post("/api/v1/legal/audit", response_model=AuditReport, tags=["2. Legal Due Diligence & Compliance"])
def audit_contract_text(request: LegalAuditRequest):
    """
    Audits contract text for abusive penalty clauses, recipe expropriation, and TR TS 009/2011 compliance.
    Generates downloadable Redline Protocol of Disagreements (.docx).
    """
    global LATEST_AUDIT_REPORT
    clauses = ContractParser.from_text(request.contract_text)
    if not clauses:
        raise HTTPException(status_code=400, detail="No readable numbered clauses detected in contract text.")
    
    report = auditor.audit_clauses(clauses, request.contract_title)
    LATEST_AUDIT_REPORT = report

    # Pre-generate Word document
    docx_path = OUTPUT_DIR / "Protocol_of_Disagreements.docx"
    LegalDocxExporter.export_protocol_to_docx(report, docx_path)

    return report


@app.get("/api/v1/legal/export-docx", tags=["2. Legal Due Diligence & Compliance"])
def download_protocol_docx():
    """Downloads the official Protocol of Disagreements (.docx)."""
    global LATEST_AUDIT_REPORT
    if not LATEST_AUDIT_REPORT:
        from agents.legal_compliance.runner import SAMPLE_PREDATORY_CONTRACT
        clauses = ContractParser.from_text(SAMPLE_PREDATORY_CONTRACT)
        LATEST_AUDIT_REPORT = auditor.audit_clauses(clauses, "Типовой Договор Поставки (Оферта Ритейлера)")
    
    docx_path = OUTPUT_DIR / "Protocol_of_Disagreements_Natura_Siberica.docx"
    LegalDocxExporter.export_protocol_to_docx(LATEST_AUDIT_REPORT, docx_path)
    return FileResponse(
        path=str(docx_path),
        filename="Протокол_разногласий_Натура_Сиберика.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


# --- Agent 3: Secure Enterprise RAG & PII Sanitizer Endpoints ---

@app.post("/api/v1/rag/search", tags=["3. Secure RAG & 152-FZ Privacy"])
def search_knowledge_base(request: RAGSearchRequest):
    """
    Searches on-premise Qdrant collection with RBAC department isolation.
    Returns sanitized text safe for external LLM transmission (zero PII/formula leakage).
    """
    results = qdrant_store.search_with_rbac(
        query=request.query,
        user_dept=request.user_department,
        top_k=request.top_k
    )

    sanitized_results = []
    for r in results:
        sanitized_txt, tokens, has_pii, has_formula = privacy_guard.sanitize_text(r.text_snippet)
        sanitized_results.append({
            "chunk_id": r.chunk_id,
            "title": r.title,
            "relevance_score": r.score,
            "department": r.department,
            "classification": r.classification,
            "sanitized_for_external_llm": sanitized_txt,
            "entities_shielded_count": len(tokens),
            "pii_detected": has_pii,
            "proprietary_formula_detected": has_formula
        })

    return {
        "query": request.query,
        "requesting_department": request.user_department.value,
        "hits_count": len(sanitized_results),
        "results": sanitized_results
    }


@app.post("/api/v1/rag/deanonymize", tags=["3. Secure RAG & 152-FZ Privacy"])
def deanonymize_within_perimeter(request: RAGDeanonymizeRequest):
    """
    On-premise authorized endpoint: restores original cleartext from encrypted tokens.
    """
    restored = privacy_guard.restore_tokens(request.sanitized_text)
    return {
        "original_cleartext": restored,
        "status": "DECRYPTION_SUCCESSFUL_WITHIN_SECURE_PERIMETER"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
