"""Local configuration loader for the application.

Keep private Google credentials and spreadsheet identifiers in .env, never in
source code committed to GitHub.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_DIR / ".env")


def _local_path(value):
    """Resolve a relative path from the project folder."""

    path = Path(value)
    return path if path.is_absolute() else PROJECT_DIR / path


credentials_value = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "").strip()
CREDENTIALS_FILE = (
    _local_path(credentials_value)
    if credentials_value
    else None
)

SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID", "").strip()
WORKSHEET_NAME = os.getenv("GOOGLE_WORKSHEET_NAME", "").strip()


def validate_configuration():
    """Raise a clear error before attempting a Google Sheets connection."""

    if not credentials_value:
        raise RuntimeError(
            "GOOGLE_SERVICE_ACCOUNT_FILE is missing. "
            "Create .env from .env.example."
        )

    if not CREDENTIALS_FILE.is_file():
        raise FileNotFoundError(
            f"Service-account file not found: {CREDENTIALS_FILE}"
        )

    if not SPREADSHEET_ID:
        raise RuntimeError(
            "GOOGLE_SPREADSHEET_ID is missing. "
            "Add it to your local .env file."
        )

    if not WORKSHEET_NAME:
        raise RuntimeError(
            "GOOGLE_WORKSHEET_NAME is missing. "
            "Add it to your local .env file."
        )
