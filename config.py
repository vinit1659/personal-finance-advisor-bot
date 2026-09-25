"""
Configuration Module for Personal Finance Advisor Bot
----------------------------------------------------
Defines application configuration settings, database URI, and Gemini API setup.
Loads environment variables securely using python-dotenv.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the application
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file if it exists
load_dotenv(BASE_DIR / ".env")


class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-capstone-finance")

    # SQLite Database Configuration
    DATABASE_PATH = BASE_DIR / "database" / "finance.db"
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{DATABASE_PATH}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Gemini AI Configuration
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    GEMINI_MODEL = "gemini-3.8-flash"

    # Server Port
    PORT = int(os.environ.get("PORT", 5000))
