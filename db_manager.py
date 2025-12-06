import psycopg2
import datetime

# Database Config
DB_CONFIG = {
    "dbname": "smart_city_db",
    "user": "admin",
    "password": "password123",
    "host": "127.0.0.1",
    "port": "5435"
}

class DatabaseHandler:
    def __init__(self):
        self.conn = None
        self.create_table()

    def get_connection(self):
        try:
            if self.conn is None or self.conn.closed:
                self.conn = psycopg2.connect(**DB_CONFIG)
                self.conn.autocommit = True
            return self.conn
        except Exception as e:
            print(f"❌ DB Connection Failed: {e}")
            return None

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS footfall_logs (
            id SERIAL PRIMARY KEY,
            event_type VARCHAR(10),
            tracker_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        conn = self.get_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute(query)
            print("✅ Database & Table Ready.")

    def get_last_max_id(self):
        """Fetches the highest tracker_id ever recorded to handle restarts"""
        query = "SELECT MAX(tracker_id) FROM footfall_logs"
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(query)
                    result = cur.fetchone()[0]
                    # If table is empty, result is None, so return 0
                    return result if result is not None else 0
            except Exception as e:
                print(f"⚠️ Could not fetch max ID: {e}")
                return 0
        return 0

    def log_event(self, event_type, tracker_id):
        query = "INSERT INTO footfall_logs (event_type, tracker_id) VALUES (%s, %s)"
        conn = self.get_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(query, (event_type, tracker_id))
                print(f"💾 Saved to DB: {event_type} (ID: {tracker_id})")
            except Exception as e:
                print(f"⚠️ Insert Failed: {e}")