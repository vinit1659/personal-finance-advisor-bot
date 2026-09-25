# Personal Finance Advisor Bot

> **An AI-powered personal financial advisory application delivering automated budget allocation, spending pattern analysis, and goal-oriented saving suggestions using Google Gemini 3.8 Flash.**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Gemini](https://img.shields.io/badge/AI%20Model-Gemini%203.8%20Flash-4285F4?style=flat&logo=google&logoColor=white)](https://aistudio.google.com/)
[![Database](https://img.shields.io/badge/Database-SQLite%20%2F%20SQLAlchemy-003B57?style=flat&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Key Features](#key-features)
3. [Technology Stack](#technology-stack)
4. [System Architecture](#system-architecture)
5. [Project Directory Structure](#project-directory-structure)
6. [Gemini Model & API Integration](#gemini-model--api-integration)
7. [Database Design](#database-design)
8. [Local Installation & Setup](#local-installation--setup)
9. [Running the Application Locally](#running-the-application-locally)
10. [Automated Testing Suite](#automated-testing-suite)
11. [Public Deployment via Ngrok](#public-deployment-via-ngrok)
12. [Security & Compliance](#security--compliance)
13. [Limitations & Future Enhancements](#limitations--future-enhancements)
14. [SkillWallet Capstone Implementation Mapping](#skillwallet-capstone-implementation-mapping)

---

## 1. Project Overview

The **Personal Finance Advisor Bot** is a full-stack educational financial advisory system designed to simplify budgeting, highlight cash-flow vulnerabilities, and produce actionable savings roadmaps.

Unlike generic conversational bots that attempt risky on-the-fly arithmetic, this system enforces a **deterministic hybrid architecture**:
1. **Authoritative Math First:** Net income, category totals, surplus/deficit balances, 50/30/20 benchmark ratios, and goal feasibility gaps are computed strictly by deterministic Python algorithms.
2. **AI Qualitative Advisory Second:** Verified figures are fed into **Google Gemini 3.8 Flash** using a unified, structured prompt contract to synthesize strategic advice across three core domains:
   - **Budget Generation:** 50/30/20 alignment and category-by-category target recommendations (*Maintain*, *Reduce*, *Optimize*).
   - **Spending Analysis:** Identification of high spending areas, behavioral observations, and concrete efficiency opportunities.
   - **Saving Suggestions:** Practical savings action items and a goal completion roadmap.

---

## 2. Key Features

- **Real-Time Client Preview:** Instant calculation of Total Income, Total Expenses, Remaining Balance, and Savings Rate as you type in Indian Rupees (`₹`).
- **Dynamic Category Management:** Add or remove expense categories on demand with sensible default presets (*Housing/Rent, Food & Groceries, Transportation, Utilities/Bills, Healthcare, Education, Shopping, Entertainment, Other*).
- **Target Goal Feasibility Calculator:** Evaluates optional user savings targets (e.g., Emergency Buffer, Downpayment) against monthly cash surplus, calculating exact timeline projections or shortfall gaps.
- **50/30/20 Financial Framework Engine:** Automatically classifies itemized expenses into Essential Needs, Discretionary Wants, and Savings with real-time visual progress tracks.
- **Unified Gemini 3.8 Flash Advisory:** Generates an executive summary, budget targets, spending pattern insights, and savings suggestions in a single structured API call.
- **Persistent Assessment Storage:** Saves full session profiles, itemized category breakdowns, and AI advisory recommendations in SQLite via SQLAlchemy.
- **Prominent Disclaimers:** Visible educational disclaimers reminding users that AI guidance is for planning purposes only and does not constitute certified financial advice.

---

## 3. Technology Stack

| Layer | Technology | Details |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.10+ / Flask 3.0.3 | Clean application factory pattern with modular routes and error handlers |
| **Database & ORM** | SQLite 3 / Flask-SQLAlchemy 3.1.1 | Zero-configuration relational persistence with cascading expense relationships |
| **AI / LLM Engine** | Google Gemini 3.8 Flash | Accessed via the official `google-genai` (v1.5.0+) SDK (`gemini-3.8-flash`) |
| **Frontend UI** | HTML5, CSS3, Vanilla JavaScript | Semantic, fully responsive 2-column layout; zero bloated frontend frameworks |
| **Styling & Fonts** | Custom CSS3 Design System | Plus Jakarta Sans typography, JetBrains Mono currency metrics, CSS Custom Properties |
| **Configuration** | Python-dotenv | Secure environment variable isolation via `.env` |

---

## 4. System Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                    User Browser (HTML5 / Vanilla JS)             │
│   - Inputs: Income (₹), Expenses, Goal (₹)                      │
│   - Real-time client-side live preview & validation             │
└───────────────────────────────┬─────────────────────────────────┘
                                │ POST /api/analyze (JSON)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Flask Controller (app.py)                   │
│   - Request validation & sanitization                           │
│   - Error boundaries & HTTP status code mapping                 │
└───────────────────────────────┬─────────────────────────────────┘
                                │ Validated payload
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│              Deterministic Financial Calculation Engine         │
│          (services/finance_calculator.py)                       │
│   - Strict bounds validation (income > 0, expenses >= 0)        │
│   - Exact arithmetic (totals, balance, ratios)                  │
│   - 50/30/20 Needs, Wants, Savings classification               │
│   - Goal feasibility & shortfall projection                     │
└───────────────────────────────┬─────────────────────────────────┘
                                │ Verified metrics
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│               Gemini Advisory Service & Prompt Pipeline          │
│              (services/gemini_service.py)                       │
│   - Model: gemini-3.8-flash                                     │
│   - Single unified structured prompt                            │
│   - Strict JSON schema enforcement                              │
│   - Mandatory educational disclaimer validation                 │
└───────────────────────────────┬─────────────────────────────────┘
                                │ Parsed & validated advice
                                ▼
┌───────────────────────────────┴─────────────────────────────────┐
│                    SQLite / SQLAlchemy Storage                  │
│   - FinancialReport (session metrics, goal, AI summary)         │
│   - ExpenseItem (category records with cascade deletion)        │
└───────────────────────────────┬─────────────────────────────────┘
                                │ Unified JSON Response
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Results Dashboard (Browser Render)              │
│   - Verified KPI Grid (Income, Expenses, Surplus/Deficit)       │
│   - 50/30/20 Framework Progress Tracks                          │
│   - Budget Category Allocations Table                           │
│   - Spending Analysis & Anomaly Badges                          │
│   - Step-by-Step Saving Suggestions & Goal Roadmap              │
│   - Educational Legal Disclaimer Callout                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Project Directory Structure

```text
personal-finance-advisor-bot/
├── app.py                     # Main Flask application & route controllers
├── config.py                  # Environment-driven Flask configuration
├── models/
│   ├── __init__.py            # Model exports
│   └── database_models.py     # SQLAlchemy models: FinancialReport & ExpenseItem
├── services/
│   ├── __init__.py            # Service exports
│   ├── finance_calculator.py  # Deterministic financial arithmetic & 50/30/20 engine
│   └── gemini_service.py      # Google GenAI SDK integration & response validator
├── templates/
│   └── index.html             # Responsive semantic HTML5 single-page dashboard
├── static/
│   ├── css/
│   │   └── style.css          # Custom CSS3 responsive stylesheet
│   └── js/
│       └── script.js          # Client-side dynamic controller & fetch() integration
├── test_core_services.py      # Unit tests for calculations, prompts, and schema
├── test_app.py                # Integration tests for Flask routes, DB, and errors
├── test_e2e_inr.py            # End-to-end integration test with realistic INR data
├── requirements.txt           # Verified Python dependencies
├── .env.example               # Template for environment variables (no secrets)
├── .gitignore                 # Exclusion rules for .env, virtual environments, DBs
├── metadata.json              # Capstone metadata & AI Studio capabilities
└── README.md                  # Comprehensive project documentation
```

---

## 6. Gemini Model & API Integration

- **Model Specification:** `gemini-3.8-flash`
- **SDK:** Official `google-genai` SDK (`from google import genai`)
- **Key Security:** Key is drawn strictly from `GEMINI_API_KEY` on the server. Never exposed to browser clients, HTML source, or Git.
- **Generation Parameters:**
  - `response_mime_type="application/json"`: Guarantees strict JSON output.
  - `temperature=0.2`: Low temperature to favor analytical consistency over creative hallucinations.
- **Unified Single-Call Prompting:** Rather than initiating three separate chat rounds, the system passes pre-verified financial metrics into a single unified prompt covering:
  1. Executive Summary
  2. Budget Framework & Category Targets
  3. Spending Analysis & Anomaly Detection
  4. Saving Suggestions & Goal Milestones
  5. Financial Health Notes & Mandatory Disclaimer
- **Fallback & Safety:** In the event of network disruption or API quota depletion, the backend catches `GeminiServiceError`, preserves the verified deterministic financial math, and returns a clean HTTP 502 with helpful user instructions.

---

## 7. Database Design

Implemented with **SQLAlchemy** on **SQLite** (`database/finance.db`):

### Table: `financial_reports`
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Auto-incrementing assessment identifier |
| `created_at` | DateTime | Indexed UTC timestamp of the session |
| `monthly_income` | Float | Verified monthly take-home pay |
| `total_expenses` | Float | Sum of all expense categories |
| `remaining_balance` | Float | Monthly net cash flow (Surplus / Deficit) |
| `expense_ratio` | Float | Total expenses as percentage of income |
| `savings_ratio` | Float | Savings capacity as percentage of income |
| `is_deficit` | Boolean | True if expenses exceed income |
| `goal_description` | String(120) | Optional financial goal name |
| `goal_target_amount` | Float | Target amount in ₹ |
| `goal_timeframe_months` | Integer | Target timeframe in months |
| `ai_summary` | Text | High-level executive summary generated by Gemini |
| `ai_full_response` | Text (JSON) | Full parsed advisory payload |

### Table: `expense_items`
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Auto-incrementing item ID |
| `report_id` | Integer (FK) | References `financial_reports.id` (cascade on delete) |
| `category` | String(64) | Category label (e.g., Housing, Food, Transportation) |
| `amount` | Float | Expense amount in ₹ |
| `percentage_of_income` | Float | Ratio relative to total net income |
| `percentage_of_expenses` | Float | Share of total expenditures |
| `category_type` | String(32) | Classification (*Essential (Need)* vs. *Discretionary (Want)*) |

---

## 8. Local Installation & Setup

### Prerequisites
- **Python:** Version **3.10** or higher (`python3 --version`)
- **pip:** Python package manager (`pip3 --version`)
- **Google Gemini API Key:** Obtainable free from [Google AI Studio](https://aistudio.google.com/)

### Step 1: Clone Repository
```bash
git clone <YOUR_REPOSITORY_URL>
cd personal-finance-advisor-bot
```

### Step 2: Create and Activate Virtual Environment
```bash
# On Linux / macOS
python3 -m venv venv
source venv/bin/activate

# On Windows (cmd.exe)
python -m venv venv
venv\Scripts\activate.bat

# On Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to create your active `.env` file:
```bash
cp .env.example .env
```
Open `.env` in any text editor and supply your Gemini API Key:
```env
GEMINI_API_KEY="AIzaSyYourActualAPIKeyHere"
FLASK_APP="app.py"
FLASK_DEBUG="1"
SECRET_KEY="replace-with-a-random-secret-key"
DATABASE_URL="sqlite:///database/finance.db"
PORT="5000"
```

---

## 9. Running the Application Locally

Start the Flask development server:
```bash
python app.py
```

The database tables will initialize automatically on first startup.

Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

### Available Endpoints:
- `GET /`: Main user interface and interactive dashboard.
- `GET /api/health`: Health status, active AI model, and configuration check.
- `POST /api/analyze`: Primary financial evaluation endpoint (accepts JSON, returns math + AI advisory).
- `GET /api/history`: Returns the 10 most recent assessment sessions.

---

## 10. Automated Testing Suite

The project includes unit and integration tests covering calculation correctness, prompt formatting, schema validation, route behaviors, error handling, and realistic Indian Rupee scenarios.

Run the test suite with Python's built-in `unittest` runner:
```bash
python3 -m unittest discover -s . -p "test_*.py" -v
```

### Test Suite Summary:
1. **`test_core_services.py` (12 tests):**
   - Income validation (rejects zero, negative, null, strings).
   - Expense validation (rejects negative amounts, empty lists).
   - Accurate arithmetic (totals, balance, percentages).
   - 50/30/20 category categorization and benchmark thresholds.
   - Goal feasibility and shortfall mathematics.
   - Structured prompt synthesis with pre-computed metrics.
   - JSON response schema validation and mandatory disclaimer enforcement.
2. **`test_app.py` (9 tests):**
   - `GET /` template rendering.
   - `GET /api/health` configuration response.
   - `POST /api/analyze` rejection of malformed or non-JSON requests.
   - Validation failure handling for invalid incomes and negative expenses.
   - Full pipeline execution, calculation integration, and SQLite persistence.
   - Graceful handling of Gemini API rate-limits and timeouts (HTTP 502).
   - `GET /api/history` retrieval.
   - Verification that no API keys leak in JSON responses.
3. **`test_e2e_inr.py` (2 tests):**
   - Direct calculation engine validation with ₹65,000 monthly income and realistic category expenses.
   - Complete end-to-end API pipeline verification in Indian Rupees.

**All 23 automated tests execute and pass in under 0.2 seconds.**

---

## 11. Public Deployment via Ngrok

Ngrok creates a secure HTTPS tunnel from the public internet directly to your local Flask port, making it ideal for client demos, grading, and external testing without manual cloud deployment.

### Step 1: Install Ngrok
- **macOS (Homebrew):** `brew install ngrok/ngrok/ngrok`
- **Linux:** `sudo snap install ngrok` or download from [ngrok.com](https://ngrok.com/download)
- **Windows:** `choco install ngrok` or download the executable

### Step 2: Authenticate Ngrok (First time only)
Sign up for a free account at [dashboard.ngrok.com](https://dashboard.ngrok.com/) to obtain your auth token:
```bash
ngrok config add-authtoken <YOUR_NGROK_AUTHTOKEN>
```

### Step 3: Start the Flask Application
In your first terminal window, start Flask on port 5000:
```bash
python app.py
```

### Step 4: Start the Ngrok Tunnel
In a second terminal window, initiate the tunnel to port 5000:
```bash
ngrok http 5000
```

### Step 5: Access the Public Application
Ngrok will display output similar to:
```text
Session Status                online
Account                       User (Plan: Free)
Forwarding                    https://abc1-23-45-67-89.ngrok-free.app -> http://localhost:5000
```
Open the `https://...ngrok-free.app` URL in any mobile or desktop browser to access the live bot.

> **Important Deployment Rules:**
> - **Never hardcode the Ngrok URL** in code, as free tunnels generate a new URL upon each restart.
> - **Never commit your `.env` file** or paste your `GEMINI_API_KEY` into public repositories or chat transcripts.

---

## 12. Security & Compliance

- **Zero Client-Side Credentials:** The Gemini API key is loaded strictly on the backend into `os.environ` via `dotenv` and passed directly to the `google-genai` client.
- **Frontend Code Isolation:** Neither `templates/index.html` nor `static/js/script.js` contain API keys, authorization tokens, or internal credentials.
- **Git Shielding:** `.gitignore` explicitly blocks `.env`, virtual environment directories, local SQLite databases (`database/*.db`), and bytecode caches.
- **Information Leak Prevention:** Server errors return sanitized JSON messages (e.g., `"error": "Monthly net income must be greater than zero."`). Python stack traces and environment internals are withheld from client responses.
- **Privacy First:** Financial inputs are kept local to the session database and are not used for model training.
- **Regulatory Disclaimers:** All advisory screens and responses prominently feature the mandatory disclaimer:
  > *"Notice: This is AI-generated educational guidance for financial planning purposes only. It does not constitute certified financial, investment, legal, or tax advice."*

---

## 13. Limitations & Future Enhancements

### Current Limitations:
- Single-user local SQLite database (sessions are stored chronologically but not partitioned by multi-tenant authentication).
- Manual expense category entry (does not ingest bank statement CSVs or Open Banking APIs).
- Stateless advisory sessions (each analysis evaluates the current submission snapshot).

### Future Enhancements:
- Multi-user authentication (OAuth2 / Google Sign-In) to track multi-month trends.
- Automated CSV/OFX bank statement parser.
- Interactive Monte Carlo simulations for retirement and investment projections.
- Localized tax deduction suggestions for Indian Income Tax sections (80C, 80D, NPS).

---

## 14. SkillWallet Capstone Implementation Mapping

| Epic | Capstone Requirement | Implementation Details |
| :--- | :--- | :--- |
| **Epic 1: Model Selection & Architecture** | Select the optimal Gemini model and define a decoupled architecture. | Chosen **`gemini-3.8-flash`** via the modern `google-genai` SDK. Implemented a deterministic hybrid architecture separating authoritative mathematical calculations from qualitative AI advisory. Built unified structured prompts with JSON schema enforcement. |
| **Epic 2: Core Functionalities Development** | Build data models, financial math engine, and Gemini service. | Created SQLAlchemy models (`FinancialReport`, `ExpenseItem`). Implemented `FinanceCalculator` for positive/non-negative input validation, expense categorization, 50/30/20 benchmark evaluation, and goal feasibility gaps. Built `GeminiAdvisoryService` with automated JSON validation and disclaimer injection. Tested via `test_core_services.py`. |
| **Epic 3: app.py Development** | Develop Flask backend controllers and application lifecycle. | Implemented Flask application factory, error handlers, and core routes (`GET /`, `GET /api/health`, `POST /api/analyze`, `GET /api/history`). Integrated input validation, mathematical pipeline, AI generation, and database persistence. Tested via `test_app.py`. |
| **Epic 4: Frontend Development** | Create a professional, responsive user interface. | Built semantic `templates/index.html`, responsive `static/css/style.css`, and vanilla `static/js/script.js`. Implemented dynamic category rows, real-time client-side calculation preview, loading radar states, Indian Rupee (`₹`) formatting, and comprehensive results dashboard. |
| **Epic 5: Deployment & Finalization** | Verify local readiness, automated testing, Ngrok configuration, and documentation. | Created `test_e2e_inr.py` validating realistic INR data (₹65,000 income scenario). Verified complete 23-test suite pass. Formulated exact local execution and Ngrok public tunneling workflows. Completed comprehensive documentation and security audits. |

---

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.
