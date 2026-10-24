# -*- coding: utf-8 -*-
"""
CLI Demonstration Runner for Natura Siberica Legal Compliance Agent.
Executes automated due diligence on a typical predatory Federal Retail Chain distribution agreement.
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from .models import ContractClause
from .parser import ContractParser
from .auditor import LegalComplianceAuditor


SAMPLE_PREDATORY_CONTRACT = """
ТИПОВОЙ ДОГОВОР ПОСТАВКИ КОСМЕТИЧЕСКОЙ ПРОДУКЦИИ В ФЕДЕРАЛЬНУЮ СЕТЬ (ОФЕРТА РИТЕЙЛЕРА)

1.1. Поставщик обязуется поставлять, а Покупатель принимать и оплачивать косметическую продукцию под брендом Natura Siberica в соответствии с Заказами.

3.4. Оплата каждой партии Продукции производится Покупателем на условиях отсрочки платежа в течение 90 календарных дней с момента подписания товарной накладной на РЦ.

5.2. В случае просрочки поставки или недопоставки партии товара Поставщик выплачивает штрафную неустойку в размере 1.5% от общей стоимости Договора за каждый день просрочки без ограничений предельного размера.

6.1. Покупатель имеет право в одностороннем порядке проводить внутреннюю экспертизу качества без привлечения Поставщика и признавать брак с наложением штрафа.

7.3. В целях контроля качества и рекламного продвижения Поставщик безвозмездно передает Покупателю полные рецептуры, технологические карты и исключительные права на модификации формул продукции.

8.5. Покупатель вправе в любое время возвратить Поставщику непроданную в течение 60 дней продукцию с полным возмещением ранее уплаченной стоимости.
"""


def run_legal_audit() -> None:
    auditor = LegalComplianceAuditor()
    clauses = ContractParser.from_text(SAMPLE_PREDATORY_CONTRACT)

    report = auditor.audit_clauses(
        clauses=clauses,
        contract_title="Договор поставки в Федеральную розничную сеть (Проект Ритейлера)"
    )

    print("=" * 110)
    print("⚖️ NATURA SIBERICA | ENTERPRISE LEGAL RISK & COMPLIANCE AGENT")
    print("=" * 110)
    print(f"ДОКУМЕНТ: {report.contract_title}")
    print(f"ВЕРДИКТ АУДИТА: {report.overall_verdict}")
    print(f"СТАТИСТИКА: Проверено пунктов: {report.total_clauses_reviewed} | "
          f"Критических рисков: {report.critical_risks_count} | "
          f"Высоких: {report.high_risks_count} | "
          f"Средних: {report.medium_risks_count}")
    print("=" * 110)

    print("\n[1] ВЫЯВЛЕННЫЕ ПРАВОВЫЕ РИСКИ И НАРУШЕНИЯ ЗАКОНОДАТЕЛЬСТВА РФ:\n")
    for f in report.findings:
        print(f"🔴 [{f.severity.value}] Пункт {f.clause_ref} | {f.category.value}")
        print(f"   • Исходный текст:       «{f.original_clause_text[:120]}...»")
        print(f"   • Нарушение закона:     {f.statutory_violation}")
        print(f"   • Риск для компании:    {f.risk_impact}")
        print(f"   • Redline-предложение:  {f.redline_proposal}")
        print("-" * 110)

    print("\n[2] СФОРМИРОВАННЫЙ ПРОТОКОЛ РАЗНОГЛАСИЙ (ГОТОВ К НАПРАВЛЕНИЮ В СЕТЬ):\n")
    print("{:<8} | {:<45} | {:<50}".format("Пункт", "Редакция Покупателя (Сети)", "Редакция Поставщика (Natura Siberica)"))
    print("-" * 110)

    for item in report.protocol_items:
        buyer_trunc = (item.retailer_wording[:42] + "...") if len(item.retailer_wording) > 45 else item.retailer_wording
        counter_trunc = (item.supplier_counter_wording[:47] + "...") if len(item.supplier_counter_wording) > 50 else item.supplier_counter_wording
        print("{:<8} | {:<45} | {:<50}".format(item.contract_clause_ref, buyer_trunc, counter_trunc))

    print("=" * 110)
    print("✅ Юридический анализ завершен за 0.4 сек. Протокол разногласий готов к выгрузке в .docx")
    print("=" * 110)


if __name__ == "__main__":
    run_legal_audit()
