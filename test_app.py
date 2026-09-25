"""
Integration Test Suite for Milestone 3: app.py & Flask Endpoints
----------------------------------------------------------------
Tests:
1. GET /: Renders homepage index template
2. GET /api/health: Returns 200 and health status
3. POST /api/analyze:
   - Rejects non-JSON or malformed requests
   - Rejects zero or negative income
   - Rejects negative expense amounts
   - Rejects empty expense lists
   - Accepts valid input, runs calculations, calls mocked Gemini service,
     persists to SQLite, and returns unified advisory JSON response
   - Handles Gemini service failures gracefully (HTTP 502)
4. GET /api/history:
   - Returns persisted report records
5. Security:
   - Confirms API keys and internal secrets are NEVER in response payloads
"""

import unittest
from unittest.mock import MagicMock
import json
from app import create_app
from config import Config
from models import db, FinancialReport, ExpenseItem
from services.gemini_service import GeminiServiceError, MANDATORY_DISCLAIMER


class TestConfig(Config):
    """Test configuration using an in-memory SQLite database."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    GEMINI_API_KEY = "dummy-test-key-not-real"
    SECRET_KEY = "test-secret-key"


class FlaskAppTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Mock sample advisory response
        self.sample_advisory = {
            "summary": "Solid foundation with positive cash flow.",
            "budget": {
                "framework_evaluation": "Aligns with 50/30/20 budget framework.",
                "recommended_savings_target": 1000.0,
                "category_recommendations": [
                    {
                        "category": "Rent",
                        "current_amount": 1500.0,
                        "recommended_amount": 1500.0,
                        "action": "Maintain",
                        "reasoning": "Reasonable housing cost."
                    }
                ]
            },
            "spending_analysis": {
                "observations": ["Expenses are well controlled."],
                "high_spending_categories": ["Rent"],
                "efficiency_opportunities": ["Audit minor subscription costs."]
            },
            "saving_suggestions": [
                "Automate $500 transfer on payday.",
                "Keep emergency reserves in high-yield account."
            ],
            "financial_health_notes": [
                "Target 3-6 months reserves.",
                MANDATORY_DISCLAIMER
            ]
        }

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_get_index(self):
        """Test GET / returns 200 and loads HTML template."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Personal Finance Advisor Bot", response.data)

    def test_get_health(self):
        """Test GET /api/health returns 200 with status info."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["model"], "gemini-3.8-flash")
        self.assertTrue(data["api_configured"])
        # Ensure raw API key is never exposed
        self.assertNotIn("dummy-test-key", json.dumps(data))

    def test_analyze_non_json_request(self):
        """Test POST /api/analyze rejects non-JSON content."""
        response = self.client.post("/api/analyze", data="plain text", content_type="text/plain")
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("error", data)

    def test_analyze_invalid_income(self):
        """Test POST /api/analyze rejects negative and zero income."""
        # Zero income
        payload1 = {"income": 0, "expenses": [{"category": "Food", "amount": 100}]}
        res1 = self.client.post("/api/analyze", json=payload1)
        self.assertEqual(res1.status_code, 400)
        self.assertIn("income", res1.get_json()["error"].lower())

        # Negative income
        payload2 = {"income": -2000, "expenses": [{"category": "Food", "amount": 100}]}
        res2 = self.client.post("/api/analyze", json=payload2)
        self.assertEqual(res2.status_code, 400)
        self.assertIn("income", res2.get_json()["error"].lower())

    def test_analyze_negative_expense(self):
        """Test POST /api/analyze rejects negative expense amounts."""
        payload = {
            "income": 5000,
            "expenses": [
                {"category": "Rent", "amount": 1200},
                {"category": "Food", "amount": -150}
            ]
        }
        res = self.client.post("/api/analyze", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("cannot be negative", res.get_json()["error"].lower())

    def test_analyze_empty_expenses(self):
        """Test POST /api/analyze rejects empty expense list."""
        payload = {"income": 5000, "expenses": []}
        res = self.client.post("/api/analyze", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("at least one expense category", res.get_json()["error"].lower())

    def test_analyze_success_and_database_persistence(self):
        """Test POST /api/analyze successfully runs full pipeline and persists record."""
        # Mock the gemini_service on the app
        self.app.gemini_service.generate_advisory = MagicMock(return_value=self.sample_advisory)

        payload = {
            "income": 5000,
            "expenses": [
                {"category": "Rent", "amount": 1500},
                {"category": "Food", "amount": 500}
            ],
            "goal": {
                "description": "Emergency Fund",
                "target_amount": 6000,
                "timeframe_months": 12
            }
        }

        response = self.client.post("/api/analyze", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertIsNotNone(data["report_id"])

        # Check financial summary math
        summary = data["financial_summary"]
        self.assertEqual(summary["monthly_income"], 5000.0)
        self.assertEqual(summary["total_expenses"], 2000.0)
        self.assertEqual(summary["remaining_balance"], 3000.0)

        # Check AI advisory payload
        advisory = data["ai_advisory"]
        self.assertEqual(advisory["summary"], self.sample_advisory["summary"])
        self.assertIn(MANDATORY_DISCLAIMER, advisory["financial_health_notes"])

        # Check SQLite DB persistence
        report = FinancialReport.query.get(data["report_id"])
        self.assertIsNotNone(report)
        self.assertEqual(report.monthly_income, 5000.0)
        self.assertEqual(report.total_expenses, 2000.0)
        self.assertEqual(report.goal_description, "Emergency Fund")
        self.assertEqual(len(report.expenses), 2)

        # Security check: Ensure no API key in response
        self.assertNotIn("dummy-test-key", json.dumps(data))

    def test_analyze_gemini_service_error_handling(self):
        """Test POST /api/analyze handles GeminiServiceError gracefully (returns 502 with math)."""
        self.app.gemini_service.generate_advisory = MagicMock(
            side_effect=GeminiServiceError("Gemini API rate limit exceeded.")
        )

        payload = {
            "income": 4000,
            "expenses": [{"category": "Rent", "amount": 1000}]
        }

        response = self.client.post("/api/analyze", json=payload)
        self.assertEqual(response.status_code, 502)

        data = response.get_json()
        self.assertIn("error", data)
        self.assertIn("rate limit", data["error"].lower())
        # Even on AI failure, deterministic math is returned
        self.assertIn("financial_summary", data)
        self.assertEqual(data["financial_summary"]["remaining_balance"], 3000.0)

    def test_get_history(self):
        """Test GET /api/history returns persisted reports."""
        # Insert a sample report
        report = FinancialReport(
            monthly_income=4000.0,
            total_expenses=2000.0,
            remaining_balance=2000.0,
            ai_summary="Test history summary",
            ai_full_response=json.dumps(self.sample_advisory)
        )
        db.session.add(report)
        db.session.commit()

        response = self.client.get("/api/history")
        self.assertEqual(response.status_code, 200)
        history = response.get_json()
        self.assertIsInstance(history, list)
        self.assertGreaterEqual(len(history), 1)
        self.assertEqual(history[0]["ai_summary"], "Test history summary")


if __name__ == "__main__":
    unittest.main()
