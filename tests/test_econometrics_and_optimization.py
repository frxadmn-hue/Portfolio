"""
Unit tests for Econometric Forecasting (STL / SARIMAX) and LP Simplex Optimization.
"""

import unittest
from agents.demand_forecast_mrp.models import BOMItem, FinishedProduct, IngredientCategory, MRPRequirement, UnitOfMeasure
from agents.demand_forecast_mrp.econometric_engine import EconometricDemandForecaster, ProcurementBudgetOptimizer


class TestEconometricsAndOptimization(unittest.TestCase):
    def setUp(self):
        self.forecaster = EconometricDemandForecaster()

    def test_stl_decomposition(self):
        res = self.forecaster.decompose_stl(period=12)
        self.assertIn("trend", res)
        self.assertIn("seasonal", res)
        self.assertIn("residual", res)
        self.assertEqual(res["trend_direction"], "GROWING")
        self.assertGreater(res["seasonal_amplitude_pct"], 0.0)

    def test_sarimax_forecast(self):
        res = self.forecaster.forecast_sarimax(horizon_weeks=4, planned_promo_discount_pct=20.0)
        self.assertEqual(res["horizon_weeks"], 4)
        self.assertEqual(len(res["weekly_forecast"]), 4)
        self.assertGreater(res["total_expected_demand"], 1000)
        self.assertGreater(res["conservative_p95_demand"], res["total_expected_demand"])

    def test_procurement_budget_simplex_optimizer(self):
        bom_item = BOMItem(
            code="ING-TEST",
            name="Test Extract",
            category=IngredientCategory.WILD_HARVEST_EXTRACT,
            unit=UnitOfMeasure.KG,
            qty_per_unit=0.02,
            supplier_lead_time_days=10,
            moq=10.0,
            pack_size=5.0,
            shelf_life_days=365,
            unit_cost_rub=1000.0
        )
        prod = FinishedProduct(sku="NS-OPT", name="Opt Shampoo", retail_price_rub=500.0, bom=[bom_item])
        
        req = MRPRequirement(
            item_code="ING-TEST",
            name="Test Extract",
            unit="kg",
            gross_requirement=100.0,
            safety_stock=20.0,
            current_free_stock=0.0,
            in_transit_stock=0.0,
            net_requirement=120.0,
            recommended_order_qty=120.0,
            total_order_cost_rub=120000.0,
            supplier_lead_time_days=10,
            shelf_life_days=365,
            urgency_status="ПЛАН"
        )
        
        # Budget cap is 60,000 RUB (50% of needed 120,000)
        opt = ProcurementBudgetOptimizer.optimize_procurement_under_budget_cap(
            product=prod,
            unconstrained_plan=[req],
            budget_cap_rub=60000.0
        )
        self.assertEqual(opt["budget_cap_rub"], 60000.0)
        self.assertEqual(opt["budget_cut_pct"], 50.0)
        self.assertAlmostEqual(opt["allocated_budget_rub"], 60000.0, places=1)


if __name__ == "__main__":
    unittest.main()
