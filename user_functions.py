from database import get_airline_connection
import streamlit as st

def add_passenger(full_name, email, phone, nationality):
    conn = get_airline_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO passangers (full_name, email, phone, nationality)
        VALUES (%s, %s, %s, %s)
        RETURNING passanger_id
    """, (full_name, email, phone, nationality))
    passanger_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return passanger_id


def book_flight(passanger_id, flight_id, seat_no):
    """Book a flight - status is 'pending' until payment - CHECK CAPACITY"""
    conn = get_airline_connection()
    cur = conn.cursor()
    try:
        # Check flight capacity
        cur.execute("""
            SELECT 
                a.seat_capacity,
                COALESCE(
                    (SELECT COUNT(*) FROM tickets t 
                     WHERE t.flight_id = %s 
                     AND t.status != 'cancelled'), 0
                ) AS booked_seats
            FROM flights f
            JOIN aircrafts a ON f.aircraft_id = a.aircraft_id
            WHERE f.flight_id = %s
        """, (flight_id, flight_id))

        result = cur.fetchone()

        if not result:
            return False, None, "❌ Flight not found!"

        seat_capacity, booked_seats = result

        # Check if flight is full
        if booked_seats >= seat_capacity:
            return False, None, f"❌ Flight is full! Capacity: {seat_capacity}, Booked: {booked_seats}"

        # Book the ticket
        cur.execute("""
            INSERT INTO tickets (passanger_id, flight_id, seat_no, status)
            VALUES (%s, %s, %s, 'pending')
            RETURNING ticket_id
        """, (passanger_id, flight_id, seat_no))
        ticket_id = cur.fetchone()[0]
        conn.commit()
        remaining_seats = seat_capacity - booked_seats - 1
        return True, ticket_id, f"Booking successful! {remaining_seats} seats remaining. Please complete payment to confirm."

    except Exception as e:
        conn.rollback()
        if "tickets_flight_seat_unique" in str(e):
            return False, None, "❌ This seat is already booked for this flight!"
        return False, None, f"❌ Error: {str(e)}"
    finally:
        cur.close()
        conn.close()


def cancel_ticket(ticket_id, passanger_id):
    conn = get_airline_connection()
    cur = conn.cursor()

    try:
        # Check if ticket exists and belongs to user
        cur.execute("""
            SELECT status FROM tickets 
            WHERE ticket_id = %s AND passanger_id = %s
        """, (ticket_id, passanger_id))

        result = cur.fetchone()

        if not result:
            return 0  # Ticket not found or doesn't belong to user

        if result[0] == 'cancelled':
            return -1  # Already cancelled

        # Cancel the ticket
        cur.execute("""
            UPDATE tickets 
            SET status = 'cancelled' 
            WHERE ticket_id = %s AND passanger_id = %s
        """, (ticket_id, passanger_id))

        rows_affected = cur.rowcount
        conn.commit()
        return rows_affected

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def view_user_tickets(passanger_id):
    """Get all tickets for a passenger - NO CACHING for real-time updates"""
    conn = get_airline_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT t.ticket_id, f.flight_number,
               o.name AS origin, d.name AS destination,
               f.departure_time, f.arrival_time, t.seat_no, t.status
        FROM tickets t
        JOIN flights f ON t.flight_id = f.flight_id
        LEFT JOIN airports o ON f.origin_airport_id = o.airport_id
        LEFT JOIN airports d ON f.destination_airport_id = d.airport_id
        WHERE t.passanger_id = %s
        ORDER BY t.ticket_id
    """, (passanger_id,))
    columns = [desc[0] for desc in cur.description]
    data = cur.fetchall()
    cur.close()
    conn.close()
    return columns, data


# ------------------- Payment Functions -------------------
def make_payment(ticket_id, amount, method, passanger_id):
    """Make payment and confirm the ticket - MUST PAY EXACT FARE"""
    conn = get_airline_connection()
    cur = conn.cursor()

    try:
        # Get ticket details including fare
        cur.execute("""
            SELECT t.status, t.passanger_id, f.fare 
            FROM tickets t
            JOIN flights f ON t.flight_id = f.flight_id
            WHERE t.ticket_id = %s
        """, (ticket_id,))
        result = cur.fetchone()

        if not result:
            return False, "Ticket not found!"

        ticket_status, ticket_passanger_id, flight_fare = result

        if ticket_passanger_id != passanger_id:
            return False, "This ticket doesn't belong to you!"

        if ticket_status == 'cancelled':
            return False, "Cannot pay for a cancelled ticket!"

        if ticket_status == 'confirmed':
            return False, "Payment already made for this ticket!"

        # Validate payment amount matches fare exactly
        if float(amount) != float(flight_fare):
            return False, f"Payment amount must be exactly ₹{flight_fare:.2f}. You entered ₹{amount:.2f}"

        # Insert payment
        cur.execute("""
            INSERT INTO payments (ticket_id, amount, method, status)
            VALUES (%s, %s, %s, 'success')
        """, (ticket_id, amount, method))

        # Update ticket status to confirmed
        cur.execute("""
            UPDATE tickets 
            SET status = 'confirmed' 
            WHERE ticket_id = %s
        """, (ticket_id,))

        conn.commit()
        return True, "Payment successful! Ticket confirmed."

    except Exception as e:
        conn.rollback()
        return False, f"Error: {str(e)}"
    finally:
        cur.close()
        conn.close()


def view_user_payments(passanger_id):
    """Get all payments for a passenger - NO CACHING"""
    conn = get_airline_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.payment_id, p.ticket_id, p.amount, p.method, p.status, p.payment_time
        FROM payments p
        JOIN tickets t ON p.ticket_id = t.ticket_id
        WHERE t.passanger_id = %s
        ORDER BY p.payment_time DESC
    """, (passanger_id,))
    columns = [desc[0] for desc in cur.description]
    data = cur.fetchall()
    cur.close()
    conn.close()
    return columns, data


# ------------------- Available Flights -------------------
def get_available_flights():
    """Get all available flights with capacity info - NO CACHING"""
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


def get_ticket_fare(ticket_id):
    """Get the fare for a specific ticket - NO CACHING"""
    conn = get_airline_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT f.fare 
        FROM tickets t
        JOIN flights f ON t.flight_id = f.flight_id
        WHERE t.ticket_id = %s
    """, (ticket_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else None


