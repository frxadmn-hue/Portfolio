"""
Domain Models & DTOs for Legal Risk & Compliance Agent.
Covers Russian Commercial Law (GK RF), TR TS 009/2011, and Federal Law 381-FZ.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class RiskSeverity(str, Enum):
    CRITICAL = "CRITICAL"    # Прямая финансовая угроза или потеря ноу-хау
    HIGH = "HIGH"            # Существенный дисбаланс прав, регуляторный риск
    MEDIUM = "MEDIUM"        # Затягивание оплаты, операционные неудобства
    LOW = "LOW"              # Формальные неточности в формулировках


class RiskCategory(str, Enum):
    PENALTY_DISBALANCE = "Штрафы и неустойки (ст. 330, 333 ГК РФ)"
    IP_RECIPE_EXPROPRIATION = "Права на рецептуру и ноу-хау (ст. 1229, 1465 ГК РФ)"
    REGULATORY_TR_TS_009 = "Регламент косметики (ТР ТС 009/2011 / Честный ЗНАК)"
    PAYMENT_DEFERRAL = "Сверхнормативная отсрочка платежа (ФЗ № 381-ФЗ)"
    UNILATERAL_CHANGES = "Одностороннее изменение условий и цен (ст. 310, 421 ГК РФ)"
    UNSOLD_GOODS_RETURN = "Возврат непроданной продукции (ст. 13 ФЗ № 381-ФЗ)"


class ContractClause(BaseModel):
    clause_id: str = Field(description="Clause reference number, e.g. '5.3'")
    title: str = Field(default="")
    text: str = Field(description="Full verbatim text of the contract clause")


class RiskFinding(BaseModel):
    finding_id: str
    clause_ref: str
    category: RiskCategory
    severity: RiskSeverity
    original_clause_text: str
    statutory_violation: str = Field(description="Articles of Civil Code (GK RF) or Technical Regulations violated")
    risk_impact: str = Field(description="Business and financial consequence for Natura Siberica")
    redline_proposal: str = Field(description="Recommended replacement wording for Protocol of Disagreements")


class ProtocolOfDisagreementsItem(BaseModel):
    item_number: int
    contract_clause_ref: str
    retailer_wording: str
    supplier_counter_wording: str
    legal_rationale: str


class AuditReport(BaseModel):
    contract_title: str
    total_clauses_reviewed: int
    critical_risks_count: int
    high_risks_count: int
    medium_risks_count: int
    overall_verdict: str
    findings: List[RiskFinding]
    protocol_items: List[ProtocolOfDisagreementsItem]
    generated_at: str
