"""
Personal Finance Advisor Bot - Flask Application
================================================
Capstone Project: Personal Finance Advisor Bot
Backend: Flask, SQLite, SQLAlchemy
AI Model: Google Gemini 3.8 Flash (gemini-3.8-flash) via official google-genai SDK

Routes:
- GET  /              : Render the main user interface
- GET  /api/health    : Health and configuration check endpoint
- POST /api/analyze   : Process finances, calculate metrics, call Gemini, persist, return advice
- GET  /api/history   : Retrieve recent historical advisory reports
"""

import json
import logging
import os
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from config import Config
from models import db, FinancialReport, ExpenseItem
from services.finance_calculator import FinanceCalculator, FinancialValidationError
from services.gemini_service import GeminiAdvisoryService, GeminiServiceError

# Configure server-side logging (Never log API keys or sensitive financial credentials)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("finance_advisor_app")


def create_app(config_class=Config):
    """Application factory for Flask app."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure database directory exists
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if db_uri.startswith("sqlite:///"):
        db_path = db_uri.replace("sqlite:///", "")
        db_dir = Path(db_path).parent
        if not db_dir.exists():
            db_dir.mkdir(parents=True, exist_ok=True)

    # Initialize SQLAlchemy with app
    db.init_app(app)

    # Initialize Gemini Advisory Service
    api_key = app.config.get("GEMINI_API_KEY")
    gemini_model = app.config.get("GEMINI_MODEL", "gemini-3.8-flash")
    gemini_service = GeminiAdvisoryService(api_key=api_key, model=gemini_model)

    # Attach service to app context for access in routes
    app.gemini_service = gemini_service

    with app.app_context():
        # Create database tables if they do not exist
        db.create_all()

    # Register error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad request.", "details": str(error)}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({"error": "HTTP method not allowed."}), 405

    @app.errorhandler(500)
    def internal_server_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({"error": "An internal server error occurred. Please try again later."}), 500

    # -------------------------------------------------------------------------
    # Route: GET /
    # -------------------------------------------------------------------------
    @app.route("/")
    def index():
        """Renders the main single-page dashboard."""
        return render_template("index.html")

    # -------------------------------------------------------------------------
    # Route: GET /api/health
    # -------------------------------------------------------------------------
    @app.route("/api/health", methods=["GET"])
    def health_check():
        """Health check endpoint for monitoring, testing, and deployment verification."""
        has_api_key = bool(app.config.get("GEMINI_API_KEY"))
        return jsonify({
            "status": "healthy",
            "service": "Personal Finance Advisor Bot",
            "model": app.config.get("GEMINI_MODEL", "gemini-3.8-flash"),
            "api_configured": has_api_key
        }), 200

    # -------------------------------------------------------------------------
    # Route: POST /api/analyze
    # -------------------------------------------------------------------------
    @app.route("/api/analyze", methods=["POST"])
    def analyze_finances():
        """
        Main Advisory Endpoint:
        1. Validates request JSON payload
        2. Validates income and expenses via FinanceCalculator
        3. Computes deterministic financial metrics & 50/30/20 distribution
        4. Invokes Gemini 3.8 Flash for structured qualitative advisory
        5. Validates structured AI output & injects advisory disclaimers
        6. Persists session records to SQLite via SQLAlchemy
        7. Returns unified response to frontend
        """
        if not request.is_json:
            return jsonify({
                "error": "Invalid request content type. Expected application/json."
            }), 400

        data = request.get_json(silent=True)
        if not data or not isinstance(data, dict):
            return jsonify({
                "error": "Request body must be a valid JSON object."
            }), 400

        raw_income = data.get("income")
        raw_expenses = data.get("expenses")
        raw_goal = data.get("goal")

        logger.info("Received financial assessment request.")

        # Step 1 & 2: Input Validation & Deterministic Financial Calculations
        try:
            financial_summary = FinanceCalculator.calculate_summary(
                raw_income=raw_income,
                raw_expenses=raw_expenses,
                raw_goal=raw_goal
            )
        except FinancialValidationError as fve:
            logger.warning(f"Financial validation failure: {fve}")
            return jsonify({"error": str(fve)}), 400
        except Exception as ex:
            logger.error(f"Unexpected error during financial calculation: {ex}")
            return jsonify({"error": "Failed to process financial metrics."}), 400

        # Step 3: Invoke Gemini AI Advisory Service
        try:
            ai_advisory = app.gemini_service.generate_advisory(
                financial_summary=financial_summary,
                goal=raw_goal
            )
        except GeminiServiceError as gse:
            logger.error(f"Gemini service advisory error: {gse}")
            return jsonify({
                "error": str(gse),
                "financial_summary": financial_summary  # Return math even if AI fails
            }), 502
        except Exception as ex:
            logger.error(f"Unexpected error during AI advisory generation: {ex}")
            return jsonify({
                "error": "An unexpected error occurred while communicating with the AI advisor.",
                "financial_summary": financial_summary
            }), 500

        # Step 4: Persist Assessment to SQLite Database
        try:
            goal_data = financial_summary.get("goal_analysis") or (raw_goal if isinstance(raw_goal, dict) else {})
            report = FinancialReport(
                monthly_income=financial_summary["monthly_income"],
                total_expenses=financial_summary["total_expenses"],
                remaining_balance=financial_summary["remaining_balance"],
                expense_ratio=financial_summary["expense_ratio"],
                savings_ratio=financial_summary["savings_ratio"],
                is_deficit=financial_summary["is_deficit"],
                goal_description=goal_data.get("description"),
                goal_target_amount=goal_data.get("target_amount"),
                goal_timeframe_months=goal_data.get("timeframe_months"),
                ai_summary=ai_advisory.get("summary", ""),
                ai_full_response=json.dumps(ai_advisory)
            )
            db.session.add(report)
            db.session.flush()  # Obtain report.id

            # Save individual expense category items
            for cat in financial_summary.get("category_breakdown", []):
                expense_item = ExpenseItem(
                    report_id=report.id,
                    category=cat["category"],
                    amount=cat["amount"],
                    percentage_of_income=cat["percentage_of_income"],
                    percentage_of_expenses=cat["percentage_of_expenses"],
                    category_type=cat.get("type", "Expense")
                )
                db.session.add(expense_item)

            db.session.commit()
            report_id = report.id
            logger.info(f"Financial assessment successfully persisted. Report ID: {report_id}")

        except Exception as db_err:
            db.session.rollback()
            logger.error(f"Database persistence failure: {db_err}")
            # If database persistence fails, we still return the calculated advice to user
            report_id = None

        # Step 5: Deliver Unified Response
        return jsonify({
            "success": True,
            "report_id": report_id,
            "financial_summary": financial_summary,
            "ai_advisory": ai_advisory
        }), 200

    # -------------------------------------------------------------------------
    # Route: GET /api/history
    # -------------------------------------------------------------------------
    @app.route("/api/history", methods=["GET"])
    def get_history():
        """Retrieves recent assessment history reports."""
        try:
            reports = FinancialReport.query.order_by(
                FinancialReport.created_at.desc()
            ).limit(10).all()
            return jsonify([r.to_dict(include_details=False) for r in reports]), 200
        except Exception as err:
            logger.error(f"Failed to fetch assessment history: {err}")
            return jsonify({"error": "Failed to retrieve history records."}), 500

    return app


# Create top-level app instance for WSGI / local execution
app = create_app()

if __name__ == "__main__":
    port = app.config.get("PORT", 5000)
    app.run(host="0.0.0.0", port=port, debug=True)
