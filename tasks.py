from celery import Celery
from db import get_connection,redis_client
from uuid import uuid4
from consts import REDIS_HOST, REDIS_PORT
import logging
import json
from fraud import get_fingerprint, is_fraud, check_velocity, check_behavior
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
import geoip2.database
import user_agents
from datetime import datetime
from celery.schedules import crontab


celery = Celery('tasks', broker=f'redis://{REDIS_HOST}:{REDIS_PORT}/0')
logger = logging.getLogger(__name__)
celery.conf.update(
       beat_schedule={
        'update-trending-scores-every-5-minutes': {
            'task': 'tasks.update_trending_urls',
            'schedule': crontab(minute='*/30'),
        }
    },
    timezone='UTC',
)
# GeoIP reader
GEOIP_READER = geoip2.database.Reader('data/GeoLite2-City.mmdb')


def parse_user_agent(ua_string: str):
    ua = user_agents.parse(ua_string)
    # return normalized device + browser
    device = "other"
    if ua.is_mobile:
        device = "mobile"
    elif ua.is_tablet:
        device = "tablet"
    elif ua.is_pc:
        device = "pc"
    browser = ua.browser.family.lower() or "unknown"
    return device, browser


def get_country_from_ip(ip: str) -> str:
    try:
        response = GEOIP_READER.city(ip)
        return response.country.iso_code.lower() if response.country.iso_code else "unknown"
    except Exception:
        return "unknown"


@celery.task(bind=True, max_retries=3, default_retry_delay=5)
def log_click(self, url_id: str, ip: str, user_agent: str, referrer: str):
    try:
        country = get_country_from_ip(ip)
        device, browser = parse_user_agent(user_agent or "")

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        click_id = str(uuid4())

        # DB insert
        cursor.execute(
            """
            INSERT INTO url_clicks (id, url_id, ip, user_agent, referrer)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (click_id, url_id, ip, user_agent, referrer)
        )
        cursor.execute("UPDATE urls SET clicks = clicks + 1 WHERE id=%s", (url_id,))
        conn.commit()

        # Analytics & Metrics
        now = datetime.utcnow()
        date_str = now.strftime("%Y-%m-%d")
        hour = now.hour
        fingerprint = get_fingerprint()

        # 🔹 Prometheus metrics
        UNIQUE_VISITORS.labels(url=url_id, date=date_str).inc()
        if referrer:
            TOP_REFERRERS.labels(url=url_id, referrer=referrer).inc()
        CLICKS_BY_COUNTRY.labels(url=url_id, country=country).inc()
        CLICKS_BY_DEVICE.labels(url=url_id, device=device).inc()
        CLICKS_BY_BROWSER.labels(url=url_id, browser=browser).inc()
        CLICKS_BY_HOUR.labels(url=url_id).observe(hour)

        # 🔹 Analytics tables
        increment_hourly_analytics(url_id, fingerprint, suspicious=False)
        update_user_sequence(fingerprint, url_id)

    except Exception as e:
        logger.error(f"Error logging click: {e}")
        raise self.retry(exc=e)
    finally:
        cursor.close()  # type: ignore
        conn.close()  # type: ignore


@celery.task(bind=True, max_retries=3, default_retry_delay=5)
def check_fraud(self, ip: str, url_id: str, user_agent: str, referrer: str):
    fingerprint = get_fingerprint()
    suspicious = (
        is_fraud(ip, url_id, user_agent, referrer) or
        check_velocity(fingerprint) or
        check_behavior(fingerprint, url_id)
    )

    if suspicious:
        logger.warning(f"Suspicious click detected: ip={ip}, url={url_id}, fingerprint={fingerprint}")

        # Increment general suspicious counter
        SUSPICIOUS_REQUESTS.labels(type="task_detected").inc()
        SUSPICIOUS_CLICKS.labels(url=url_id, type="heuristic_detected").inc()
        SUSPICIOUS_IPS.inc()  # Current number of suspicious IPs
        SUSPICIOUS_IP_URLS.inc()  # Current number of IP+URL combinations flagged

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

            # Analytics update
            increment_hourly_analytics(url_id, fingerprint, suspicious=True)

        except Exception as e:
            logger.error(f"Error logging suspicious click: {e}")
            raise self.retry(exc=e)
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    return suspicious


@celery.task
def update_trending_urls(top_n:int=20):
    conn=get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
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
        """)
        trending=cursor.fetchall()
        # Update DB
        for row in trending:
            cursor.execute(
                "UPDATE urls SET trending_score=%s WHERE id=%s",
                (row['trending_score'], row['url_id'])
            )
        conn.commit()
        redis_client.set("trending_urls",json.dumps(trending))
    finally:
        cursor.close()
        conn.close()    
