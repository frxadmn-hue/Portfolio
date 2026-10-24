"""
Unit tests for DemandForecaster and ProductionMRPEngine.
"""

import unittest
from agents.demand_forecast_mrp.models import (
    BOMItem,
    FinishedProduct,
    ForecastRequest,
    IngredientCategory,
    UnitOfMeasure,
)
from agents.demand_forecast_mrp.forecaster import DemandForecaster, ProductionMRPEngine


class TestDemandForecaster(unittest.TestCase):
    def setUp(self):
        self.forecaster = DemandForecaster(default_service_level=0.95)
        self.bom_item = BOMItem(
            code="ING-TEST-01",
            name="Organic Sea Buckthorn",
            category=IngredientCategory.WILD_HARVEST_EXTRACT,
            unit=UnitOfMeasure.KG,
            qty_per_unit=0.02,
            scrap_rate=0.0,
            supplier_lead_time_days=30,
            moq=10.0,
            pack_size=5.0,
            shelf_life_days=365,
            unit_cost_rub=1000.0
        )
        self.product = FinishedProduct(
            sku="NS-TEST-01",
            name="Test Shampoo",
            retail_price_rub=500.0,
            bom=[self.bom_item]
        )

    def test_z_score_calculation(self):
        z_95 = self.forecaster.calculate_z_score(0.95)
        self.assertAlmostEqual(z_95, 1.6448, places=2)

    def test_forecast_with_promo(self):
        req = ForecastRequest(
            product_sku="NS-TEST-01",
            planned_baseline_units=1000,
            channel_promo_lift_pct=20.0,
            service_level=0.95
        )
        res = self.forecaster.forecast_product_demand(self.product, req)
        self.assertEqual(res.expected_demand, 1200)
        self.assertGreater(res.target_production_volume, 1200)

    def test_mrp_engine_lot_sizing(self):
        req = ForecastRequest(
            product_sku="NS-TEST-01",
            planned_baseline_units=1000,
            channel_promo_lift_pct=0.0,
            service_level=0.95
        )
        forecast_res = self.forecaster.forecast_product_demand(self.product, req)
        mrp = ProductionMRPEngine(self.forecaster)
        
        # Test with zero inventory
        inv = {"ING-TEST-01": {"free_stock": 0.0, "in_transit": 0.0}}
        plan = mrp.generate_procurement_plan(self.product, forecast_res, inv)
        
        self.assertEqual(len(plan.requirements), 1)
        req_item = plan.requirements[0]
        # Must be aligned to pack_size multiple and >= MOQ
        self.assertGreaterEqual(req_item.recommended_order_qty, 10.0)
        self.assertEqual(req_item.recommended_order_qty % 5.0, 0.0)


if __name__ == "__main__":
    unittest.main()
