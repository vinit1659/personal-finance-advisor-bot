"""
Unit Test Suite for Milestone 2: Core Functionalities
---------------------------------------------------
Tests:
1. Income validation (positive, zero, negative, invalid type)
2. Expense validation (negative amounts, missing categories, empty list)
3. Financial summary arithmetic (totals, ratios, 50/30/20 benchmark, goal evaluation)
4. Gemini prompt construction and format contract
5. Gemini response schema validation and disclaimer enforcement
6. Error handling for malformed or incomplete AI responses
"""

import unittest
from services.finance_calculator import FinanceCalculator, FinancialValidationError
from services.gemini_service import GeminiAdvisoryService, GeminiServiceError, MANDATORY_DISCLAIMER


class TestFinanceCalculator(unittest.TestCase):

    def test_valid_income(self):
        self.assertEqual(FinanceCalculator.validate_income(5000), 5000.0)
        self.assertEqual(FinanceCalculator.validate_income("4250.50"), 4250.50)

    def test_invalid_income(self):
        with self.assertRaises(FinancialValidationError):
            FinanceCalculator.validate_income(0)
        with self.assertRaises(FinancialValidationError):
            FinanceCalculator.validate_income(-500)
        with self.assertRaises(FinancialValidationError):
            FinanceCalculator.validate_income("abc")
        with self.assertRaises(FinancialValidationError):
            FinanceCalculator.validate_income(None)

    def test_expense_validation(self):
        valid_expenses = [
            {"category": "Rent", "amount": 1200},
            {"category": "Food", "amount": "400.50"}
        ]
        res = FinanceCalculator.validate_expenses(valid_expenses)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]["category"], "Rent")
        self.assertEqual(res[0]["amount"], 1200.0)
        self.assertEqual(res[1]["amount"], 400.50)

    def test_negative_expense_rejected(self):
        bad_expenses = [{"category": "Dining", "amount": -50}]
        with self.assertRaises(FinancialValidationError):
            FinanceCalculator.validate_expenses(bad_expenses)

    def test_empty_expenses_rejected(self):
        with self.assertRaises(FinancialValidationError):
            FinanceCalculator.validate_expenses([])

    def test_financial_summary_calculations(self):
        income = 5000.0
        expenses = [
            {"category": "Rent", "amount": 1500.0},
            {"category": "Groceries", "amount": 500.0},
            {"category": "Entertainment", "amount": 500.0}
        ]
        summary = FinanceCalculator.calculate_summary(income, expenses)

        self.assertEqual(summary["monthly_income"], 5000.0)
        self.assertEqual(summary["total_expenses"], 2500.0)
        self.assertEqual(summary["remaining_balance"], 2500.0)
        self.assertEqual(summary["expense_ratio"], 50.0)
        self.assertEqual(summary["savings_ratio"], 50.0)
        self.assertFalse(summary["is_deficit"])

        # Check breakdown
        self.assertEqual(len(summary["category_breakdown"]), 3)
        rent_item = next(c for c in summary["category_breakdown"] if c["category"] == "Rent")
        self.assertEqual(rent_item["percentage_of_income"], 30.0)
        self.assertEqual(rent_item["percentage_of_expenses"], 60.0)
        self.assertEqual(rent_item["type"], "Essential (Need)")

        # 50/30/20 check
        dist = summary["distribution_50_30_20"]
        self.assertEqual(dist["needs"]["actual_amount"], 2000.0) # Rent (1500) + Groceries (500)
        self.assertEqual(dist["wants"]["actual_amount"], 500.0)  # Entertainment (500)
        self.assertEqual(dist["savings"]["actual_amount"], 2500.0)

    def test_deficit_calculation(self):
        income = 2000.0
        expenses = [{"category": "Housing", "amount": 2500.0}]
        summary = FinanceCalculator.calculate_summary(income, expenses)

        self.assertTrue(summary["is_deficit"])
        self.assertEqual(summary["remaining_balance"], -500.0)
        self.assertEqual(summary["savings_ratio"], 0.0)

    def test_goal_feasibility_analysis(self):
        income = 4000.0
        expenses = [{"category": "Living", "amount": 3000.0}] # Remaining = $1000/mo
        
        # Feasible Goal: $6,000 in 12 months = $500/mo required (< $1000)
        goal_feasible = {"description": "Emergency Cushion", "target_amount": 6000, "timeframe_months": 12}
        summary1 = FinanceCalculator.calculate_summary(income, expenses, goal_feasible)
        self.assertTrue(summary1["goal_analysis"]["is_feasible_with_current_surplus"])
        self.assertEqual(summary1["goal_analysis"]["monthly_required"], 500.0)
        self.assertEqual(summary1["goal_analysis"]["monthly_savings_gap"], 0.0)

        # Infeasible Goal: $24,000 in 12 months = $2000/mo required (> $1000)
        goal_infeasible = {"description": "Downpayment", "target_amount": 24000, "timeframe_months": 12}
        summary2 = FinanceCalculator.calculate_summary(income, expenses, goal_infeasible)
        self.assertFalse(summary2["goal_analysis"]["is_feasible_with_current_surplus"])
        self.assertEqual(summary2["goal_analysis"]["monthly_required"], 2000.0)
        self.assertEqual(summary2["goal_analysis"]["monthly_savings_gap"], 1000.0)


class TestGeminiService(unittest.TestCase):

    def setUp(self):
        self.service = GeminiAdvisoryService(api_key="test-key-mock", model="gemini-3.8-flash")

    def test_prompt_generation_contains_metrics_and_disclaimer(self):
        summary = {
            "monthly_income": 6000.0,
            "total_expenses": 3600.0,
            "remaining_balance": 2400.0,
            "expense_ratio": 60.0,
            "savings_ratio": 40.0,
            "is_deficit": False,
            "category_breakdown": [
                {"category": "Rent", "amount": 2000.0, "percentage_of_income": 33.33, "percentage_of_expenses": 55.56, "type": "Essential (Need)"},
                {"category": "Dining Out", "amount": 1600.0, "percentage_of_income": 26.67, "percentage_of_expenses": 44.44, "type": "Discretionary (Want)"}
            ],
            "distribution_50_30_20": {
                "needs": {"target_amount": 3000, "actual_amount": 2000, "actual_percent": 33.33, "status": "On Track"},
                "wants": {"target_amount": 1800, "actual_amount": 1600, "actual_percent": 26.67, "status": "On Track"},
                "savings": {"target_amount": 1200, "actual_amount": 2400, "actual_percent": 40.0, "status": "On Track"}
            }
        }
        prompt = self.service.build_financial_prompt(summary)

        self.assertIn("$6,000.00", prompt)
        self.assertIn("$3,600.00", prompt)
        self.assertIn("Rent", prompt)
        self.assertIn("50/30/20 BENCHMARK", prompt)
        self.assertIn(MANDATORY_DISCLAIMER, prompt)

    def test_response_validation_valid_payload(self):
        valid_response = {
            "summary": "Great financial baseline with 40% savings margin.",
            "budget": {
                "framework_evaluation": "Aligns nicely within 50/30/20 rule.",
                "recommended_savings_target": 1200.0,
                "category_recommendations": [
                    {
                        "category": "Rent",
                        "current_amount": 2000.0,
                        "recommended_amount": 2000.0,
                        "action": "Maintain",
                        "reasoning": "Housing is currently 33% of income, within healthy limits."
                    }
                ]
            },
            "spending_analysis": {
                "observations": ["Dining out accounts for 26.7% of total earnings."],
                "high_spending_categories": ["Dining Out"],
                "efficiency_opportunities": ["Cook at home 2 more days per week."]
            },
            "saving_suggestions": [
                "Route $1,000 automatically to high-yield savings on payday.",
                "Cap dining out to $1,000 to unlock an extra $600/month."
            ],
            "financial_health_notes": [
                "Build a 3-month essential buffer of $6,000.",
                MANDATORY_DISCLAIMER
            ]
        }

        validated = self.service.validate_advisory_response(valid_response)
        self.assertEqual(validated["summary"], valid_response["summary"])
        self.assertIn(MANDATORY_DISCLAIMER, validated["financial_health_notes"])

    def test_response_validation_enforces_disclaimer(self):
        # Response missing explicit disclaimer must have it injected
        response_without_disclaimer = {
            "summary": "Good standing.",
            "budget": {"category_recommendations": []},
            "spending_analysis": {"observations": [], "high_spending_categories": []},
            "saving_suggestions": ["Save 10%"],
            "financial_health_notes": ["Maintain debt at 0."]
        }
        validated = self.service.validate_advisory_response(response_without_disclaimer)
        self.assertTrue(any(MANDATORY_DISCLAIMER in note for note in validated["financial_health_notes"]))

    def test_response_validation_rejects_missing_sections(self):
        bad_response = {
            "summary": "Incomplete data"
            # Missing budget, spending_analysis, saving_suggestions, financial_health_notes
        }
        with self.assertRaises(GeminiServiceError):
            self.service.validate_advisory_response(bad_response)


if __name__ == "__main__":
    unittest.main()
