"""
Unit tests for Cryptographic Privacy Vault and PII Sanitizer.
"""

import unittest
from agents.secure_enterprise_rag.pii_sanitizer import EnterprisePrivacyGuard


class TestPrivacyVault(unittest.TestCase):
    def setUp(self):
        self.vault = EnterprisePrivacyGuard()

    def test_pii_sanitization_and_restoration(self):
        sample = "Сотрудник Иванов Иван Иванович, паспорт 4511 654321, телефон +7 999 111-22-33."
        sanitized, tokens, has_pii, has_formula = self.vault.sanitize_text(sample)

        self.assertTrue(has_pii)
        self.assertNotIn("4511 654321", sanitized)
        self.assertNotIn("+7 999 111-22-33", sanitized)
        self.assertIn("[VAULT_PII_PASSPORT_", sanitized)

        restored = self.vault.restore_tokens(sanitized)
        self.assertIn("4511 654321", restored)
        self.assertIn("+7 999 111-22-33", restored)

    def test_formula_sanitization(self):
        sample = "Рецептура содержит 15.0% масла дикой морошки на 50 кг на варку."
        sanitized, tokens, has_pii, has_formula = self.vault.sanitize_text(sample)

        self.assertTrue(has_formula)
        self.assertNotIn("15.0% масла", sanitized)
        self.assertIn("[VAULT_FORMULA_PERCENT_", sanitized)


if __name__ == "__main__":
    unittest.main()
