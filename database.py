
import os
from pathlib import Path

import pyodbc
from dotenv import load_dotenv

# Load environment variables from the project folder
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

def get_connection():
    """Create and return a connection to the CharterOps database."""

    password = os.getenv("SQLSERVER_PASSWORD")

    if not password:
        raise RuntimeError(
            "SQLSERVER_PASSWORD is missing from .env"
        )

    # Escape special characters in the password
    escaped_password = (
        "{" + password.replace("}", "}}") + "}"
    )

    connection_string = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=localhost,1433;"
        "DATABASE=CharterOps;"
        "UID=sa;"
        f"PWD={escaped_password};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )

    return pyodbc.connect(connection_string, timeout=10)
