from celery import Celery
from db import get_connection
from uuid import uuid4
from consts import REDIS_HOST,REDIS_PORT
import logging
from fraud import get_fingerprint,is_fraud,check_velocity,check_behavior
from metrics import SUSPICIOUS_REQUESTS
from db import get_connection
celery = Celery('tasks', broker=f'redis://{REDIS_HOST}:{REDIS_PORT}/0')
logger = logging.getLogger(__name__)

@celery.task(bind=True, max_retries=3, default_retry_delay=5)
def log_click(self, url_id, ip, user_agent, referrer):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """INSERT INTO url_clicks (id, url_id, ip, user_agent, referrer) 
               VALUES (%s, %s, %s, %s, %s)""",
            (str(uuid4()), url_id, ip, user_agent, referrer)
        )
        cursor.execute("UPDATE urls SET clicks = clicks + 1 WHERE id=%s", (url_id,))
        conn.commit()
    except Exception as e:
        raise self.retry(exc=e)
    finally:
        cursor.close() # pyright: ignore[reportPossiblyUnboundVariable]
        conn.close() # pyright: ignore[reportPossiblyUnboundVariable]

@celery.task(bind=True, max_retries=3, default_retry_delay=5)
def check_fraud(self, ip: str, url_code: str, user_agent: str, referrer: str):
    """
    Celery task to asynchronously check if a click is suspicious/fraudulent.
    Generates a fingerprint and uses combined heuristics.
    Suspicious clicks are logged to MySQL and Prometheus.
    """
    try:
        # 1️⃣ Generate fingerprint
        fingerprint = get_fingerprint()

        # 2️⃣ Check all fraud heuristics
        suspicious = (
            is_fraud(ip, url_code, user_agent, referrer) or
            check_velocity(fingerprint) or
            check_behavior(fingerprint, url_code)
        )

        if suspicious:
            logger.warning(
                f"Suspicious/fraudulent activity detected: "
                f"ip={ip}, url={url_code}, fingerprint={fingerprint}, user_agent={user_agent}, referrer={referrer}"
            )
            SUSPICIOUS_REQUESTS.labels(type="task_detected").inc()

            # 3️⃣ Store in suspicious_clicks table
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    INSERT INTO suspicious_clicks
                    (id, fingerprint, ip, user_agent, referrer, reason, url_code)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        str(uuid4()),
                        fingerprint,
                        ip,
                        user_agent,
                        referrer,
                        "heuristic_detected",
                        url_code
                    )
                )
                conn.commit()
            finally:
                cursor.close()
                conn.close()

        return suspicious

    except Exception as e:
        logger.error(f"Error in check_fraud task: {e}")
        raise self.retry(exc=e)