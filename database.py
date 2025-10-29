import psycopg2
import hashlib
from db_config import AIRLINE_DB_CONFIG, AUTH_DB_CONFIG, POSTGRES_DEFAULT_CONFIG


def get_airline_connection():
    return psycopg2.connect(**AIRLINE_DB_CONFIG)


def get_auth_connection():
    return psycopg2.connect(**AUTH_DB_CONFIG)

def create_auth_database():
    try:
        # Connect to default postgres database
        conn = psycopg2.connect(**POSTGRES_DEFAULT_CONFIG)
        conn.autocommit = True
        cur = conn.cursor()

        # Create database if not exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname='airline_auth_db'")
        if not cur.fetchone():
            cur.execute("CREATE DATABASE airline_auth_db")
            print("✅ Authentication database created")

        cur.close()
        conn.close()

        # Create tables in auth database
        conn = get_auth_connection()
        cur = conn.cursor()

        # Single admin table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS admin_user (
                admin_id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # User credentials table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_credentials (
                user_cred_id SERIAL PRIMARY KEY,
                passanger_id INTEGER UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        conn.commit()
        cur.close()
        conn.close()
        print("✅ Authentication tables created")

    except Exception as e:
        print(f"Error creating auth database: {e}")


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def initialize_single_admin():
    conn = get_auth_connection()
    cur = conn.cursor()

    try:
        cur.execute("DELETE FROM admin_user")

        cur.execute("""
            INSERT INTO admin_user (username, password_hash)
            VALUES (%s, %s)
        """, ("admin", hash_password("Rssb@1909")))

        conn.commit()
        print("✅ Single admin account initialized (username: admin, password: Rssb@1909)")
    except Exception as e:
        conn.rollback()
        print(f"Error initializing admin: {e}")
    finally:
        cur.close()
        conn.close()
if __name__ == "__main__":
    create_auth_database()
    initialize_single_admin()
