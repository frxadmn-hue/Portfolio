"""
Data Transfer Objects & Domain Models for Demand Forecasting & InvenTree MRP.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, computed_field


class UnitOfMeasure(str, Enum):
    KG = "kg"
    GRAM = "g"
    LITER = "L"
    ML = "ml"
    PCS = "pcs"


class IngredientCategory(str, Enum):
    WILD_HARVEST_EXTRACT = "wild_harvest_extract"
    ORGANIC_OIL = "organic_oil"
    SURFACTANT_BASE = "surfactant_base"
    PRESERVATIVE_ACTIVE = "preservative_active"
    PRIMARY_PACKAGING = "primary_packaging"
    SECONDARY_PACKAGING = "secondary_packaging"


class BOMItem(BaseModel):
    code: str = Field(description="Unique SKU or part identifier in InvenTree")
    name: str = Field(description="Commercial or botanical name")
    category: IngredientCategory
    unit: UnitOfMeasure
    qty_per_unit: float = Field(gt=0, description="Gross quantity required per 1 finished unit")
    scrap_rate: float = Field(default=0.02, ge=0.0, le=0.20, description="Process loss scrap rate (e.g., 2%)")
    supplier_lead_time_days: int = Field(ge=1, description="Replenishment lead time in calendar days")
    moq: float = Field(gt=0, description="Minimum Order Quantity imposed by supplier")
    pack_size: float = Field(gt=0, description="Standard supplier packaging unit (lot size)")
    shelf_life_days: int = Field(ge=30, description="Maximum shelf life of raw material in days")
    unit_cost_rub: float = Field(gt=0, description="Unit acquisition cost in RUB excluding VAT")
    storage_temp_celsius: Optional[str] = Field(default="15-25C", description="Storage temperature conditions")


class FinishedProduct(BaseModel):
    sku: str = Field(description="Product SKU (e.g. NS-SHMP-OBL-400)")
    name: str = Field(description="Commercial brand name")
    category: str = Field(default="Hair Care / Shampoo")
    retail_price_rub: float = Field(gt=0, description="Target retail price")
    bom: List[BOMItem] = Field(description="Multi-tier bill of materials specification")


class SalesHistoryPoint(BaseModel):
    period_start: str = Field(description="ISO Date YYYY-MM-DD")
    units_sold: int = Field(ge=0)
    promo_discount_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    retail_channel: str = Field(default="Federal Chains")


class ForecastRequest(BaseModel):
    product_sku: str
    target_period_days: int = Field(default=30, ge=7, le=365)
    planned_baseline_units: int = Field(gt=0)
    channel_promo_lift_pct: float = Field(default=0.0, ge=0.0, le=300.0)
    service_level: float = Field(default=0.95, ge=0.80, le=0.999, description="Target fulfillment rate (e.g. 95%)")


class DemandForecastResult(BaseModel):
    sku: str
    service_level: float
    z_score: float
    expected_demand: int = Field(description="Mean expected sales (p50)")
    std_dev: float = Field(description="Calculated demand volatility standard deviation")
    safety_stock_units: int = Field(description="Required finished goods buffer")
    target_production_volume: int = Field(description="p90 / p95 conservative target volume for plant")
    estimated_revenue_rub: float


class MRPRequirement(BaseModel):
    item_code: str
    name: str
    unit: str
    gross_requirement: float
    safety_stock: float
    current_free_stock: float
    in_transit_stock: float
    net_requirement: float
    recommended_order_qty: float
    total_order_cost_rub: float
    supplier_lead_time_days: int
    shelf_life_days: int
    urgency_status: str
    inventree_part_id: Optional[int] = None


class ProcurementPlan(BaseModel):
    sku: str
    product_name: str
    target_production_volume: int
    total_procurement_budget_rub: float
    critical_lead_time_days: int
    generated_at: str
    requirements: List[MRPRequirement]
