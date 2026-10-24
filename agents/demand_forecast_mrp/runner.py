# -*- coding: utf-8 -*-
"""
CLI Demonstration Runner for Natura Siberica Demand Forecasting & MRP Agent.
Simulates a production scheduling run for 50,000 units with promo uplift in federal retail.
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from .models import (
    BOMItem,
    FinishedProduct,
    ForecastRequest,
    IngredientCategory,
    UnitOfMeasure,
)
from .forecaster import DemandForecaster, ProductionMRPEngine
from .inventree_client import InvenTreeClient


def build_flagship_product() -> FinishedProduct:
    """
    Constructs BOM specification for Natura Siberica's flagship SKU:
    'Облепиховый шампунь Облепиха Сиберика (Питание и Восстановление) 400 мл'.
    """
    bom = [
        BOMItem(
            code="ING-EXT-OBL-01",
            name="Экстракт алтайской облепихи органический (Hippophae Rhamnoides)",
            category=IngredientCategory.WILD_HARVEST_EXTRACT,
            unit=UnitOfMeasure.KG,
            qty_per_unit=0.025,  # 25 грамм на флакон 400мл
            scrap_rate=0.02,
            supplier_lead_time_days=21, # Сбор на Алтае, экстракция, доставка
            moq=50.0,
            pack_size=25.0,
            shelf_life_days=180,
            unit_cost_rub=1450.00
        ),
        BOMItem(
            code="ING-OIL-CED-02",
            name="Масло сибирского кедра холодного отжима (Pinus Sibirica)",
            category=IngredientCategory.ORGANIC_OIL,
            unit=UnitOfMeasure.KG,
            qty_per_unit=0.008,  # 8 грамм на флакон
            scrap_rate=0.015,
            supplier_lead_time_days=14,
            moq=25.0,
            pack_size=25.0,
            shelf_life_days=365,
            unit_cost_rub=2800.00
        ),
        BOMItem(
            code="ING-EXT-ROD-03",
            name="Экстракт родиолы розовой сухой стандартизованный (Золотой Корень)",
            category=IngredientCategory.WILD_HARVEST_EXTRACT,
            unit=UnitOfMeasure.KG,
            qty_per_unit=0.002,  # 2 грамма на флакон
            scrap_rate=0.01,
            supplier_lead_time_days=28, # Длинное плечо, заготовка в Саянах
            moq=10.0,
            pack_size=5.0,
            shelf_life_days=720,
            unit_cost_rub=6900.00
        ),
        BOMItem(
            code="ING-SRF-SCS-04",
            name="Мягкая моющая основа Sodium Coco-Sulfate (из кокосового масла)",
            category=IngredientCategory.SURFACTANT_BASE,
            unit=UnitOfMeasure.KG,
            qty_per_unit=0.110,  # 110 грамм на флакон
            scrap_rate=0.02,
            supplier_lead_time_days=10,
            moq=500.0,
            pack_size=100.0,
            shelf_life_days=730,
            unit_cost_rub=320.00
        ),
        BOMItem(
            code="PKG-BOT-PET-400",
            name="Флакон ПЭТ янтарный 400мл с тиснением логотипа",
            category=IngredientCategory.PRIMARY_PACKAGING,
            unit=UnitOfMeasure.PCS,
            qty_per_unit=1.0,
            scrap_rate=0.015,
            supplier_lead_time_days=25, # Пресс-форма на заводе пластика
            moq=10000.0,
            pack_size=5000.0,
            shelf_life_days=1825,
            unit_cost_rub=18.50
        ),
        BOMItem(
            code="PKG-CAP-FLP-GLD",
            name="Крышка флип-топ с золоченым кольцом 28/410",
            category=IngredientCategory.PRIMARY_PACKAGING,
            unit=UnitOfMeasure.PCS,
            qty_per_unit=1.0,
            scrap_rate=0.01,
            supplier_lead_time_days=12,
            moq=10000.0,
            pack_size=5000.0,
            shelf_life_days=1825,
            unit_cost_rub=9.20
        ),
    ]

    return FinishedProduct(
        sku="NS-SHMP-OBL-400",
        name="Облепиховый шампунь Питание и Восстановление 400мл",
        category="Уход за волосами (Organic FMCG)",
        retail_price_rub=540.00,
        bom=bom
    )


def run_pipeline() -> None:
    product = build_flagship_product()
    forecaster = DemandForecaster(default_service_level=0.95)
    mrp_engine = ProductionMRPEngine(forecaster=forecaster)
    inventree = InvenTreeClient()

    # Сценарий: Сеть «Золотое Яблоко» запускает промо-акцию на 50 000 шт с лифтом +25%
    forecast_req = ForecastRequest(
        product_sku=product.sku,
        target_period_days=30,
        planned_baseline_units=50000,
        channel_promo_lift_pct=25.0,
        service_level=0.95
    )

    print("=" * 105)
    print("🌿 NATURA SIBERICA | ENTERPRISE DEMAND FORECAST & INVENTREE MRP AGENT")
    print("=" * 105)
    print(f"ПРОДУКТ: {product.name} (SKU: {product.sku})")
    print(f"ЦЕЛЕВОЙ КАНАЛ: Федеральные сети / Сезонное промо (+{forecast_req.channel_promo_lift_pct}%)")
    print(f"ТРЕБУЕМЫЙ УРОВЕНЬ СЕРВИСА: {forecast_req.service_level * 100:.1f}% (Z-score)")
    print("-" * 105)

    # 1. Прогноз спроса
    forecast_res = forecaster.forecast_product_demand(product, forecast_req)
    print(f"[1] ЭКОНОМЕТРИЧЕСКИЙ ПРОГНОЗ СПРОСА:")
    print(f"  • Ожидаемые продажи (p50):        {forecast_res.expected_demand:,} шт.")
    print(f"  • Страховой буфер ГП (Safety):    {forecast_res.safety_stock_units:,} шт. (волатильность sigma={forecast_res.std_dev:,.0f})")
    print(f"  • ИТОГОВЫЙ ПЛАН ВЫПУСКА (p95):    {forecast_res.target_production_volume:,} шт.")
    print(f"  • Расчетная выручка партии:       {forecast_res.estimated_revenue_rub:,.2f} руб.")
    print("-" * 105)

    # 2. Опрос остатков в InvenTree ERP
    part_codes = [b.code for b in product.bom]
    warehouse_stock = inventree.get_stock_levels(part_codes)

    # 3. Расчет потребности сырья (BOM Explosion & Netting)
    plan = mrp_engine.generate_procurement_plan(product, forecast_res, warehouse_stock)

    print("[2] ДЕТАЛИЗАЦИЯ ПОТРЕБНОСТИ В СЫРЬЕ И УПАКОВКЕ (MRP RUN):")
    header_fmt = "{:<16} | {:<28} | {:<8} | {:<9} | {:<9} | {:<10} | {:<12} | {:<11}"
    row_fmt = "{:<16} | {:<28} | {:<8} | {:<9.1f} | {:<9.1f} | {:<10.1f} | {:<12.1f} | {:<11.2f}"
    
    print(header_fmt.format(
        "Код сырья", "Наименование", "Ед. изм", "Потребно", "Остаток", "В пути", "К заказу", "Бюджет (руб)"
    ))
    print("-" * 105)

    for item in plan.requirements:
        short_name = (item.name[:25] + "...") if len(item.name) > 28 else item.name
        print(row_fmt.format(
            item.item_code,
            short_name,
            item.unit,
            item.gross_requirement,
            item.current_free_stock,
            item.in_transit_stock,
            item.recommended_order_qty,
            item.total_order_cost_rub
        ))

    print("-" * 105)
    print(f"💰 ОБЩИЙ БЮДЖЕТ ЗАКУПКИ СЫРЬЯ:       {plan.total_procurement_budget_rub:,.2f} руб.")
    print(f"⏱️ КРИТИЧЕСКИЙ СРОК ПОСТАВКИ (LEAD):  {plan.critical_lead_time_days} дней (определяет дату запуска варки)")
    print("=" * 105)

    # 4. Формирование драфта PO в ERP
    po_draft = inventree.create_purchase_order(
        supplier_name="ООО «Алтайский Заготовитель» / АО «Полимер-Тара»",
        items=[{"sku": r.item_code, "qty": r.recommended_order_qty} for r in plan.requirements if r.recommended_order_qty > 0]
    )
    print(f"✅ В InvenTree ERP создан драфт заказа на закупку: {po_draft['order_id']} ({po_draft['items_count']} позиций)")
    print("=" * 105)


if __name__ == "__main__":
    run_pipeline()
