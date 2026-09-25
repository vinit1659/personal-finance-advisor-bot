"""
Gemini Advisory Service
-----------------------
Integrates with Google's official GenAI SDK (google-genai) using the
gemini-3.8-flash model.

Constructs a structured prompt containing verified mathematical calculations
and requests a unified JSON response delivering:
1. Financial Summary
2. Budget Recommendations (50/30/20 & category allocations)
3. Spending Analysis (High spending & anomaly detection)
4. Saving Suggestions (Actionable recommendations & goal pathways)
5. Financial Health Observations & Mandatory Disclaimer

Validation & Security:
- Validates the JSON structure before returning
- Does not expose raw internal exceptions or API keys
- Adheres to Google GenAI SDK standards
"""

import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Mandatory Educational Disclaimer
MANDATORY_DISCLAIMER = (
    "Notice: This is AI-generated educational guidance for financial planning purposes only. "
    "It does not constitute certified financial, investment, legal, or tax advice. "
    "Always consult a licensed financial advisor for significant monetary decisions."
)


class GeminiServiceError(Exception):
    """Base exception for Gemini service failures."""
    pass


class GeminiAdvisoryService:
    """Manages prompt orchestration, SDK execution, and structured AI response validation."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-3.8-flash"):
        self.api_key = api_key
        self.model_name = model
        self.client = None

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Google GenAI Client: {e}")
                self.client = None

    def build_financial_prompt(
        self,
        financial_summary: Dict[str, Any],
        goal: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Constructs a unified, structured prompt for financial advisory generation."""
        income = financial_summary.get("monthly_income", 0.0)
        total_expenses = financial_summary.get("total_expenses", 0.0)
        remaining = financial_summary.get("remaining_balance", 0.0)
        expense_ratio = financial_summary.get("expense_ratio", 0.0)
        savings_ratio = financial_summary.get("savings_ratio", 0.0)
        is_deficit = financial_summary.get("is_deficit", False)
        categories = financial_summary.get("category_breakdown", [])
        dist_50_30_20 = financial_summary.get("distribution_50_30_20", {})
        goal_analysis = financial_summary.get("goal_analysis", None)

        prompt = f"""You are a professional AI Personal Finance Advisor and financial educator.
Analyze the following verified financial figures and produce a unified, comprehensive, practical advisory evaluation.

CRITICAL INSTRUCTION:
Do not perform your own basic arithmetic. The financial figures below are already mathematically verified.
Use these verified numbers to interpret financial health, identify risk areas, allocate budget caps, and provide actionable saving steps.

VERIFIED USER FINANCIAL PROFILE:
- Monthly Net Income: ${income:,.2f}
- Total Monthly Expenses: ${total_expenses:,.2f}
- Net Balance: ${remaining:,.2f} ({'MONTHLY DEFICIT' if is_deficit else 'Monthly Surplus'})
- Total Expense Ratio: {expense_ratio}% of income
- Current Savings Capacity: {savings_ratio}% of income

50/30/20 BENCHMARK COMPARISON:
- Needs (Target 50% = ${dist_50_30_20.get('needs', {}).get('target_amount', 0):,.2f}): Actual is ${dist_50_30_20.get('needs', {}).get('actual_amount', 0):,.2f} ({dist_50_30_20.get('needs', {}).get('actual_percent', 0)}%) [{dist_50_30_20.get('needs', {}).get('status', 'N/A')}]
- Wants (Target 30% = ${dist_50_30_20.get('wants', {}).get('target_amount', 0):,.2f}): Actual is ${dist_50_30_20.get('wants', {}).get('actual_amount', 0):,.2f} ({dist_50_30_20.get('wants', {}).get('actual_percent', 0)}%) [{dist_50_30_20.get('wants', {}).get('status', 'N/A')}]
- Savings/Debt (Target 20% = ${dist_50_30_20.get('savings', {}).get('target_amount', 0):,.2f}): Actual is ${dist_50_30_20.get('savings', {}).get('actual_amount', 0):,.2f} ({dist_50_30_20.get('savings', {}).get('actual_percent', 0)}%) [{dist_50_30_20.get('savings', {}).get('status', 'N/A')}]

ITEMIZED EXPENSES:
"""
        for cat in categories:
            prompt += f"- {cat['category']} ({cat.get('type', 'Expense')}): ${cat['amount']:,.2f} ({cat['percentage_of_income']}% of income, {cat['percentage_of_expenses']}% of total spending)\n"

        if goal_analysis:
            prompt += f"""
STATED FINANCIAL GOAL:
- Goal Description: {goal_analysis.get('description')}
- Target Amount: ${goal_analysis.get('target_amount', 0):,.2f}
- Timeframe: {goal_analysis.get('timeframe_months', 0)} months
- Required Monthly Contribution: ${goal_analysis.get('monthly_required', 0):,.2f}
- Feasible with Current Surplus: {'YES' if goal_analysis.get('is_feasible_with_current_surplus') else f'NO (Monthly gap of ${goal_analysis.get("monthly_savings_gap", 0):,.2f})'}
"""

        prompt += f"""
OUTPUT FORMAT:
Return ONE unified JSON object containing all required financial advisory sections matching this exact JSON schema:
{{
  "summary": "Concise, empathetic high-level assessment of their overall financial condition, cash flow sustainability, and primary strength or concern.",
  "budget": {{
    "framework_evaluation": "Narrative evaluating how their current spending aligns with the 50/30/20 framework or balanced budgeting principles.",
    "recommended_savings_target": 0.0,
    "category_recommendations": [
      {{
        "category": "Exact Category Name",
        "current_amount": 0.0,
        "recommended_amount": 0.0,
        "action": "Maintain | Reduce | Optimize | Increase",
        "reasoning": "Clear, practical rationale explaining why and how to adjust or maintain this category"
      }}
    ]
  }},
  "spending_analysis": {{
    "observations": [
      "Key spending observation 1",
      "Key spending observation 2"
    ],
    "high_spending_categories": ["Category A", "Category B"],
    "efficiency_opportunities": [
      "Concrete opportunity to reduce spending without extreme sacrifice"
    ]
  }},
  "saving_suggestions": [
    "Practical saving action step 1 with estimated monthly impact",
    "Practical saving action step 2 with estimated monthly impact",
    "Specific roadmap action tied to their financial goal or emergency cushion"
  ],
  "financial_health_notes": [
    "Guideline on emergency fund target (e.g. 3-6 months essential expenses)",
    "Debt or liquidity risk observation",
    "{MANDATORY_DISCLAIMER}"
  ]
}}

IMPORTANT: Return strictly valid JSON. Do not wrap in markdown quotes if possible. Ensure all category recommendations match the user's category names.
"""
        return prompt.strip()

    def validate_advisory_response(self, response_data: Any) -> Dict[str, Any]:
        """
        Validates the structure and content of the AI advisory response.
        Ensures all mandatory keys exist and have appropriate data types.
        """
        if not isinstance(response_data, dict):
            raise GeminiServiceError("Malformed advisory response: Expected JSON object.")

        # Check required top-level keys
        required_keys = ["summary", "budget", "spending_analysis", "saving_suggestions", "financial_health_notes"]
        for key in required_keys:
            if key not in response_data:
                raise GeminiServiceError(f"Missing required section '{key}' in AI advisory response.")

        # Validate summary
        if not isinstance(response_data["summary"], str) or not response_data["summary"].strip():
            response_data["summary"] = "Your financial profile has been analyzed based on your income and expense data."

        # Validate budget
        budget = response_data.get("budget", {})
        if not isinstance(budget, dict):
            budget = {}
            response_data["budget"] = budget

        if "category_recommendations" not in budget or not isinstance(budget["category_recommendations"], list):
            budget["category_recommendations"] = []

        # Validate spending analysis
        spending = response_data.get("spending_analysis", {})
        if not isinstance(spending, dict):
            spending = {}
            response_data["spending_analysis"] = spending

        if "observations" not in spending or not isinstance(spending["observations"], list):
            spending["observations"] = ["Spending categorized according to submitted line items."]
        if "high_spending_categories" not in spending or not isinstance(spending["high_spending_categories"], list):
            spending["high_spending_categories"] = []

        # Validate saving suggestions
        if not isinstance(response_data["saving_suggestions"], list) or not response_data["saving_suggestions"]:
            response_data["saving_suggestions"] = [
                "Establish a dedicated high-yield savings account for automated monthly transfers.",
                "Review subscription and recurring utility expenses for quick discount opportunities."
            ]

        # Enforce disclaimer presence in financial health notes
        notes = response_data.get("financial_health_notes", [])
        if not isinstance(notes, list):
            notes = []
        if not any("AI-generated" in str(note) or "disclaimer" in str(note).lower() for note in notes):
            notes.append(MANDATORY_DISCLAIMER)
        response_data["financial_health_notes"] = notes

        return response_data

    def generate_advisory(
        self,
        financial_summary: Dict[str, Any],
        goal: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Sends the structured financial prompt to Gemini 3.8 Flash using the official
        google-genai SDK, handles errors gracefully, and returns validated structured data.
        """
        if not self.api_key:
            raise GeminiServiceError(
                "Gemini API key is not configured. Please set the GEMINI_API_KEY environment variable."
            )

        if not self.client:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Google GenAI Client: {e}")
                raise GeminiServiceError("Could not connect to Google GenAI client.")

        prompt = self.build_financial_prompt(financial_summary, goal)

        try:
            from google.genai import types

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )

            if not response or not response.text:
                raise GeminiServiceError("Empty response received from the Gemini advisory model.")

            raw_text = response.text.strip()

            # Clean potential markdown wrap
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]

            parsed_data = json.loads(raw_text.strip())
            return self.validate_advisory_response(parsed_data)

        except json.JSONDecodeError as err:
            logger.error(f"Malformed JSON from Gemini model: {err}")
            raise GeminiServiceError("The AI advisor returned an unparseable response format. Please retry.")
        except Exception as e:
            logger.error(f"Gemini API error during advisory generation: {e}")
            # Do not leak raw internal trace/credentials to user
            error_msg = str(e)
            if "quota" in error_msg.lower() or "rate" in error_msg.lower():
                raise GeminiServiceError("Gemini API rate limit exceeded. Please wait a moment and try again.")
            elif "authentication" in error_msg.lower() or "api_key" in error_msg.lower():
                raise GeminiServiceError("Authentication failure with Gemini API. Verify your API key.")
            raise GeminiServiceError("An unexpected error occurred while communicating with the AI advisor.")
