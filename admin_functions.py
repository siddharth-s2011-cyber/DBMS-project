from database import get_airline_connection
import streamlit as st

# ------------------- Aircraft Management -------------------
def add_aircraft(model, manufacturer, seat_capacity):
    conn = get_airline_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO aircrafts (model, manufacturer, seat_capacity) VALUES (%s, %s, %s)",
        (model, manufacturer, seat_capacity)
    )
    conn.commit()
    cur.close()
    conn.close()

def delete_aircraft_by_model(model):
    """Delete aircraft by model name"""
    conn = get_airline_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM aircrafts WHERE model = %s", (model,))
    rows_affected = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return rows_affected

def get_aircrafts():
    """Get all aircrafts - NO CACHING"""
    conn = get_airline_connection()
    cur = conn.cursor()
    cur.execute("SELECT aircraft_id, model, manufacturer, seat_capacity FROM aircrafts ORDER BY aircraft_id")
    columns = [desc[0] for desc in cur.description]
    data = cur.fetchall()
    cur.close()
    conn.close()
    return columns, data

# ------------------- Airport Management -------------------
def add_airport(code, name, city, country):
    conn = get_airline_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO airports (code, name, city, country) VALUES (%s, %s, %s, %s)",
        (code, name, city, country)
    )
    conn.commit()
    cur.close()
    conn.close()

def delete_airport_by_code(code):
    """Delete airport by airport code"""
    conn = get_airline_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM airports WHERE code = %s", (code,))
    rows_affected = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return rows_affected

def get_airports():
    """Get all airports - NO CACHING"""
    conn = get_airline_connection()
    cur = conn.cursor()
    cur.execute("SELECT airport_id, code, name, city, country FROM airports ORDER BY airport_id")
    columns = [desc[0] for desc in cur.description]
    data = cur.fetchall()
    cur.close()
    conn.close()
    return columns, data

# ------------------- Flight Management -------------------
def add_flight(flight_number, origin_airport_id, destination_airport_id,
               departure_time, arrival_time, aircraft_id, fare):
    conn = get_airline_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO flights (flight_number, origin_airport_id, destination_airport_id, 
                           departure_time, arrival_time, aircraft_id, fare)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (flight_number, origin_airport_id, destination_airport_id,
          departure_time, arrival_time, aircraft_id, fare))
    conn.commit()
    cur.close()
    conn.close()

def delete_flight_by_number(flight_number):
    """Delete flight by flight number"""
    conn = get_airline_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM flights WHERE flight_number = %s", (flight_number,))
    rows_affected = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return rows_affected

def view_flights():
    """Get all flights with capacity info - NO CACHING"""
    conn = get_airline_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT f.flight_id, f.flight_number, 
               o.name AS origin, d.name AS destination, 
               f.departure_time, f.arrival_time, 
               a.model AS aircraft, 
               a.seat_capacity,
               COALESCE(
                   (SELECT COUNT(*) FROM tickets t 
                    WHERE t.flight_id = f.flight_id 
                    AND t.status != 'cancelled'), 0
               ) AS booked_seats,
               f.fare
        FROM flights f
        LEFT JOIN airports o ON f.origin_airport_id = o.airport_id
        LEFT JOIN airports d ON f.destination_airport_id = d.airport_id
        LEFT JOIN aircrafts a ON f.aircraft_id = a.aircraft_id
        ORDER BY f.flight_id
    """)
    columns = [desc[0] for desc in cur.description]
    data = cur.fetchall()
    cur.close()
    conn.close()
    return columns, data

# ------------------- Passenger Management -------------------
def delete_passenger_completely(email):
    """Delete user from both airline DB and auth DB"""
    # 1. Get passenger_id from airline DB
    conn = get_airline_connection()
    cur = conn.cursor()
    cur.execute("SELECT passanger_id FROM passangers WHERE email = %s", (email,))
    result = cur.fetchone()
    passanger_id = result[0] if result else None
    cur.close()
    conn.close()

    if passanger_id:
        # 2. Delete from main airline DB
        conn = get_airline_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM passangers WHERE passanger_id = %s", (passanger_id,))
        conn.commit()
        cur.close()
        conn.close()

        # 3. Delete login credentials from auth DB
        conn = get_auth_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM user_credentials WHERE passanger_id = %s", (passanger_id,))
        conn.commit()
        cur.close()
        conn.close()

        return True
    return False


def view_passengers():
    """Get all passengers - NO CACHING"""
    conn = get_airline_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT passanger_id, full_name, email, phone, nationality 
        FROM passangers 
        ORDER BY passanger_id
    """)
    columns = [desc[0] for desc in cur.description]
    data = cur.fetchall()
    cur.close()
    conn.close()
    return columns, data

# ------------------- Ticket Management -------------------
def delete_ticket_by_id(ticket_id):
    """Delete ticket by ticket ID"""
    conn = get_airline_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tickets WHERE ticket_id = %s", (ticket_id,))
    rows_affected = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return rows_affected

def view_all_tickets():
    """Get all tickets - NO CACHING"""
    conn = get_airline_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT t.ticket_id, t.passanger_id, p.email, f.flight_number,
               o.name AS origin, d.name AS destination,
               f.departure_time, t.seat_no, t.status
        FROM tickets t
        JOIN passangers p ON t.passanger_id = p.passanger_id
        JOIN flights f ON t.flight_id = f.flight_id
        LEFT JOIN airports o ON f.origin_airport_id = o.airport_id
        LEFT JOIN airports d ON f.destination_airport_id = d.airport_id
        ORDER BY t.ticket_id
    """)
    columns = [desc[0] for desc in cur.description]
    data = cur.fetchall()
    cur.close()
    conn.close()
    return columns, data

# ------------------- Payment Management -------------------
def delete_payment_by_id(payment_id):
    """Delete payment by payment ID"""
    conn = get_airline_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM payments WHERE payment_id = %s", (payment_id,))
    rows_affected = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return rows_affected

def view_all_payments():
    """Get all payments - NO CACHING"""
    conn = get_airline_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.payment_id, p.ticket_id, t.passanger_id, 
               ps.email, p.amount, p.method, p.status, p.payment_time
        FROM payments p
        JOIN tickets t ON p.ticket_id = t.ticket_id
        JOIN passangers ps ON t.passanger_id = ps.passanger_id
        ORDER BY p.payment_id DESC
    """)
    columns = [desc[0] for desc in cur.description]
    data = cur.fetchall()
    cur.close()
    conn.close()
    return columns, data



