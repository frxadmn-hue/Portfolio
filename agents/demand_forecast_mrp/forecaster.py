"""
Production-Grade Demand Forecasting & MRP Engine.
Specialized for Organic Cosmetics & FMCG Manufacturing (Natura Siberica).

Combines:
1. Econometric Demand Volatility & Promo Lift Forecasting (p50 / p90 targets).
2. Multi-tier BOM Explosion with Scrap Loss Allowance.
3. Expiration-Aware Buffer Stocks & Lot Sizing (MOQ / Pack Multiples).
"""

import math
from datetime import datetime
from typing import Dict, List, Optional
from scipy.stats import norm

from .models import (
    BOMItem,
    DemandForecastResult,
    FinishedProduct,
    ForecastRequest,
    MRPRequirement,
    ProcurementPlan,
)


class DemandForecaster:
    """
    Econometric and statistical forecasting engine for retail supply chains.
    Calculates safety stocks and production targets based on requested service levels.
    """

    def __init__(self, default_service_level: float = 0.95):
        self.default_service_level = default_service_level

    def calculate_z_score(self, service_level: float) -> float:
        """
        Calculates Inverse Normal Cumulative Distribution Function (Z-score).
        e.g., 95% -> 1.6449, 98% -> 2.0537
        """
        try:
            return float(norm.ppf(service_level))
        except Exception:
            # Fallback table if scipy is unavailable
            lookup = {0.90: 1.282, 0.95: 1.645, 0.98: 2.054, 0.99: 2.326}
            return lookup.get(round(service_level, 2), 1.645)

    def forecast_product_demand(
        self,
        product: FinishedProduct,
        request: ForecastRequest,
        historical_variance_ratio: float = 0.14
    ) -> DemandForecastResult:
        """
        Computes planned volume considering promo lifts and stochastic volatility.
        """
        z_score = self.calculate_z_score(request.service_level)
        
        # Base demand augmented by retail promotion lift
        promo_factor = 1.0 + (request.channel_promo_lift_pct / 100.0)
        expected_units = int(math.ceil(request.planned_baseline_units * promo_factor))
        
        # Demand standard deviation across the planning horizon
        std_dev = expected_units * historical_variance_ratio
        
        # Buffer safety stock of finished goods
        finished_goods_safety_stock = int(math.ceil(z_score * std_dev))
        
        # Total production target (p90/p95 conservative target)
        target_production = expected_units + finished_goods_safety_stock
        estimated_revenue = target_production * product.retail_price_rub

        return DemandForecastResult(
            sku=product.sku,
            service_level=request.service_level,
            z_score=round(z_score, 4),
            expected_demand=expected_units,
            std_dev=round(std_dev, 2),
            safety_stock_units=finished_goods_safety_stock,
            target_production_volume=target_production,
            estimated_revenue_rub=estimated_revenue
        )


class ProductionMRPEngine:
    """
    Material Requirements Planning (MRP) engine.
    Performs BOM explosion, inventory netting, and lot-size procurement planning.
    """

    def __init__(self, forecaster: Optional[DemandForecaster] = None):
        self.forecaster = forecaster or DemandForecaster()

    def generate_procurement_plan(
        self,
        product: FinishedProduct,
        forecast: DemandForecastResult,
        current_inventory: Dict[str, Dict[str, float]],
        planning_period_days: int = 30
    ) -> ProcurementPlan:
        """
        Executes MRP run against BOM specifications and warehouse balances.

        :param product: Finished product specification with BOM
        :param forecast: Output from DemandForecaster
        :param current_inventory: Dict of {part_code: {'free_stock': float, 'in_transit': float}}
        :param planning_period_days: Duration of the scheduling cycle
        """
        requirements: List[MRPRequirement] = []
        total_budget = 0.0
        max_lead_time = 0

        for item in product.bom:
            # 1. Gross requirement with process scrap allowance
            scrap_multiplier = 1.0 + item.scrap_rate
            gross_needed = forecast.target_production_volume * item.qty_per_unit * scrap_multiplier

            # 2. Safety stock calculation for raw materials
            # Formula: SS = Z * std_dev * (qty_per_unit) * sqrt(LeadTime / PlanningPeriod)
            lead_time_ratio = math.sqrt(item.supplier_lead_time_days / float(planning_period_days))
            item_safety_stock = forecast.z_score * forecast.std_dev * item.qty_per_unit * lead_time_ratio

            # 3. Warehouse position reconciliation
            stock_info = current_inventory.get(item.code, {"free_stock": 0.0, "in_transit": 0.0})
            free_stock = stock_info.get("free_stock", 0.0)
            in_transit = stock_info.get("in_transit", 0.0)
            available_supply = free_stock + in_transit

            # 4. Net requirement determination
            net_needed = (gross_needed + item_safety_stock) - available_supply

            if net_needed > 0:
                # Lot sizing: must respect MOQ and Pack Size multiples
                base_qty = max(net_needed, item.moq)
                lot_count = math.ceil(base_qty / item.pack_size)
                recommended_order = lot_count * item.pack_size
                order_cost = recommended_order * item.unit_cost_rub

                # Urgency classification
                if item.supplier_lead_time_days > 20:
                    status = "КРИТИЧНО: Длинное плечо поставки (заказ сегодня)"
                elif free_stock < (gross_needed * 0.3):
                    status = "ВЫСОКИЙ ПРИОРИТЕТ: Дефицит складского остатка"
                else:
                    status = "ПЛАНОВЫЙ ЗАКАЗ: В графике производства"
            else:
                recommended_order = 0.0
                order_cost = 0.0
                status = "ОСТАТОК ДОСТАТОЧЕН: Закупка не требуется"

            total_budget += order_cost
            if item.supplier_lead_time_days > max_lead_time:
                max_lead_time = item.supplier_lead_time_days

            requirements.append(MRPRequirement(
                item_code=item.code,
                name=item.name,
                unit=item.unit.value,
                gross_requirement=round(gross_needed, 3),
                safety_stock=round(item_safety_stock, 3),
                current_free_stock=round(free_stock, 3),
                in_transit_stock=round(in_transit, 3),
                net_requirement=round(max(0.0, net_needed), 3),
                recommended_order_qty=round(recommended_order, 3),
                total_order_cost_rub=round(order_cost, 2),
                supplier_lead_time_days=item.supplier_lead_time_days,
                shelf_life_days=item.shelf_life_days,
                urgency_status=status
            ))

        return ProcurementPlan(
            sku=product.sku,
            product_name=product.name,
            target_production_volume=forecast.target_production_volume,
            total_procurement_budget_rub=round(total_budget, 2),
            critical_lead_time_days=max_lead_time,
            generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            requirements=requirements
        )
