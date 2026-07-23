import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file (only exists locally, not on Vercel)
_env_path = BASE_DIR / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

# API Keys & Tokens
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Application Settings
TIMEZONE = os.getenv("TIMEZONE", "Asia/Tashkent")

# File paths - on Vercel the filesystem is read-only except /tmp
IS_SERVERLESS = os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME")
if IS_SERVERLESS:
    GOOGLE_CREDENTIALS_FILE = Path("/tmp") / os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    GOOGLE_TOKEN_FILE = Path("/tmp") / os.getenv("GOOGLE_TOKEN_FILE", "token.json")
else:
    GOOGLE_CREDENTIALS_FILE = BASE_DIR / os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    GOOGLE_TOKEN_FILE = BASE_DIR / os.getenv("GOOGLE_TOKEN_FILE", "token.json")

# Gemini Model Selection
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash")

def validate_config():
    """Validates that necessary configuration keys are set."""
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Please copy .env.example to .env and fill in your API credentials."
        )

# Google Calendar OAuth Scopes
SCOPES = ["https://www.googleapis.com/auth/calendar"]
