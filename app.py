import math
from datetime import timedelta

import pyodbc
from flask import Flask, jsonify, request

from database import get_connection

app = Flask(__name__)

SEAT_LETTERS = "ABCD"
MIN_LAYOVER = timedelta(minutes=45)
MAX_LAYOVER = timedelta(hours=4)


class BookingError(Exception):
    def __init__(self, message, status):
        super().__init__(message)
        self.message = message
        self.status = status


def serialize(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def load_legs(cursor, where_clause="", params=()):
    cursor.execute(f"""
        SELECT
            F.FLIGHT_ID,
            F.FLIGHT_NUMBER,
            OA.ICAO_CODE AS ORIGIN,
            DA.ICAO_CODE AS DESTINATION,
            F.DEPARTURE_DATETIME,
            F.ARRIVAL_DATETIME,
            F.AIRCRAFT_TYPE,
            F.SEAT_CAPACITY,
            (SELECT COUNT(*) FROM dbo.BOOKING B WHERE B.FLIGHT_ID = F.FLIGHT_ID) AS BOOKED
        FROM dbo.FLIGHT F
        INNER JOIN dbo.AIRPORT OA ON F.ORIGIN_AIRPORT_ID = OA.AIRPORT_ID
        INNER JOIN dbo.AIRPORT DA ON F.DESTINATION_AIRPORT_ID = DA.AIRPORT_ID
        {where_clause}
        ORDER BY F.DEPARTURE_DATETIME;
    """, *params)

    columns = [column[0] for column in cursor.description]
    legs = []
    for row in cursor.fetchall():
        leg = dict(zip(columns, row))
        leg["SEATS_LEFT"] = leg["SEAT_CAPACITY"] - leg["BOOKED"]
        legs.append(leg)
    return legs


def public_leg(leg):
    return {
        "FLIGHT_ID": leg["FLIGHT_ID"],
        "FLIGHT_NUMBER": leg["FLIGHT_NUMBER"],
        "ORIGIN": leg["ORIGIN"],
        "DESTINATION": leg["DESTINATION"],
        "DEPARTURE_DATETIME": serialize(leg["DEPARTURE_DATETIME"]),
        "ARRIVAL_DATETIME": serialize(leg["ARRIVAL_DATETIME"]),
        "AIRCRAFT_TYPE": leg["AIRCRAFT_TYPE"],
        "SEATS_LEFT": leg["SEATS_LEFT"],
    }


@app.route("/")
def home():
    return jsonify({
        "application": "CharterOps",
        "message": "Charter Flight Management System",
        "status": "Running"
    })


@app.route("/booking")
def booking_page():
    return app.send_static_file("booking.html")


@app.route("/api/airports")
def get_airports():
    connection = None

    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT ICAO_CODE, NAME, CITY FROM dbo.AIRPORT ORDER BY CITY;")
        airports = [
            {"ICAO_CODE": row[0], "NAME": row[1], "CITY": row[2]}
            for row in cursor.fetchall()
        ]
        return jsonify(airports)

    except Exception:
        app.logger.exception("Unable to retrieve airports")
        return jsonify({"error": "Unable to retrieve airports"}), 500

    finally:
        if connection is not None:
            connection.close()


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
                F.AIRCRAFT_TAIL_NUMBER AS TAIL_NUMBER,
                F.AIRCRAFT_TYPE
            FROM dbo.FLIGHT F
            INNER JOIN dbo.AIRPORT OA
                ON F.ORIGIN_AIRPORT_ID = OA.AIRPORT_ID
            INNER JOIN dbo.AIRPORT DA
                ON F.DESTINATION_AIRPORT_ID = DA.AIRPORT_ID
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


@app.route("/api/search")
def search_flights():
    origin = request.args.get("origin", "").strip().upper()
    destination = request.args.get("destination", "").strip().upper()

    if not origin or not destination:
        return jsonify({"error": "origin and destination are required"}), 400
    if origin == destination:
        return jsonify({"error": "Origin and destination must be different"}), 400

    connection = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        departing = load_legs(cursor, "WHERE OA.ICAO_CODE = ?", (origin,))
        arriving = load_legs(cursor, "WHERE DA.ICAO_CODE = ?", (destination,))

        direct = [
            leg for leg in departing
            if leg["DESTINATION"] == destination and leg["SEATS_LEFT"] > 0
        ]

        connections = []
        for first in departing:
            if first["DESTINATION"] in (origin, destination) or first["SEATS_LEFT"] <= 0:
                continue
            for second in arriving:
                if second["ORIGIN"] != first["DESTINATION"] or second["SEATS_LEFT"] <= 0:
                    continue
                layover = second["DEPARTURE_DATETIME"] - first["ARRIVAL_DATETIME"]
                if MIN_LAYOVER <= layover <= MAX_LAYOVER:
                    connections.append({
                        "legs": [public_leg(first), public_leg(second)],
                        "layover_minutes": int(layover.total_seconds() // 60),
                    })

        return jsonify({
            "direct": [public_leg(leg) for leg in direct],
            "connections": connections,
        })

    except Exception:
        app.logger.exception("Unable to search flights")
        return jsonify({"error": "Unable to search flights"}), 500

    finally:
        if connection is not None:
            connection.close()


@app.route("/api/flights/<int:flight_id>/seats")
def get_seats(flight_id):
    connection = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT SEAT_CAPACITY FROM dbo.FLIGHT WHERE FLIGHT_ID = ?", flight_id)
        row = cursor.fetchone()
        if row is None:
            return jsonify({"error": "Flight not found"}), 404
        capacity = row[0]

        cursor.execute("SELECT SEAT_NUMBER FROM dbo.BOOKING WHERE FLIGHT_ID = ?", flight_id)
        booked = {r[0] for r in cursor.fetchall()}

        rows = math.ceil(capacity / len(SEAT_LETTERS))
        all_seats = [
            f"{r}{letter}"
            for r in range(1, rows + 1)
            for letter in SEAT_LETTERS
        ][:capacity]
        available = [seat for seat in all_seats if seat not in booked]

        return jsonify({
            "capacity": capacity,
            "available": available,
            "booked": sorted(booked)
        })

    except Exception:
        app.logger.exception("Unable to retrieve seats")
        return jsonify({"error": "Unable to retrieve seats"}), 500

    finally:
        if connection is not None:
            connection.close()


@app.route("/api/itineraries", methods=["POST"])
def create_itinerary():
    data = request.get_json(silent=True) or {}
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    phone = (data.get("phone") or "").strip() or None
    passenger_id = data.get("passenger_id")
    legs_input = data.get("legs")

    if not isinstance(legs_input, list) or not 1 <= len(legs_input) <= 2:
        return jsonify({
            "error": "Choose a direct flight or a flight with one connection"
        }), 400

    requested = []
    for item in legs_input:
        try:
            flight_id = int(item.get("flight_id"))
        except (AttributeError, TypeError, ValueError):
            return jsonify({"error": "Each leg needs a valid flight_id"}), 400
        seat = str(item.get("seat_number") or "").strip().upper()
        if not seat:
            return jsonify({"error": "Each leg needs a seat_number"}), 400
        requested.append((flight_id, seat))

    if not passenger_id and not (first_name and last_name and email):
        return jsonify({
            "error": "Enter a passenger ID, or a first name, last name, and email"
        }), 400

    connection = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        legs = []
        for flight_id, seat in requested:
            rows = load_legs(cursor, "WHERE F.FLIGHT_ID = ?", (flight_id,))
            if not rows:
                raise BookingError(f"Flight {flight_id} not found", 404)
            leg = rows[0]
            if leg["SEATS_LEFT"] <= 0:
                raise BookingError(f"{leg['FLIGHT_NUMBER']} is full", 409)
            cursor.execute(
                "SELECT 1 FROM dbo.BOOKING WHERE FLIGHT_ID = ? AND SEAT_NUMBER = ?",
                flight_id, seat,
            )
            if cursor.fetchone() is not None:
                raise BookingError(f"Seat {seat} is already taken on {leg['FLIGHT_NUMBER']}", 409)
            legs.append((leg, seat))

        if len(legs) == 2:
            first = legs[0][0]
            second = legs[1][0]
            if first["DESTINATION"] != second["ORIGIN"]:
                raise BookingError("Connecting flights must meet at the same airport", 400)
            layover = second["DEPARTURE_DATETIME"] - first["ARRIVAL_DATETIME"]
            if not MIN_LAYOVER <= layover <= MAX_LAYOVER:
                raise BookingError("Layover must be between 45 minutes and 4 hours", 400)

        if passenger_id:
            cursor.execute("SELECT 1 FROM dbo.PASSENGER WHERE PASSENGER_ID = ?", passenger_id)
            if cursor.fetchone() is None:
                raise BookingError("Passenger not found", 404)
        else:
            cursor.execute("SELECT PASSENGER_ID FROM dbo.PASSENGER WHERE EMAIL = ?", email)
            found = cursor.fetchone()
            if found:
                passenger_id = found[0]
            else:
                cursor.execute(
                    "INSERT INTO dbo.PASSENGER (FIRST_NAME, LAST_NAME, EMAIL, PHONE) "
                    "OUTPUT INSERTED.PASSENGER_ID VALUES (?, ?, ?, ?)",
                    first_name, last_name, email, phone,
                )
                passenger_id = cursor.fetchone()[0]

        for leg, _ in legs:
            cursor.execute(
                """
                SELECT F.FLIGHT_NUMBER
                FROM dbo.BOOKING B
                INNER JOIN dbo.FLIGHT F ON B.FLIGHT_ID = F.FLIGHT_ID
                WHERE B.PASSENGER_ID = ?
                  AND F.DEPARTURE_DATETIME < ?
                  AND F.ARRIVAL_DATETIME > ?
                """,
                passenger_id, leg["ARRIVAL_DATETIME"], leg["DEPARTURE_DATETIME"],
            )
            clash = cursor.fetchone()
            if clash is not None:
                raise BookingError(
                    f"Passenger already has {clash[0]}, which overlaps {leg['FLIGHT_NUMBER']}",
                    409,
                )

        for leg, seat in legs:
            cursor.execute(
                "INSERT INTO dbo.BOOKING (PASSENGER_ID, FLIGHT_ID, SEAT_NUMBER) VALUES (?, ?, ?)",
                passenger_id, leg["FLIGHT_ID"], seat,
            )

        connection.commit()

        return jsonify({
            "message": "Booking created",
            "passenger_id": passenger_id,
            "legs_booked": len(legs)
        }), 201

    except BookingError as error:
        if connection is not None:
            connection.rollback()
        return jsonify({"error": error.message}), error.status

    except pyodbc.IntegrityError:
        if connection is not None:
            connection.rollback()
        return jsonify({
            "error": "Passenger is already booked on this flight or seat is taken"
        }), 409

    except Exception:
        if connection is not None:
            connection.rollback()
        app.logger.exception("Unable to create booking")
        return jsonify({"error": "Unable to create booking"}), 500

    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    app.run(debug=True)
