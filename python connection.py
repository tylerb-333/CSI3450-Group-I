import pypyodbc as odbc #pip install pypyodbc

DRIVER_NAME= 'SQL SERVER'
SERVER_NAME = 'server name' # replace theses with your server name in SSMS
DATABASE_NAME = 'database name' # replace theses with your database name in SSMS

connection_string = f"""
    DRIVER={{{DRIVER_NAME}}};
    SERVER={SERVER_NAME};
    DATABASE={DATABASE_NAME};
    Trust_Connection=yes;
    """

conn= odbc.connect(connection_string)
print(conn)
