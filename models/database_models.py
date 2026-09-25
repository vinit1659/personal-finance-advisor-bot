"""
Database Models for Personal Finance Advisor Bot
------------------------------------------------
Defines SQLAlchemy ORM models for storing financial assessments:
- FinancialReport: Stores overall income, total expenses, remaining balance,
  optional goal attributes, and the full structured AI advisory summary.
- ExpenseItem: Stores individual line-item expense category, amount, income percentage,
  expense percentage, and essential vs discretionary classification.
"""

from datetime import datetime, timezone
import json
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utc_now():
    """Returns current UTC timestamp in a timezone-aware manner."""
    return datetime.now(timezone.utc)


class FinancialReport(db.Model):
    """Stores a financial analysis session, calculated metrics, and AI advisory output."""
    __tablename__ = "financial_reports"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False, index=True)
    monthly_income = db.Column(db.Float, nullable=False)
    total_expenses = db.Column(db.Float, nullable=False)
    remaining_balance = db.Column(db.Float, nullable=False)
    expense_ratio = db.Column(db.Float, nullable=True)
    savings_ratio = db.Column(db.Float, nullable=True)
    is_deficit = db.Column(db.Boolean, default=False, nullable=False)

    # Financial Goal (optional)
    goal_description = db.Column(db.String(255), nullable=True)
    goal_target_amount = db.Column(db.Float, nullable=True)
    goal_timeframe_months = db.Column(db.Integer, nullable=True)

    # AI Advisory Output
    ai_summary = db.Column(db.Text, nullable=True)
    ai_full_response = db.Column(db.Text, nullable=True)  # Stored as serialized JSON string

    # Relationship to individual expense items with cascading delete
    expenses = db.relationship(
        "ExpenseItem", backref="report", lazy="joined", cascade="all, delete-orphan"
    )

    def get_parsed_ai_response(self):
        """Returns the stored JSON AI advisory as a Python dictionary."""
        if not self.ai_full_response:
            return None
        try:
            return json.loads(self.ai_full_response)
        except Exception:
            return None

    def to_dict(self, include_details: bool = True):
        """Serialize report summary for API responses."""
        data = {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "monthly_income": self.monthly_income,
            "total_expenses": self.total_expenses,
            "remaining_balance": self.remaining_balance,
            "expense_ratio": self.expense_ratio,
            "savings_ratio": self.savings_ratio,
            "is_deficit": self.is_deficit,
            "goal": {
                "description": self.goal_description,
                "target_amount": self.goal_target_amount,
                "timeframe_months": self.goal_timeframe_months,
            } if self.goal_description else None,
            "ai_summary": self.ai_summary,
        }

        if include_details:
            data["expenses"] = [item.to_dict() for item in self.expenses]
            data["ai_advisory"] = self.get_parsed_ai_response()

        return data


class ExpenseItem(db.Model):
    """Stores individual line-item expense category, amount, and distribution ratio."""
    __tablename__ = "expense_items"

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(
        db.Integer, db.ForeignKey("financial_reports.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    percentage_of_income = db.Column(db.Float, nullable=False)
    percentage_of_expenses = db.Column(db.Float, nullable=True)
    category_type = db.Column(db.String(50), nullable=True)  # Essential or Discretionary

    def to_dict(self):
        """Serialize individual expense item."""
        return {
            "id": self.id,
            "category": self.category,
            "amount": self.amount,
            "percentage_of_income": self.percentage_of_income,
            "percentage_of_expenses": self.percentage_of_expenses,
            "category_type": self.category_type,
        }
