import os

import pyodbc


def get_connection():
    """Create and return a connection to the CharterFlights database."""

    password = os.getenv("SQLSERVER_PASSWORD")

    if password:
        server = os.getenv("SQL_SERVER", "localhost,1433")
        escaped_password = "{" + password.replace("}", "}}") + "}"
        auth = f"UID=sa;PWD={escaped_password};"
    else:
        server = os.getenv("SQL_SERVER", r"localhost\SQLEXPRESS")
        auth = "Trusted_Connection=yes;"

    connection_string = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={server};"
        "DATABASE=CharterFlights;"
        f"{auth}"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )

    return pyodbc.connect(connection_string, timeout=10)