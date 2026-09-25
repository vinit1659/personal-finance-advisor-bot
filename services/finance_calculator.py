"""
Finance Calculator Service
--------------------------
Handles deterministic mathematical and financial calculations.
Offloads all basic arithmetic from Gemini so the LLM focuses on
qualitative financial reasoning, spending analysis, and strategic advisory.

Validations:
- Income must be numeric and positive (> 0)
- Expenses must be non-negative (>= 0)
- Handles empty/invalid inputs safely with clear custom exceptions
"""

from typing import Dict, List, Any, Optional


class FinancialValidationError(ValueError):
    """Raised when user-provided financial figures fail validation."""
    pass


class FinanceCalculator:
    """Provides validated financial computations, ratios, and goal feasibility metrics."""

    # Standard essential vs discretionary classification guidelines
    ESSENTIAL_CATEGORIES = {
        "housing", "rent", "mortgage", "utilities", "bills", "groceries",
        "food", "food & groceries", "healthcare", "health", "medical",
        "transportation", "insurance", "debt", "loan", "education", "tuition"
    }

    @staticmethod
    def validate_income(income_value: Any) -> float:
        """Validates that income is a valid positive number."""
        if income_value is None or income_value == "":
            raise FinancialValidationError("Monthly income is required.")
        try:
            val = float(income_value)
        except (ValueError, TypeError):
            raise FinancialValidationError(f"Invalid income value '{income_value}'. Must be a number.")
        if val <= 0:
            raise FinancialValidationError("Monthly net income must be greater than zero.")
        if val > 1_000_000_000:
            raise FinancialValidationError("Monthly net income exceeds maximum supported limit.")
        return round(val, 2)

    @staticmethod
    def validate_expenses(expenses_list: Any) -> List[Dict[str, Any]]:
        """
        Validates expense entries:
        - Must be a list
        - Each entry must have category and amount
        - Amount must be non-negative numeric
        """
        if not isinstance(expenses_list, list):
            raise FinancialValidationError("Expenses must be provided as a list.")

        validated = []
        for index, item in enumerate(expenses_list):
            if not isinstance(item, dict):
                raise FinancialValidationError(f"Expense entry at index {index} must be an object.")

            category = str(item.get("category", "")).strip()
            if not category:
                raise FinancialValidationError(f"Expense entry at index {index} is missing a category name.")

            raw_amount = item.get("amount")
            if raw_amount is None or raw_amount == "":
                raise FinancialValidationError(f"Expense category '{category}' is missing an amount.")

            try:
                amount = float(raw_amount)
            except (ValueError, TypeError):
                raise FinancialValidationError(f"Expense amount for '{category}' must be a valid number.")

            if amount < 0:
                raise FinancialValidationError(f"Expense amount for '{category}' cannot be negative (${amount:.2f}).")

            if amount > 1_000_000_000:
                raise FinancialValidationError(f"Expense amount for '{category}' exceeds maximum supported limit.")

            if amount > 0:
                validated.append({
                    "category": category,
                    "amount": round(amount, 2)
                })

        if not validated:
            raise FinancialValidationError("At least one expense category with an amount greater than zero is required.")

        return validated

    @classmethod
    def calculate_summary(
        cls,
        raw_income: Any,
        raw_expenses: Any,
        raw_goal: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculates all core deterministic financial metrics:
        - Verified income and total expenses
        - Remaining balance (surplus / deficit)
        - Expense ratio and savings capacity ratio
        - Category breakdown with both % of income and % of expenses
        - 50/30/20 benchmark distribution (Needs, Wants, Savings)
        - Goal feasibility assessment (required monthly contribution vs available surplus)
        """
        income = cls.validate_income(raw_income)
        expenses = cls.validate_expenses(raw_expenses)

        total_expenses = round(sum(item["amount"] for item in expenses), 2)
        remaining_balance = round(income - total_expenses, 2)
        is_deficit = remaining_balance < 0

        expense_ratio = round((total_expenses / income * 100.0), 2)
        savings_ratio = round((remaining_balance / income * 100.0), 2) if not is_deficit else 0.0

        # Detailed Category Breakdown
        categorized = []
        needs_sum = 0.0
        wants_sum = 0.0

        for item in expenses:
            amount = item["amount"]
            category_name = item["category"]
            cat_lower = category_name.lower().strip()

            is_essential = any(k in cat_lower for k in cls.ESSENTIAL_CATEGORIES)
            if is_essential:
                needs_sum += amount
            else:
                wants_sum += amount

            pct_of_income = round((amount / income * 100.0), 2)
            pct_of_expenses = round((amount / total_expenses * 100.0), 2) if total_expenses > 0 else 0.0

            categorized.append({
                "category": category_name,
                "amount": amount,
                "percentage_of_income": pct_of_income,
                "percentage_of_expenses": pct_of_expenses,
                "type": "Essential (Need)" if is_essential else "Discretionary (Want)"
            })

        # Sort highest expense first
        categorized.sort(key=lambda x: x["amount"], reverse=True)

        # 50/30/20 Rule Benchmark Analysis
        benchmark_needs_target = round(income * 0.50, 2)
        benchmark_wants_target = round(income * 0.30, 2)
        benchmark_savings_target = round(income * 0.20, 2)

        distribution_50_30_20 = {
            "needs": {
                "actual_amount": round(needs_sum, 2),
                "actual_percent": round((needs_sum / income * 100.0), 2),
                "target_percent": 50.0,
                "target_amount": benchmark_needs_target,
                "status": "On Track" if needs_sum <= benchmark_needs_target else "Over Benchmark"
            },
            "wants": {
                "actual_amount": round(wants_sum, 2),
                "actual_percent": round((wants_sum / income * 100.0), 2),
                "target_percent": 30.0,
                "target_amount": benchmark_wants_target,
                "status": "On Track" if wants_sum <= benchmark_wants_target else "Over Benchmark"
            },
            "savings": {
                "actual_amount": max(0.0, remaining_balance),
                "actual_percent": savings_ratio,
                "target_percent": 20.0,
                "target_amount": benchmark_savings_target,
                "status": "On Track" if remaining_balance >= benchmark_savings_target else "Below Target"
            }
        }

        # Optional Goal Feasibility Evaluation
        goal_analysis = None
        if raw_goal and isinstance(raw_goal, dict) and raw_goal.get("description"):
            try:
                target_amount = float(raw_goal.get("target_amount", 0))
                timeframe = int(raw_goal.get("timeframe_months", 12))
                if target_amount > 0 and timeframe > 0:
                    monthly_needed = round(target_amount / timeframe, 2)
                    feasible = remaining_balance >= monthly_needed
                    monthly_gap = round(monthly_needed - remaining_balance, 2) if not feasible else 0.0

                    goal_analysis = {
                        "description": str(raw_goal.get("description")).strip(),
                        "target_amount": target_amount,
                        "timeframe_months": timeframe,
                        "monthly_required": monthly_needed,
                        "is_feasible_with_current_surplus": feasible,
                        "monthly_savings_gap": monthly_gap,
                        "projected_months_at_current_rate": round(target_amount / remaining_balance, 1) if remaining_balance > 0 else None
                    }
            except (ValueError, TypeError):
                goal_analysis = None

        return {
            "monthly_income": income,
            "total_expenses": total_expenses,
            "remaining_balance": remaining_balance,
            "expense_ratio": expense_ratio,
            "savings_ratio": savings_ratio,
            "is_deficit": is_deficit,
            "category_breakdown": categorized,
            "distribution_50_30_20": distribution_50_30_20,
            "goal_analysis": goal_analysis
        }
