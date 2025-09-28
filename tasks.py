import logging
import json
from uuid import uuid4
from datetime import datetime

from celery import Celery
from celery.schedules import crontab
import geoip2.database
import user_agents

from db import get_connection, redis_client,safe_close
from consts import REDIS_HOST, REDIS_PORT
from fraud import is_fraud, check_velocity, check_behavior
from metrics import (
    UNIQUE_VISITORS,
    TOP_REFERRERS,
    CLICKS_BY_COUNTRY,
    CLICKS_BY_DEVICE,
    CLICKS_BY_BROWSER,
    CLICKS_BY_HOUR,
    SUSPICIOUS_CLICKS,
    SUSPICIOUS_IP_URLS,
    SUSPICIOUS_IPS,
    SUSPICIOUS_REQUESTS
)
from analytics import increment_hourly_analytics, update_user_sequence

# ---------- Logging ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- Celery ----------
celery = Celery("tasks", broker=f"redis://{REDIS_HOST}:{REDIS_PORT}/0")

celery.conf.update(
    beat_schedule={
        "update-trending-scores-every-1-minute": {
            "task": "tasks.update_trending_urls",
            "schedule": crontab(minute="*/1"),
        }
    },
    timezone="UTC",
)

# ---------- GeoIP ----------
try:
    GEOIP_READER = geoip2.database.Reader("data/GeoLite2-City.mmdb")
except FileNotFoundError:
    GEOIP_READER = None
    logger.warning("⚠️ GeoLite2-City.mmdb not found. Falling back to 'unknown' country")


def parse_user_agent(ua_string: str):
    ua = user_agents.parse(ua_string)
    if ua.is_mobile:
        device = "mobile"
    elif ua.is_tablet:
        device = "tablet"
    elif ua.is_pc:
        device = "pc"
    else:
        device = "other"
    browser = ua.browser.family.lower() or "unknown"
    return device, browser


def get_country_from_ip(ip: str) -> str:
    if not GEOIP_READER:
        return "unknown"
    try:
        response = GEOIP_READER.city(ip)
        return response.country.iso_code.lower() if response.country.iso_code else "unknown"
    except Exception:
        return "unknown"


# ---------------- Celery Tasks ----------------

@celery.task(bind=True, max_retries=3, default_retry_delay=5)
def log_click(self, url_id: str, ip: str, user_agent: str, referrer: str, fingerprint: str):
    """
    Log a click event:
    - Stores click in DB
    - Updates Prometheus metrics
    - Updates analytics
    """
    conn = None
    cursor = None
    try:
        country = get_country_from_ip(ip)
        device, browser = parse_user_agent(user_agent or "")
        click_id = str(uuid4())
        now = datetime.utcnow()
        date_str = now.strftime("%Y-%m-%d")
        hour = now.hour

        # --- DB ---
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            INSERT INTO url_clicks (id, url_id, ip, user_agent, referrer)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (click_id, url_id, ip, user_agent, referrer)
        )
        cursor.execute(
            "UPDATE urls SET clicks = clicks + 1 WHERE id=%s",
            (url_id,)
        )
        conn.commit()

        # --- Metrics ---
        UNIQUE_VISITORS.labels(url=url_id, date=date_str).inc()
        if referrer:
            TOP_REFERRERS.labels(url=url_id, referrer=referrer).inc()
        CLICKS_BY_COUNTRY.labels(url=url_id, country=country).inc()
        CLICKS_BY_DEVICE.labels(url=url_id, device=device).inc()
        CLICKS_BY_BROWSER.labels(url=url_id, browser=browser).inc()
        CLICKS_BY_HOUR.labels(url=url_id).observe(hour)

        # --- Analytics ---
        increment_hourly_analytics(url_id, fingerprint, suspicious=False)
        update_user_sequence(fingerprint, url_id)

    except Exception as e:
        logger.error(f"Error logging click: {e}", exc_info=True)
        raise self.retry(exc=e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@celery.task(bind=True, max_retries=3, default_retry_delay=5)
def check_fraud(self, ip: str, url_id: str, user_agent: str, referrer: str, fingerprint: str):
    """
    Detect suspicious activity:
    - Checks heuristic fraud rules
    - Stores suspicious clicks
    - Updates analytics & metrics
    """
    suspicious = (
        is_fraud(ip, url_id, user_agent, referrer) or
        check_velocity(fingerprint) or
        check_behavior(fingerprint, url_id)
    )

    if suspicious:
        logger.warning(f"🚨 Suspicious click: ip={ip}, url={url_id}, fingerprint={fingerprint}")

        # --- Prometheus Metrics ---
        SUSPICIOUS_REQUESTS.labels(type="task_detected").inc()
        SUSPICIOUS_CLICKS.labels(url=url_id, type="heuristic_detected").inc()
        SUSPICIOUS_IPS.inc()
        SUSPICIOUS_IP_URLS.inc()

        # --- Store in DB ---
        conn = None
        cursor = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO suspicious_clicks
                (id, fingerprint, ip, user_agent, referrer, reason, url_code)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (str(uuid4()), fingerprint, ip, user_agent, referrer, "heuristic_detected", url_id)
            )
            conn.commit()

            # Analytics for suspicious click
            increment_hourly_analytics(url_id, fingerprint, suspicious=True)

        except Exception as e:
            logger.error(f"Error logging suspicious click: {e}", exc_info=True)
            raise self.retry(exc=e)
        finally:
            if cursor:
                cursor.close()
            if conn:
                safe_close(conn)

    return suspicious


@celery.task
def update_trending_urls(top_n: int = 20):
    """
    Updates trending URLs based on last 4 hours of hourly analytics
    Stores result in MySQL and Redis
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT url_id,
                SUM(
                    clicks * CASE
                        WHEN TIMESTAMPDIFF(HOUR, date_hour, NOW()) < 1 THEN 1
                        WHEN TIMESTAMPDIFF(HOUR, date_hour, NOW()) < 2 THEN 0.5
                        WHEN TIMESTAMPDIFF(HOUR, date_hour, NOW()) < 4 THEN 0.25
                        ELSE 0
                    END
                ) AS trending_score
            FROM url_analytics_hourly
            WHERE date_hour >= NOW() - INTERVAL 4 HOUR
            GROUP BY url_id
            ORDER BY trending_score DESC
            LIMIT %s
        """, (top_n,))
        trending = cursor.fetchall()

        for row in trending:
            cursor.execute(
                "UPDATE urls SET trending_score=%s WHERE id=%s",
                (row["trending_score"], row["url_id"])
            )
        conn.commit()

        # Store in Redis
        redis_client.set("trending_urls", json.dumps(trending))
        logger.info(f"✅ Updated trending URLs ({len(trending)} rows)")

    except Exception as e:
        logger.error(f"Error updating trending URLs: {e}", exc_info=True)
    finally:
        if cursor:
            cursor.close()
        if conn:
            safe_close(conn)
