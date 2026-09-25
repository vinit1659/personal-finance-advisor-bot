"""
End-to-End Verification Test for Milestone 5: Realistic Indian Rupee (INR) Data
--------------------------------------------------------------------------------
Input Scenario:
- Monthly Net Income: ₹65,000
- Expenses:
  - Housing: ₹18,000
  - Food: ₹12,000
  - Transportation: ₹5,000
  - Utilities: ₹4,000
  - Healthcare: ₹3,000
  - Shopping: ₹4,000
  - Entertainment: ₹2,000
  - Other: ₹2,000

Expected Arithmetic Verification:
- Total Expenses: ₹50,000
- Net Remaining Balance: ₹15,000 (Monthly Surplus)
- Expense Ratio: 76.92% of income
- Savings Ratio: 23.08% of income
- Essential Needs (Housing + Food + Transportation + Utilities + Healthcare): ₹42,000 (64.62%)
- Discretionary Wants (Shopping + Entertainment + Other): ₹8,000 (12.31%)
- Savings / Surplus: ₹15,000 (23.08%)

Advisory Outputs Verified:
1. Total income
2. Total expenses
3. Remaining balance
4. Budget recommendations
5. Spending analysis
6. Saving suggestions
7. Mandatory educational disclaimer
"""

import unittest
from unittest.mock import MagicMock
import json
from app import create_app
from config import Config
from models import db, FinancialReport
from services.finance_calculator import FinanceCalculator
from services.gemini_service import MANDATORY_DISCLAIMER


class E2EIndianRupeeTestCase(unittest.TestCase):

    def setUp(self):
        class E2ETestConfig(Config):
            TESTING = True
            SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
            GEMINI_API_KEY = "mock-key-for-test"

        self.app = create_app(E2ETestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_direct_calculator_with_inr_dataset(self):
        income = 65000.0
        expenses = [
            {"category": "Housing", "amount": 18000.0},
            {"category": "Food", "amount": 12000.0},
            {"category": "Transportation", "amount": 5000.0},
            {"category": "Utilities", "amount": 4000.0},
            {"category": "Healthcare", "amount": 3000.0},
            {"category": "Shopping", "amount": 4000.0},
            {"category": "Entertainment", "amount": 2000.0},
            {"category": "Other", "amount": 2000.0}
        ]
        goal = {
            "description": "Emergency Reserve Fund",
            "target_amount": 100000.0,
            "timeframe_months": 12
        }

        summary = FinanceCalculator.calculate_summary(income, expenses, goal)

        # 1. Total income
        self.assertEqual(summary["monthly_income"], 65000.0)

        # 2. Total expenses
        self.assertEqual(summary["total_expenses"], 50000.0)

        # 3. Remaining balance & ratios
        self.assertEqual(summary["remaining_balance"], 15000.0)
        self.assertAlmostEqual(summary["expense_ratio"], 76.92, places=2)
        self.assertAlmostEqual(summary["savings_ratio"], 23.08, places=2)
        self.assertFalse(summary["is_deficit"])

        # 4. 50/30/20 Distribution
        dist = summary["distribution_50_30_20"]
        self.assertEqual(dist["needs"]["actual_amount"], 42000.0)
        self.assertEqual(dist["wants"]["actual_amount"], 8000.0)
        self.assertEqual(dist["savings"]["actual_amount"], 15000.0)

        # 5. Goal Feasibility
        goal_res = summary["goal_analysis"]
        self.assertAlmostEqual(goal_res["monthly_required"], 8333.33, places=2)
        self.assertTrue(goal_res["is_feasible_with_current_surplus"])
        self.assertEqual(goal_res["monthly_savings_gap"], 0.0)

    def test_end_to_end_api_pipeline_with_inr_dataset(self):
        # Mock Gemini Advisory response conforming to schema
        mock_advisory = {
            "summary": "Your net monthly income of ₹65,000 supports a positive surplus of ₹15,000.",
            "budget": {
                "framework_evaluation": "Essential needs are at 64.6%, slightly above the 50% target. Wants are well managed at 12.3%.",
                "recommended_savings_target": 13000.0,
                "category_recommendations": [
                    {"category": "Housing", "current_amount": 18000.0, "recommended_amount": 18000.0, "action": "Maintain", "reasoning": "Standard rent in urban centers."},
                    {"category": "Food", "current_amount": 12000.0, "recommended_amount": 10000.0, "action": "Optimize", "reasoning": "Plan meals to save ₹2,000 monthly."},
                    {"category": "Shopping", "current_amount": 4000.0, "recommended_amount": 3000.0, "action": "Reduce", "reasoning": "Trim non-essential purchases."}
                ]
            },
            "spending_analysis": {
                "observations": [
                    "Housing and Food account for ₹30,000 or 46.2% of take-home pay.",
                    "Discretionary spending is low at 12.3%, showing good financial discipline."
                ],
                "high_spending_categories": ["Housing", "Food"],
                "efficiency_opportunities": [
                    "Audit monthly utility usage and compare broadband plans.",
                    "Cook in batches to reduce food spending by 15%."
                ]
            },
            "saving_suggestions": [
                "Automate a ₹10,000 recurring deposit on salary day to reach ₹1,00,000 in 10 months.",
                "Maintain remaining ₹5,000 surplus as a revolving buffer in a liquid account.",
                "Direct tax refunds or annual bonuses toward the emergency fund."
            ],
            "financial_health_notes": [
                "Aim for a 3-month essential buffer of ₹1,26,000.",
                MANDATORY_DISCLAIMER
            ]
        }

        self.app.gemini_service.generate_advisory = MagicMock(return_value=mock_advisory)

        payload = {
            "income": 65000,
            "expenses": [
                {"category": "Housing", "amount": 18000},
                {"category": "Food", "amount": 12000},
                {"category": "Transportation", "amount": 5000},
                {"category": "Utilities", "amount": 4000},
                {"category": "Healthcare", "amount": 3000},
                {"category": "Shopping", "amount": 4000},
                {"category": "Entertainment", "amount": 2000},
                {"category": "Other", "amount": 2000}
            ],
            "goal": {
                "description": "Emergency Reserve Fund",
                "target_amount": 100000,
                "timeframe_months": 12
            }
        }

        response = self.client.post("/api/analyze", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertTrue(data["success"])

        # Check required outputs
        summary = data["financial_summary"]
        self.assertEqual(summary["monthly_income"], 65000.0)
        self.assertEqual(summary["total_expenses"], 50000.0)
        self.assertEqual(summary["remaining_balance"], 15000.0)

        advisory = data["ai_advisory"]
        # Budget recommendations
        self.assertIn("budget", advisory)
        self.assertGreater(len(advisory["budget"]["category_recommendations"]), 0)

        # Spending analysis
        self.assertIn("spending_analysis", advisory)
        self.assertGreater(len(advisory["spending_analysis"]["observations"]), 0)

        # Saving suggestions
        self.assertIn("saving_suggestions", advisory)
        self.assertGreater(len(advisory["saving_suggestions"]), 0)

        # Mandatory disclaimer presence
        self.assertIn(MANDATORY_DISCLAIMER, advisory["financial_health_notes"])

        # Ensure no API key in payload
        self.assertNotIn("mock-key-for-test", json.dumps(data))


if __name__ == "__main__":
    unittest.main()
