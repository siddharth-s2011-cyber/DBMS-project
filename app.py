import streamlit as st
import pandas as pd
from database import create_auth_database, initialize_single_admin
from authentication import verify_admin, verify_user_login, register_user_credentials, check_email_exists
from admin_functions import *
from user_functions import *

# Initialize databases
create_auth_database()
initialize_single_admin()

# ------------------- Streamlit UI -------------------
st.set_page_config(page_title="Airline Reservation System", layout="wide")

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_type' not in st.session_state:
    st.session_state.user_type = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'login_view' not in st.session_state:
    st.session_state.login_view = 'user'

#Login
if not st.session_state.logged_in:
    st.title("✈️ Airline Reservation System")
    st.markdown("---")

    # Toggle between Admin and User login
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👤 User Login", use_container_width=True,
                     type="primary" if st.session_state.login_view == 'user' else "secondary"):
            st.session_state.login_view = 'user'
            st.rerun()
    with col2:
        if st.button("🔐 Admin Login", use_container_width=True,
                     type="primary" if st.session_state.login_view == 'admin' else "secondary"):
            st.session_state.login_view = 'admin'
            st.rerun()

    st.markdown("---")

    # ADMIN LOGIN
    if st.session_state.login_view == 'admin':
        st.subheader("🔐 Admin Login")

        with st.form("admin_login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login as Admin")

            if submitted:
                if verify_admin(username, password):
                    st.session_state.logged_in = True
                    st.session_state.user_type = 'admin'
                    st.success("✅ Admin login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid admin credentials")

    # USER LOGIN/REGISTER
    else:
        tabs = st.tabs(["Login", "Register"])

        # USER LOGIN
        with tabs[0]:
            st.subheader("👤 User Login")
            with st.form("user_login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login")

                if submitted:
                    success, passanger_id = verify_user_login(email, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.user_type = 'user'
                        st.session_state.user_id = passanger_id
                        st.session_state.user_email = email
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid email or password")

        # USER REGISTER
        with tabs[1]:
            st.subheader("📝 Register as New User")
            with st.form("register_form"):
                full_name = st.text_input("Full Name")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                phone = st.text_input("Phone Number")
                nationality = st.text_input("Nationality")
                submitted = st.form_submit_button("Register")

                if submitted and full_name and email and password:
                    if check_email_exists(email):
                        st.error("❌ Email already registered!")
                    else:
                        try:
                            passanger_id = add_passenger(full_name, email, phone, nationality)
                            if register_user_credentials(passanger_id, email, password):
                                st.success(f"✅ Registered! Your Passenger ID: **{passanger_id}**")
                                st.info("You can now login with your email and password")
                            else:
                                st.error("Registration failed!")
                        except Exception as e:
                            st.error(f"Error: {e}")

# =================== LOGGED IN ===================
else:
    # Top bar with logout
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        if st.session_state.user_type == 'admin':
            st.title("✈️ Airline Reservation System - Admin Dashboard")
        else:
            st.title(f"✈️ Airline Reservation System - Welcome!")
            st.caption(f"Passenger ID: {st.session_state.user_id} | Email: {st.session_state.user_email}")

    with col2:
        if st.button("Refresh"):
            st.rerun()

    with col3:
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_type = None
            st.session_state.user_id = None
            st.session_state.user_email = None
            st.rerun()

    st.markdown("---")

    # =================== ADMIN DASHBOARD ===================
    if st.session_state.user_type == 'admin':
        tabs = st.tabs(["✈️ Aircrafts", "🏢 Airports", "🛫 Flights", "🎫 Tickets", "💳 Payments", "👥 Passengers"])

        # MANAGE AIRCRAFTS
        with tabs[0]:
            st.subheader("Manage Aircrafts")
            col1, col2 = st.columns([2, 1])

            with col1:
                st.write("#### Add Aircraft")
                with st.form("add_aircraft_form"):
                    model = st.text_input("Aircraft Model")
                    manufacturer = st.text_input("Manufacturer")
                    seat_capacity = st.number_input("Seat Capacity", min_value=1, value=150)
                    if st.form_submit_button("➕ Add Aircraft") and model and manufacturer:
                        try:
                            add_aircraft(model, manufacturer, seat_capacity)
                            st.success(f"✅ Aircraft '{model}' added!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

            with col2:
                st.write("#### Delete Aircraft")
                with st.form("delete_aircraft_form"):
                    model_del = st.text_input("Aircraft Model")
                    if st.form_submit_button("🗑️ Delete"):
                        try:
                            rows = delete_aircraft_by_model(model_del)
                            if rows > 0:
                                st.success(f"✅ Deleted {rows} aircraft(s)")
                                st.rerun()
                            else:
                                st.warning("No aircraft found with that model")
                        except Exception as e:
                            st.error(f"Error: {e}")

            st.write("#### All Aircrafts")
            columns, data = get_aircrafts()
            if data:
                st.dataframe(pd.DataFrame(data, columns=columns), use_container_width=True)

        # MANAGE AIRPORTS
        with tabs[1]:
            st.subheader("Manage Airports")
            col1, col2 = st.columns([2, 1])

            with col1:
                st.write("#### Add Airport")
                with st.form("add_airport_form"):
                    code = st.text_input("Airport Code (e.g., DEL)")
                    name = st.text_input("Airport Name")
                    city = st.text_input("City")
                    country = st.text_input("Country")
                    if st.form_submit_button("➕ Add Airport") and all([code, name, city, country]):
                        try:
                            add_airport(code.upper(), name, city, country)
                            st.success(f"✅ Airport '{name}' added!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

            with col2:
                st.write("#### Delete Airport")
                with st.form("delete_airport_form"):
                    code_del = st.text_input("Airport Code")
                    if st.form_submit_button("🗑️ Delete"):
                        try:
                            rows = delete_airport_by_code(code_del.upper())
                            if rows > 0:
                                st.success(f"✅ Deleted {rows} airport(s)")
                                st.rerun()
                            else:
                                st.warning("No airport found with that code")
                        except Exception as e:
                            st.error(f"Error: {e}")

            st.write("#### All Airports")
            columns, data = get_airports()
            if data:
                st.dataframe(pd.DataFrame(data, columns=columns), use_container_width=True)

        # MANAGE FLIGHTS
        with tabs[2]:
            st.subheader("Manage Flights")
            col1, col2 = st.columns([2, 1])

            with col1:
                st.write("#### Add Flight")

                with st.expander("📍 View Airports"):
                    cols, data = get_airports()
                    if data:
                        st.dataframe(pd.DataFrame(data, columns=cols))

                with st.expander("✈️ View Aircrafts"):
                    cols, data = get_aircrafts()
                    if data:
                        st.dataframe(pd.DataFrame(data, columns=cols))

                with st.form("add_flight_form"):
                    flight_number = st.text_input("Flight Number (e.g., AI101)")
                    origin_id = st.number_input("Origin Airport ID", min_value=1)
                    dest_id = st.number_input("Destination Airport ID", min_value=1)
                    dep_time = st.text_input("Departure (YYYY-MM-DD HH:MM:SS)")
                    arr_time = st.text_input("Arrival (YYYY-MM-DD HH:MM:SS)")
                    aircraft_id = st.number_input("Aircraft ID", min_value=1)
                    fare = st.number_input("Fare (₹)", min_value=0.0, value=5000.0)

                    if st.form_submit_button("➕ Add Flight") and flight_number:
                        try:
                            add_flight(flight_number, origin_id, dest_id, dep_time, arr_time, aircraft_id, fare)
                            st.success(f"✅ Flight {flight_number} added!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

            with col2:
                st.write("#### Delete Flight")
                with st.form("delete_flight_form"):
                    flight_num_del = st.text_input("Flight Number")
                    if st.form_submit_button("🗑️ Delete"):
                        try:
                            rows = delete_flight_by_number(flight_num_del)
                            if rows > 0:
                                st.success(f"✅ Deleted flight {flight_num_del}")
                                st.rerun()
                            else:
                                st.warning("No flight found with that number")
                        except Exception as e:
                            st.error(f"Error: {e}")

            st.write("#### All Flights (with Capacity)")
            columns, data = view_flights()
            if data:
                df = pd.DataFrame(data, columns=columns)
                # Add availability column
                df['Available Seats'] = df['seat_capacity'] - df['booked_seats']
                st.dataframe(df, use_container_width=True)

        # MANAGE TICKETS
        with tabs[3]:
            st.subheader("Manage All Tickets")

            col1, col2 = st.columns([3, 1])
            with col2:
                with st.form("delete_ticket_form"):
                    ticket_id = st.number_input("Ticket ID", min_value=1)
                    if st.form_submit_button("🗑️ Delete"):
                        try:
                            rows = delete_ticket_by_id(ticket_id)
                            if rows > 0:
                                st.success(f"✅ Deleted ticket {ticket_id}")
                                st.rerun()
                            else:
                                st.warning("Ticket not found")
                        except Exception as e:
                            st.error(f"Error: {e}")

            columns, data = view_all_tickets()
            if data:
                st.dataframe(pd.DataFrame(data, columns=columns), use_container_width=True)
            else:
                st.info("No tickets in the system")

        # MANAGE PAYMENTS
        with tabs[4]:
            st.subheader("Manage All Payments")

            col1, col2 = st.columns([3, 1])
            with col2:
                with st.form("delete_payment_form"):
                    payment_id = st.number_input("Payment ID", min_value=1)
                    if st.form_submit_button("🗑️ Delete"):
                        try:
                            rows = delete_payment_by_id(payment_id)
                            if rows > 0:
                                st.success(f"✅ Deleted payment {payment_id}")
                                st.rerun()
                            else:
                                st.warning("Payment not found")
                        except Exception as e:
                            st.error(f"Error: {e}")

            columns, data = view_all_payments()
            if data:
                st.dataframe(pd.DataFrame(data, columns=columns), use_container_width=True)
            else:
                st.info("No payments in the system")

        # MANAGE PASSENGERS
        with tabs[5]:
            st.subheader("Manage All Passengers")

            col1, col2 = st.columns([3, 1])
            with col2:
                with st.form("delete_passenger_form"):
                    email_del = st.text_input("Passenger Email")
                    if st.form_submit_button("🗑️ Delete"):
                        try:
                            rows = delete_passenger_completely(email_del)
                            if rows > 0:
                                st.success(f"✅ Deleted passenger {email_del}")
                                st.rerun()
                            else:
                                st.warning("Passenger not found")
                        except Exception as e:
                            st.error(f"Error: {e}")

            columns, data = view_passengers()
            if data:
                st.dataframe(pd.DataFrame(data, columns=columns), use_container_width=True)
            else:
                st.info("No passengers registered")

    # =================== USER DASHBOARD ===================
    else:
        tabs = st.tabs(["🛫 Available Flights", "🎫 Book Ticket", "📋 My Tickets", "💳 Make Payment", "💰 My Payments"])

        # AVAILABLE FLIGHTS
        with tabs[0]:
            st.subheader("Available Flights")
            columns, flights = get_available_flights()
            if flights:
                df = pd.DataFrame(flights, columns=columns)
                # Add availability column
                df['Available Seats'] = df['seat_capacity'] - df['booked_seats']
                df['Status'] = df['Available Seats'].apply(
                    lambda x: '🟢 Available' if x > 10
                    else '🟡 Limited' if x > 0
                    else '🔴 Full'
                )
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No flights available")

        # BOOK TICKET
        with tabs[1]:
            st.subheader("Book a Flight")

            st.info("💡 Your booking will be **pending** until payment is completed")

            with st.expander("📋 View Available Flights"):
                columns, flights = get_available_flights()
                if flights:
                    df = pd.DataFrame(flights, columns=columns)
                    df['Available Seats'] = df['seat_capacity'] - df['booked_seats']
                    st.dataframe(df)

            with st.form("book_flight_form"):
                flight_id = st.number_input("Flight ID", min_value=1)
                seat = st.text_input("Seat Number (e.g., 12A, 5C)")
                if st.form_submit_button("🎫 Book Flight") and seat:
                    success, ticket_id, message = book_flight(st.session_state.user_id, flight_id, seat.upper())
                    if success:
                        st.success(f"✅ {message}")
                        st.info(f"Your Ticket ID: **{ticket_id}**")
                        st.warning("⚠️ Please complete payment to confirm your booking!")
                        st.rerun()
                    else:
                        st.error(message)

        # MY TICKETS
        with tabs[2]:
            st.subheader("My Tickets")
            columns, tickets = view_user_tickets(st.session_state.user_id)
            if tickets:
                df = pd.DataFrame(tickets, columns=columns)
                st.dataframe(df, use_container_width=True)

                st.markdown("---")
                st.write("#### Cancel Ticket")
                with st.form("cancel_ticket_form"):
                    ticket_id = st.number_input("Ticket ID to Cancel", min_value=1)
                    if st.form_submit_button("❌ Cancel Ticket"):
                        try:
                            result = cancel_ticket(ticket_id, st.session_state.user_id)

                            if result > 0:
                                st.success("✅ Ticket cancelled successfully!")
                                st.rerun()
                            elif result == -1:
                                st.warning("⚠️ This ticket is already cancelled")
                            else:
                                st.error("❌ Ticket not found or doesn't belong to you")
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
            else:
                st.info("You have no tickets yet. Book a flight to get started!")

        # MAKE PAYMENT
        with tabs[3]:
            st.subheader("Make Payment")

            st.info("💡 You must pay the exact flight fare to confirm your ticket")

            with st.expander("📋 View My Tickets"):
                columns, tickets = view_user_tickets(st.session_state.user_id)
                if tickets:
                    st.dataframe(pd.DataFrame(tickets, columns=columns))

            with st.form("payment_form"):
                ticket_id_input = st.number_input("Ticket ID", min_value=1, step=1)

                # Automatically fetch and display fare
                if ticket_id_input > 0:
                    fare = get_ticket_fare(ticket_id_input)
                    if fare:
                        st.success(f"💰 Required Payment: ₹{fare:.2f}")
                        # Pre-fill the amount with the correct fare
                        amount = st.number_input("Amount (₹)",
                                                 min_value=0.0,
                                                 value=float(fare),
                                                 step=0.01,
                                                 help="Amount must match the flight fare exactly")
                    else:
                        st.warning("⚠️ Ticket not found or doesn't belong to you")
                        amount = st.number_input("Amount (₹)", min_value=0.0, value=0.0, step=0.01)
                else:
                    amount = st.number_input("Amount (₹)", min_value=0.0, value=0.0, step=0.01)

                method = st.selectbox("Payment Method",
                                      ["credit_card", "upi", "debit_card", "netbanking", "cash"])

                if st.form_submit_button("💳 Pay Now"):
                    if amount <= 0:
                        st.error("❌ Please enter a valid amount")
                    else:
                        success, message = make_payment(ticket_id_input, amount, method, st.session_state.user_id)
                        if success:
                            st.success(f"✅ {message}")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")

        with tabs[4]:
            st.subheader("My Payment History")
            columns, payments = view_user_payments(st.session_state.user_id)
            if payments:
                st.dataframe(pd.DataFrame(payments, columns=columns), use_container_width=True)
            else:
                st.info("No payment history yet")
