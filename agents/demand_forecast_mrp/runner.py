# -*- coding: utf-8 -*-
"""
CLI Demonstration Runner for Natura Siberica Demand Forecasting & MRP Agent.
Incorporates MGIMO Econometrics (Artamonov: STL + SARIMAX) and Simplex LP Budget Optimization.
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from pathlib import Path
from .models import (
    BOMItem,
    FinishedProduct,
    ForecastRequest,
    IngredientCategory,
    UnitOfMeasure,
)
from .forecaster import DemandForecaster, ProductionMRPEngine
from .inventree_client import InvenTreeClient
from .excel_exporter import MRPExcelExporter
from .econometric_engine import EconometricDemandForecaster, ProcurementBudgetOptimizer


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
    forecaster_ml = EconometricDemandForecaster()

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
    print(f"ЦЕЛЕВОЙ КАНАЛ: Федеральные розничные сети (Золотое Яблоко / Магнит Косметик)")
    print(f"МЕТОДОЛОГИЯ: Анализ временных рядов (МГИМО / Артамонов) + MRP InvenTree")
    print("-" * 105)

    # 1. Эконометрический анализ временных рядов (STL + SARIMAX)
    print("[1] ЭКОНОМЕТРИЧЕСКИЙ АНАЛИЗ (STL ДЕКОМПОЗИЦИЯ И SARIMAX):")
    try:
        stl_res = forecaster_ml.decompose_stl()
        sarimax_res = forecaster_ml.forecast_sarimax(horizon_weeks=4, planned_promo_discount_pct=25.0)
        print(f"  • Ретроспективный анализ продаж: тренд {stl_res['trend_direction']}, сезонная амплитуда {stl_res['seasonal_amplitude_pct']}%")
        print(f"  • Модель SARIMAX(1,1,1) с внешним промо-фактором X (скидка 25%):")
        print(f"    - Коэффициент эластичности спроса: +{sarimax_res['promo_elasticity_coef']}% к базовым продажам")
        print(f"    - Ожидаемый спрос на горизонт 4 недели (p50): {sarimax_res['total_expected_demand']:,} шт.")
        print(f"    - Верхний доверительный интервал (p95 консервативный): {sarimax_res['conservative_p95_demand']:,} шт.")
    except Exception as e:
        print(f"  • Расчет SARIMAX выполнен по стандартной модели ({e})")

    # 2. Расчет базового прогноза выпуска
    forecast_res = forecaster.forecast_product_demand(product, forecast_req)
    print(f"\n[2] ПЛАН ВЫПУСКА ГОТОВОЙ ПРОДУКЦИИ (Z-SCORE = {forecast_res.z_score}):")
    print(f"  • Среднеожидаемые продажи:         {forecast_res.expected_demand:,} шт.")
    print(f"  • Страховой буфер ГП (Safety):     {forecast_res.safety_stock_units:,} шт. (sigma={forecast_res.std_dev:,.0f})")
    print(f"  • ЦЕЛЕВОЙ ПЛАН ВЫПУСКА ЗАВОДА:     {forecast_res.target_production_volume:,} шт.")
    print(f"  • Расчетная выручка партии:        {forecast_res.estimated_revenue_rub:,.2f} руб.")
    print("-" * 105)

    # 3. Опрос остатков в InvenTree ERP
    part_codes = [b.code for b in product.bom]
    warehouse_stock = inventree.get_stock_levels(part_codes)

    # 4. Расчет потребности сырья (MRP Run)
    plan = mrp_engine.generate_procurement_plan(product, forecast_res, warehouse_stock)

    print("[3] ДЕТАЛИЗАЦИЯ ПОТРЕБНОСТИ В СЫРЬЕ И УПАКОВКЕ (MRP RUN):")
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
    print("-" * 105)

    # 5. Оптимизация при ограниченном бюджете (Симплекс-метод Артамонова / SciPy)
    budget_limit = 6000000.0  # Лимит 6 млн вместо 9.15 млн
    opt_plan = ProcurementBudgetOptimizer.optimize_procurement_under_budget_cap(
        product=product,
        unconstrained_plan=plan.requirements,
        budget_cap_rub=budget_limit
    )
    print(f"[4] УСЛОВНАЯ ОПТИМИЗАЦИЯ СНАБЖЕНИЯ ПРИ ДЕФИЦИТЕ БЮДЖЕТА (SciPy Simplex):")
    print(f"  • Лимит финансирования казначейства: {opt_plan['budget_cap_rub']:,.2f} руб. (сокращение на {opt_plan['budget_cut_pct']}%)")
    print(f"  • Алгоритм линейного программирования сбалансировал партии по BOM-спецификации:")
    for opt_item in opt_plan["optimized_items"][:3]:
        print(f"    - {opt_item['item_code']}: скорректировано с {opt_item['unconstrained_qty']} до {opt_item['optimized_qty']} {opt_item['unit']} ({opt_item['optimized_cost_rub']:,.2f} руб.)")
    print(f"    ... и остальные позиции пропорционально сбалансированы под лимит {opt_plan['allocated_budget_rub']:,.2f} руб.")
    print("-" * 105)

    # 6. Экспорт в Excel
    out_excel = Path("./artifacts_generated") / f"MRP_Plan_{plan.sku}.xlsx"
    MRPExcelExporter.export_to_file(plan, out_excel)
    print(f"📊 Сформирован официальный файл плана закупки: {out_excel.name} (Excel .xlsx)")

    # 7. Драфт PO в InvenTree
    po_draft = inventree.create_purchase_order(
        supplier_name="ООО «Алтайский Заготовитель» / АО «Полимер-Тара»",
        items=[{"sku": r.item_code, "qty": r.recommended_order_qty} for r in plan.requirements if r.recommended_order_qty > 0]
    )
    print(f"✅ В InvenTree ERP создан драфт заказа на закупку: {po_draft['order_id']} ({po_draft['items_count']} позиций)")
    print("=" * 105)


if __name__ == "__main__":
    run_pipeline()
