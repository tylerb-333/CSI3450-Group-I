from flask import Flask, jsonify
from database import get_connection

app = Flask(__name__)


@app.route("/")
def home():
    return jsonify({
        "application": "CharterOps",
        "message": "Charter Flight Management System",
        "status": "Running"
    })


@app.route("/api/flights")
def get_flights():
    connection = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                F.FLIGHT_ID,
                F.FLIGHT_NUMBER,
                OA.ICAO_CODE AS ORIGIN,
                DA.ICAO_CODE AS DESTINATION,
                F.DEPARTURE_DATETIME,
                F.ARRIVAL_DATETIME,
                A.TAIL_NUMBER,
                A.AIRCRAFT_TYPE
            FROM dbo.FLIGHT F
            INNER JOIN dbo.AIRPORT OA
                ON F.ORIGIN_AIRPORT_ID = OA.AIRPORT_ID
            INNER JOIN dbo.AIRPORT DA
                ON F.DESTINATION_AIRPORT_ID = DA.AIRPORT_ID
            INNER JOIN dbo.AIRCRAFT A
                ON F.AIRCRAFT_ID = A.AIRCRAFT_ID
            ORDER BY F.DEPARTURE_DATETIME;
        """)

        columns = [column[0] for column in cursor.description]
        flights = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        for flight in flights:
            for key, value in flight.items():
                if hasattr(value, "isoformat"):
                    flight[key] = value.isoformat()

        return jsonify(flights)

    except Exception:
        app.logger.exception("Unable to retrieve flight schedule")
        return jsonify({
            "error": "Unable to retrieve flight schedule"
        }), 500

    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    app.run(debug=True)
