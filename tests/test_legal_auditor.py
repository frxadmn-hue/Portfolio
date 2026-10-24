"""
Unit tests for Legal Compliance Auditor.
"""

import unittest
from agents.legal_compliance.models import ContractClause, RiskCategory, RiskSeverity
from agents.legal_compliance.auditor import LegalComplianceAuditor


class TestLegalComplianceAuditor(unittest.TestCase):
    def setUp(self):
        self.auditor = LegalComplianceAuditor()

    def test_detects_excessive_penalty(self):
        clause = ContractClause(
            clause_id="5.1",
            text="В случае просрочки поставки Поставщик уплачивает штраф в размере 2.0% за каждый день просрочки."
        )
        report = self.auditor.audit_clauses([clause], "Test Contract")
        self.assertGreaterEqual(len(report.findings), 1)
        finding = report.findings[0]
        self.assertEqual(finding.category, RiskCategory.PENALTY_DISBALANCE)
        self.assertEqual(finding.severity, RiskSeverity.CRITICAL)

    def test_detects_recipe_expropriation(self):
        clause = ContractClause(
            clause_id="8.2",
            text="Исключительные права и рецептура продукции переходят покупателю в день первой поставки."
        )
        report = self.auditor.audit_clauses([clause], "Test Contract")
        recipe_findings = [f for f in report.findings if f.category == RiskCategory.IP_RECIPE_EXPROPRIATION]
        self.assertEqual(len(recipe_findings), 1)
        self.assertEqual(recipe_findings[0].severity, RiskSeverity.CRITICAL)

    def test_detects_illegal_return_of_unsold_goods(self):
        clause = ContractClause(
            clause_id="9.4",
            text="Покупатель вправе осуществить возврат непроданной продукции по истечении 30 дней."
        )
        report = self.auditor.audit_clauses([clause], "Test Contract")
        return_findings = [f for f in report.findings if f.category == RiskCategory.UNSOLD_GOODS_RETURN]
        self.assertEqual(len(return_findings), 1)


if __name__ == "__main__":
    unittest.main()
