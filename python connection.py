
import os
import pyodbc
from dotenv import load_dotenv

# Load database credentials from .env
load_dotenv()

password = os.getenv("reallyStrongPwd123")

if not password:
    raise RuntimeError("reallyStrongPwd123 is missing from .env")

# Escape special characters in the password
escaped_password = "{" + password.replace("}", "}}") + "}"

# SQL Server connection settings
connection_string = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost,1433;"
    "DATABASE=CharterOps;"
    "UID=sa;"
    f"PWD={escaped_password};"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)

# Connect and test database access
connection = None

try:
    connection = pyodbc.connect(connection_string, timeout=10)
    cursor = connection.cursor()

    cursor.execute(
        "SELECT DB_NAME(), COUNT(*) FROM dbo.FLIGHT"
    )

    database_name, flight_count = cursor.fetchone()

    print("Connection successful!")
    print(f"Database: {database_name}")
    print(f"Flights found: {flight_count}")

    cursor.close()

except pyodbc.Error as error:
    print("Database connection failed.")
    print(error)

finally:
    if connection is not None:
        connection.close()