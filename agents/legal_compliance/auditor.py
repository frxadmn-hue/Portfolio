"""
Core Legal Risk Audit Engine for FMCG & Cosmetics Contracts.
Detects abusive retailer terms and synthesizes Russian Law-compliant Redline counter-proposals.
"""

from datetime import datetime
import re
from typing import List, Optional

from config.settings import get_settings
from .models import (
    AuditReport,
    ContractClause,
    ProtocolOfDisagreementsItem,
    RiskCategory,
    RiskFinding,
    RiskSeverity,
)


class LegalComplianceAuditor:
    """
    Audits supplier and distribution contracts against Russian commercial law,
    sanitary technical regulations (TR TS 009/2011), and retail anti-monopoly rules (381-FZ).
    """

    def __init__(self):
        self.settings = get_settings()

    def audit_clauses(self, clauses: List[ContractClause], contract_title: str) -> AuditReport:
        findings: List[RiskFinding] = []
        protocol_items: List[ProtocolOfDisagreementsItem] = []
        counter = 1

        for c in clauses:
            text = c.text
            lower_text = text.lower()

            # 1. Проверка несоразмерных штрафов и неустоек (ст. 330, 333 ГК РФ)
            if any(k in lower_text for k in ["штраф", "неустойк", "пени"]):
                # Поиск процентной ставки
                rate_match = re.search(r"(\d+(?:[.,]\d+)?)\s*%", text)
                has_cap = any(k in lower_text for k in ["не более", "ограничен", "совокупный размер не может превышать"])
                
                is_excessive = False
                rate_val = 0.0
                if rate_match:
                    try:
                        rate_val = float(rate_match.group(1).replace(",", "."))
                        if rate_val > self.settings.MAX_ACCEPTABLE_PENALTY_PCT:
                            is_excessive = True
                    except ValueError:
                        pass

                if is_excessive or not has_cap or "от общей стоимости договора" in lower_text:
                    finding = RiskFinding(
                        finding_id=f"RF-{counter:03d}",
                        clause_ref=c.clause_id,
                        category=RiskCategory.PENALTY_DISBALANCE,
                        severity=RiskSeverity.CRITICAL if rate_val >= 0.5 or not has_cap else RiskSeverity.HIGH,
                        original_clause_text=text,
                        statutory_violation="Статьи 330, 333, 401 ГК РФ (Несоразмерность неустойки последствиям нарушения)",
                        risk_impact=f"Риск безакцептного списания сетью сверхвысоких штрафов ({rate_val}% в день) без предельного лимита ответственности.",
                        redline_proposal=(
                            f"В случае нарушения сроков поставки Поставщик уплачивает Покупателю неустойку в размере "
                            f"0.1% от стоимости фактически недопоставленной в срок партии за каждый день просрочки, "
                            f"но совокупный размер ответственности не может превышать 5% от стоимости партии."
                        )
                    )
                    findings.append(finding)
                    protocol_items.append(ProtocolOfDisagreementsItem(
                        item_number=counter,
                        contract_clause_ref=c.clause_id,
                        retailer_wording=text,
                        supplier_counter_wording=finding.redline_proposal,
                        legal_rationale="Снижение штрафных санкций до рыночного уровня (0.1%/день) и ограничение 5% лимитом в соответствии со ст. 333 ГК РФ."
                    ))
                    counter += 1

            # 2. Попытка отчуждения рецептур, ноу-хау и формул косметики (ст. 1229, 1465 ГК РФ)
            if any(k in lower_text for k in ["рецептур", "формул", "технологи", "ноу-хау", "интеллектуальн"]):
                if any(k in lower_text for k in ["переходят покупателю", "отчуждаются", "исключительные права", "собственность сети"]):
                    finding = RiskFinding(
                        finding_id=f"RF-{counter:03d}",
                        clause_ref=c.clause_id,
                        category=RiskCategory.IP_RECIPE_EXPROPRIATION,
                        severity=RiskSeverity.CRITICAL,
                        original_clause_text=text,
                        statutory_violation="Статьи 1229, 1465, 1466 ГК РФ (Защита секрета производства / ноу-хау)",
                        risk_impact="Критическая угроза утраты исключительных прав на рецептуры органической косметики Натура Сиберика.",
                        redline_proposal=(
                            "Все исключительные права на результаты интеллектуальной деятельности, рецептуры, "
                            "технологические регламенты и ноу-хау, используемые при производстве Продукции, "
                            "остаются в полной собственности Поставщика. Покупателю не предоставляется никаких лицензий."
                        )
                    )
                    findings.append(finding)
                    protocol_items.append(ProtocolOfDisagreementsItem(
                        item_number=counter,
                        contract_clause_ref=c.clause_id,
                        retailer_wording=text,
                        supplier_counter_wording=finding.redline_proposal,
                        legal_rationale="Безусловная защита корпоративных рецептур и производственных ноу-хау Натура Сиберика (ст. 1465 ГК РФ)."
                    ))
                    counter += 1

            # 3. Регламент ТР ТС 009/2011 и односторонний отказ по качеству
            if any(k in lower_text for k in ["брак", "качество", "несоответств", "возврат", "лаборатор"]) and "экспертиз" in lower_text:
                if "в одностороннем порядке" in lower_text or "без участия поставщика" in lower_text:
                    finding = RiskFinding(
                        finding_id=f"RF-{counter:03d}",
                        clause_ref=c.clause_id,
                        category=RiskCategory.REGULATORY_TR_TS_009,
                        severity=RiskSeverity.HIGH,
                        original_clause_text=text,
                        statutory_violation="ТР ТС 009/2011 «О безопасности парфюмерно-косметической продукции», ст. 474, 513 ГК РФ",
                        risk_impact="Риск необоснованного отказа от приемки партий без независимой аккредитованной лабораторной экспертизы.",
                        redline_proposal=(
                            "Проверка качества продукции проводится строго в соответствии с ТР ТС 009/2011. "
                            "В случае разногласий стороны производят совместный отбор проб с направлением в "
                            "аккредитованную независимую испытательную лабораторию."
                        )
                    )
                    findings.append(finding)
                    protocol_items.append(ProtocolOfDisagreementsItem(
                        item_number=counter,
                        contract_clause_ref=c.clause_id,
                        retailer_wording=text,
                        supplier_counter_wording=finding.redline_proposal,
                        legal_rationale="Исключение односторонней выбраковки, требование соблюдения арбитражного отбора проб по ТР ТС 009/2011."
                    ))
                    counter += 1

            # 4. Сверхнормативная отсрочка оплаты (ФЗ № 381-ФЗ)
            if "отсрочк" in lower_text or "оплат" in lower_text:
                days_match = re.search(r"(\d{2,3})\s*(?:календарн\w*|банковск\w*|рабоч\w*)?\s*дн", text)
                if days_match:
                    try:
                        days_val = int(days_match.group(1))
                        if days_val > self.settings.MAX_PAYMENT_DEFERRAL_DAYS:
                            finding = RiskFinding(
                                finding_id=f"RF-{counter:03d}",
                                clause_ref=c.clause_id,
                                category=RiskCategory.PAYMENT_DEFERRAL,
                                severity=RiskSeverity.MEDIUM,
                                original_clause_text=text,
                                statutory_violation="Статья 9 Федерального закона № 381-ФЗ «Об основах государственного регулирования торговой деятельности в РФ»",
                                risk_impact=f"Замораживание оборотного капитала на {days_val} дней, нарушение установленных законом предельных сроков расчетов.",
                                redline_proposal=(
                                    "Оплата поставленной Продукции производится Покупателем не позднее 30 (тридцати) "
                                    "календарных дней со дня фактической приемки Продукции на Распределительном Центре."
                                )
                            )
                            findings.append(finding)
                            protocol_items.append(ProtocolOfDisagreementsItem(
                                item_number=counter,
                                contract_clause_ref=c.clause_id,
                                retailer_wording=text,
                                supplier_counter_wording=finding.redline_proposal,
                                legal_rationale="Приведение срока оплаты в строгое соответствие с нормами ФЗ № 381-ФЗ."
                            ))
                            counter += 1
                    except ValueError:
                        pass

            # 5. Возврат непроданной продукции (ст. 13 ФЗ № 381-ФЗ)
            if any(k in lower_text for k in ["возврат непродан", "обратный выкуп", "нереализованн"]):
                finding = RiskFinding(
                    finding_id=f"RF-{counter:03d}",
                    clause_ref=c.clause_id,
                    category=RiskCategory.UNSOLD_GOODS_RETURN,
                    severity=RiskSeverity.CRITICAL,
                    original_clause_text=text,
                    statutory_violation="Пункт 4 части 1 статьи 13 Федерального закона № 381-ФЗ (Прямой законодательный запрет)",
                    risk_impact="Прямой запрет антимонопольного законодательства: торговой сети запрещено навязывать возврат непроданных товаров.",
                    redline_proposal="Пункт исключить полностью."
                )
                findings.append(finding)
                protocol_items.append(ProtocolOfDisagreementsItem(
                    item_number=counter,
                    contract_clause_ref=c.clause_id,
                    retailer_wording=text,
                    supplier_counter_wording="Пункт исключить.",
                    legal_rationale="Прямой императивный запрет ст. 13 Федерального закона № 381-ФЗ на навязывание возврата нереализованной продукции."
                ))
                counter += 1

        crit = sum(1 for f in findings if f.severity == RiskSeverity.CRITICAL)
        high = sum(1 for f in findings if f.severity == RiskSeverity.HIGH)
        med = sum(1 for f in findings if f.severity == RiskSeverity.MEDIUM)

        if crit > 0:
            verdict = "ВЫСОКИЙ РИСК: ПОДПИСАНИЕ БЕЗ ПРОТОКОЛА РАЗНОГЛАСИЙ ЗАПРЕЩЕНО"
        elif high > 0:
            verdict = "УМЕРЕННЫЙ РИСК: РЕКОМЕНДОВАНО СОГЛАСОВАНИЕ СПОРНЫХ ПУНКТОВ"
        else:
            verdict = "ПРИЕМЛЕМЫЙ РИСК: УСЛОВИЯ СООТВЕТСТВУЮТ РЫНОЧНОМУ СТАНДАРТУ"

        return AuditReport(
            contract_title=contract_title,
            total_clauses_reviewed=len(clauses),
            critical_risks_count=crit,
            high_risks_count=high,
            medium_risks_count=med,
            overall_verdict=verdict,
            findings=findings,
            protocol_items=protocol_items,
            generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        )
