CharterOps

A Flask web app with a SQL Server database for booking charter flights.

Setup
Install SQL Server Express, SSMS, and ODBC Driver 18 for SQL Server.
Run database/CharterFlights.sql in SSMS. This deletes any existing CharterFlights database and creates a new empty one.
Run database/CharterFlights_root.sql in SSMS. This loads the sample data.
From the project folder, run python -m pip install -r requirements.txt.
Run python app.py.
Booking

Open http://127.0.0.1:5000/booking. Choose a From and To airport, click Search, select a flight or connection, enter your details, pick your seat(s), and click Book.