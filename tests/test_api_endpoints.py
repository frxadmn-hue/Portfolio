"""
Integration tests for FastAPI REST Gateway endpoints.
"""

import unittest
from fastapi.testclient import TestClient
from app import app


class TestFastAPIGateway(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_root_manifest(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "OPERATIONAL")
        self.assertEqual(len(data["active_agents"]), 3)

    def test_mrp_calculation_endpoint(self):
        payload = {
            "product_sku": "NS-SHMP-OBL-400",
            "target_period_days": 30,
            "planned_baseline_units": 10000,
            "channel_promo_lift_pct": 20.0,
            "service_level": 0.95
        }
        resp = self.client.post("/api/v1/mrp/calculate", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["sku"], "NS-SHMP-OBL-400")
        self.assertGreater(data["target_production_volume"], 10000)
        self.assertGreater(len(data["requirements"]), 0)

    def test_mrp_excel_export_endpoint(self):
        resp = self.client.get("/api/v1/mrp/export-excel")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("application/vnd.openxmlformats-officedocument", resp.headers["content-type"])
        self.assertGreater(len(resp.content), 1000)

    def test_legal_audit_endpoint(self):
        payload = {
            "contract_title": "Тестовый договор поставки",
            "contract_text": (
                "1.1. Поставщик поставляет косметику.\n"
                "4.2. В случае просрочки поставки штраф составляет 3.0% в день от всей суммы договора.\n"
                "7.1. Рецептуры и секреты производства безвозмездно отчуждаются покупателю."
            )
        }
        resp = self.client.post("/api/v1/legal/audit", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(data["critical_risks_count"], 1)
        self.assertGreaterEqual(len(data["protocol_items"]), 2)

    def test_legal_docx_export_endpoint(self):
        resp = self.client.get("/api/v1/legal/export-docx")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("wordprocessingml.document", resp.headers["content-type"])
        self.assertGreater(len(resp.content), 1000)

    def test_rag_search_and_privacy_vault_endpoint(self):
        # 1. Search as R&D
        search_payload = {
            "query": "рецептура варки облепиха",
            "user_department": "rd_laboratory",
            "top_k": 2
        }
        resp = self.client.post("/api/v1/rag/search", json=search_payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(data["hits_count"], 1)
        first_hit = data["results"][0]
        sanitized = first_hit["sanitized_for_external_llm"]
        self.assertIn("[VAULT_", sanitized)

        # 2. De-anonymize on-premise
        deanon_payload = {"sanitized_text": sanitized}
        resp_deanon = self.client.post("/api/v1/rag/deanonymize", json=deanon_payload)
        self.assertEqual(resp_deanon.status_code, 200)
        cleartext = resp_deanon.json()["original_cleartext"]
        self.assertNotIn("[VAULT_", cleartext)


if __name__ == "__main__":
    unittest.main()
