from db import redis_client
from typing import Optional
from consts import (
    MAX_CLICKS_PER_MINUTE_PER_IP,MAX_CLICKS_PER_MINUTE_PER_IP_URL,
    RATE_THRESHOLD,UNUSUAL_USER_AGENTS,VELOCITY_THRESHOLD,
    WINDOW_SECONDS,MAX_CLICKS_PER_WINDOW,MAX_SEQUENCE_LENGTH
)
import hashlib
from flask import request
from metrics import SUSPICIOUS_IP_URLS,SUSPICIOUS_IPS,SUSPICIOUS_REQUESTS
import time

def get_fingerprint() -> str:
    """Generate a simple fingerprint for a visitor."""
    ip = request.remote_addr or ""
    user_agent = request.headers.get("User-Agent", "")
    referrer = request.referrer or ""
    accept_lang = request.headers.get("Accept-Language", "")
    
    raw_string = f"{ip}|{user_agent}|{referrer}|{accept_lang}"
    fingerprint = hashlib.sha256(raw_string.encode()).hexdigest()
    return fingerprint



def is_fraud(ip: str, url_code: str, user_agent: Optional[str], referrer: Optional[str]) -> bool:
    """
    Combine suspicious heuristics and IP/url fraud detection.
    Returns True if any fraud or suspicious condition is triggered.
    """
    suspicious = False

    # --- Rate per IP ---
    rate_key = f"suspicious_rate:{ip}"
    current: Optional[int] = redis_client.get(rate_key) # type: ignore
    count = int(current) if current else 0
    if count > RATE_THRESHOLD:
        SUSPICIOUS_REQUESTS.labels(type="ip_rate_threshold").inc()
        suspicious = True

    # --- Unusual User-Agent ---
    if user_agent:
        ua = user_agent.lower()
        if any(bot in ua for bot in UNUSUAL_USER_AGENTS):
            SUSPICIOUS_REQUESTS.labels(type="unusual_user_agent").inc()
            suspicious = True

    # --- Referrer checks ---
    if not referrer:
        SUSPICIOUS_REQUESTS.labels(type="missing_referrer").inc()
        suspicious = True
    elif len(referrer) > 200:
        SUSPICIOUS_REQUESTS.labels(type="long_referrer").inc()
        suspicious = True

    # --- IP click count ---
    ip_key = f"fraud:ip:{ip}"
    ip_clicks: Optional[int] = redis_client.get(ip_key) # type: ignore
    if ip_clicks is None:
        redis_client.set(ip_key, 1, ex=60)
    else:
        ip_clicks = int(ip_clicks) + 1
        redis_client.set(ip_key, ip_clicks, ex=60)
        if ip_clicks > MAX_CLICKS_PER_MINUTE_PER_IP:
            SUSPICIOUS_REQUESTS.labels(type="ip_clicks").inc()
            suspicious = True

    # --- IP+URL click count ---
    ip_url_key = f"fraud:ip_url:{ip}:{url_code}"
    ip_url_clicks: Optional[int] = redis_client.get(ip_url_key) # pyright: ignore[reportAssignmentType]
    if ip_url_clicks is None:
        redis_client.set(ip_url_key, 1, ex=60)
    else:
        ip_url_clicks = int(ip_url_clicks) + 1
        redis_client.set(ip_url_key, ip_url_clicks, ex=60)
        if ip_url_clicks > MAX_CLICKS_PER_MINUTE_PER_IP_URL:
            SUSPICIOUS_REQUESTS.labels(type="ip_url_clicks").inc()
            suspicious = True

    # --- Bot user-agent check ---
    if user_agent and "bot" in user_agent.lower():
        SUSPICIOUS_REQUESTS.labels(type="bot_user_agent").inc()
        suspicious = True

    # --- Update counter for rate per IP ---
    redis_client.incr(rate_key)
    redis_client.expire(rate_key, 60)

    # --- Update Prometheus gauges ---
    SUSPICIOUS_IPS.set(len(redis_client.keys("fraud:ip:*"))) # type: ignore
    SUSPICIOUS_IP_URLS.set(len(redis_client.keys("fraud:ip_url:*"))) # type: ignore

    return suspicious

def check_velocity(fingerprint:str)->bool:
    """Return True if velocity is suspicious."""
    now=time.time()
    last_click:Optional[float]=redis_client.get(f"last_click:{fingerprint}") # type: ignore
    click_count:Optional[int]=redis_client.get(f"click_count:{fingerprint}") # type: ignore
    last_click = float(last_click) if last_click else 0
    click_count = int(click_count) if click_count else 0
    # Measure interval between clicks
    interval = now - last_click
    if interval < VELOCITY_THRESHOLD:
        return True  # too fast
    # Increment click count and store expiration
    click_count += 1
    redis_client.set(f"click_count:{fingerprint}", click_count, ex=WINDOW_SECONDS)
    redis_client.set(f"last_click:{fingerprint}", now, ex=WINDOW_SECONDS)

    if click_count > MAX_CLICKS_PER_WINDOW:
        return True  # too many clicks in window
    return False

def check_behavior(fingerprint:str,url_code:str)->bool:
    """Return True if behavior is suspicious."""
    key = f"behavior_seq:{fingerprint}"
    seq= redis_client.lrange(key, 0, -1)
    #Add current url
    redis_client.rpush(key,url_code)
    redis_client.ltrim(key,-MAX_SEQUENCE_LENGTH,-1)
    redis_client.expire(key,60)
    # If the sequence is too repetitive or random,flag
    if len(seq)>=MAX_SEQUENCE_LENGTH: # type: ignore
        # simple check: all URLs identical
        if all(u == url_code for u in seq): # type: ignore
            return True
    return False