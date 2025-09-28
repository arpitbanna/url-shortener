from db import get_connection,safe_close
import json
from datetime import datetime


def increment_hourly_analytics(url_id, fingerprint, suspicious=False):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check URL exists
        cursor.execute("SELECT 1 FROM urls WHERE id = %s", (url_id,))
        if cursor.fetchone() is None:
            return

        # Current hour
        now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)

        cursor.execute("""
            INSERT INTO url_analytics_hourly (url_id, fingerprint, date_hour, clicks, suspicious_clicks)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                clicks = clicks + VALUES(clicks),
                suspicious_clicks = suspicious_clicks + VALUES(suspicious_clicks)
        """, (url_id, fingerprint, now, 1 if not suspicious else 0, 1 if suspicious else 0))
        conn.commit()
    finally:
        try:
            safe_close(conn) # type: ignore
            cursor.close() #type: ignore
        except Exception:
            pass  # Ignore connection errors on close


def update_user_sequence(fingerprint: str, url_code: str, max_length: int = 10):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT sequence FROM user_sequences WHERE fingerprint=%s", (fingerprint,))
        row = cursor.fetchone()

        # Safely load JSON
        if row and row['sequence']:
            try:
                sequence = json.loads(row['sequence'])
                if not isinstance(sequence, list):
                    sequence = [sequence]  # wrap single string into a list
            except json.JSONDecodeError:
                sequence = []
        else:
            sequence = []

        # Append new code
        if url_code not in sequence:
            sequence.append(url_code)

        # Keep only last N
        sequence = sequence[-max_length:]

        if row:
            cursor.execute(
                "UPDATE user_sequences SET sequence=%s, last_update=NOW() WHERE fingerprint=%s",
                (json.dumps(sequence), fingerprint)
            )
        else:
            cursor.execute(
                "INSERT INTO user_sequences (fingerprint, sequence) VALUES (%s, %s)",
                (fingerprint, json.dumps(sequence))
            )
        conn.commit()
    finally:
        cursor.close()
        safe_close(conn)

