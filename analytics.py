from db import get_connection
import json

def increment_hourly_analytics(url_id: str, fingerprint: str, suspicious: bool):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # truncate timestamp to hour
        cursor.execute("""
            INSERT INTO url_analytics_hourly (url_id, date_hour, clicks, unique_visitors, suspicious_clicks)
            VALUES (%s, DATE_FORMAT(NOW(), '%%Y-%%m-%%d %%H:00:00'), 1, 1, %s)
            ON DUPLICATE KEY UPDATE
                clicks = clicks + 1,
                unique_visitors = unique_visitors + (CASE WHEN NOT EXISTS (
                    SELECT 1 FROM url_clicks WHERE url_id=%s AND fingerprint=%s
                ) THEN 1 ELSE 0 END),
                suspicious_clicks = suspicious_clicks + %s
        """, (url_id, int(suspicious), url_id, fingerprint, int(suspicious)))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def update_user_sequence(fingerprint:str,url_code:str,max_length:int=10):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT sequence FROM user_sequences WHERE fingerprint=%s", (fingerprint,))
        row = cursor.fetchone()
        sequence = row['sequence'] if row else []
        if url_code not in sequence:
            sequence.append(url_code)
        sequence = sequence[-max_length:]
        if row:
            cursor.execute("UPDATE user_sequences SET sequence=%s, last_update=NOW() WHERE fingerprint=%s",
                           (json.dumps(sequence), fingerprint))
        else:
            cursor.execute("INSERT INTO user_sequences (fingerprint, sequence) VALUES (%s, %s)",
                           (fingerprint, json.dumps(sequence)))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
