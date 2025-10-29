from database import get_auth_connection, get_airline_connection, hash_password

def verify_admin(username, password):
    conn = get_auth_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT password_hash FROM admin_user WHERE username = %s
    """, (username,))

    result = cur.fetchone()
    cur.close()
    conn.close()

    if result:
        return result[0] == hash_password(password)
    return False

def register_user_credentials(passanger_id, email, password):
    conn = get_auth_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO user_credentials (passanger_id, email, password_hash)
            VALUES (%s, %s, %s)
        """, (passanger_id, email, hash_password(password)))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return False


def verify_user_login(email, password):
    conn = get_auth_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT passanger_id, password_hash 
        FROM user_credentials 
        WHERE email = %s
    """, (email,))

    result = cur.fetchone()
    cur.close()
    conn.close()

    if result and result[1] == hash_password(password):
        return True, result[0]  # Return passenger_id
    return False, None


def check_email_exists(email):
    """Check if email already exists in auth database"""
    conn = get_auth_connection()
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM user_credentials WHERE email = %s", (email,))
    result = cur.fetchone()

    cur.close()
    conn.close()
    return result is not None
