import logging
from flask import Flask, request, jsonify, redirect
from typing import Optional, TypedDict, cast
import redis
import mysql.connector
import os
import nanoid
from uuid import uuid4
from auth import hash_password, check_password, create_refresh_token, create_access_token, jwt_required
import validators
from errors import handle_errors, APIError

# ---------------------------
# Logging setup
# ---------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

RATE_LIMIT = 10 

# ---------------------------
# TypedDicts for MySQL rows
# ---------------------------
class UserRow(TypedDict):
    id: str
    username: str
    password_hash: str  # stored in DB


class URLRow(TypedDict):
    id: str
    code: str
    original_url: str
    clicks: int
    user_id: int


# ---------------------------
# App + Config
# ---------------------------
app = Flask(__name__)

# Redis client
redis_client = redis.Redis(
    host=os.environ.get("REDIS_HOST", "redis"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True,
)

# MySQL connection
conn = mysql.connector.connect(
    host=os.environ.get("MYSQL_HOST", "db"),
    user=os.environ.get("MYSQL_USER", "root"),
    password=os.environ.get("MYSQL_PASSWORD", "password"),
    database=os.environ.get("MYSQL_DB", "urlshortener"),
)
cursor = conn.cursor(dictionary=True)


# ---------------------------
# Rate limiting helper
# ---------------------------
def check_rate_limit(user_id: str) -> bool:
    key = f"rate:{user_id}"
    current: Optional[int] = redis_client.get(key)  # type: ignore
    if current is None:
        redis_client.set(key, 1, ex=60)
        logger.info(f"Rate limit: new counter for user {user_id}")
        return True
    elif int(current) < RATE_LIMIT:
        redis_client.incr(key)
        logger.info(f"Rate limit: increment counter for user {user_id} ({int(current)+1})")
        return True
    logger.warning(f"Rate limit exceeded for user {user_id}")
    return False


# ---------------------------
# Auth routes
# ---------------------------
@app.route("/auth/signup", methods=["POST"])
@handle_errors
def signup():
    data = request.get_json()
    username: str = data["username"]
    password: str = data["password"]

    pw_hash = hash_password(password)

    try:
        cursor.execute(
            "INSERT INTO users (id, username, password_hash) VALUES (%s, %s, %s)",
            (str(uuid4()), username, pw_hash),
        )
        conn.commit()
        logger.info(f"User created: {username}")
        return jsonify({"msg": "User created"}), 201
    except mysql.connector.errors.IntegrityError:
        logger.warning(f"Signup failed: Username {username} already exists")
        return jsonify({"msg": "Username already exists"}), 400


@app.route("/auth/login", methods=["POST"])
@handle_errors
def login():
    data = request.get_json()
    username: str = data["username"]
    password: str = data["password"]

    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    row = cast(Optional[UserRow], cursor.fetchone())

    if not row or not check_password(password, row["password_hash"]):
        logger.warning(f"Login failed for username: {username}")
        return jsonify({"msg": "Bad credentials"}), 401

    access_token = create_access_token(row["id"])
    refresh_token = create_refresh_token(row["id"])
    logger.info(f"User logged in: {username}")
    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token
    })


@app.route("/auth/access_token", methods=["POST"])
@jwt_required(token_type="refresh")
def access_token():
    user_id = request.environ["user_id"]
    token = create_access_token(user_id)
    logger.info(f"Issued access token for user_id: {user_id}")
    return jsonify({"access_token": token})


# ---------------------------
# URL Shortener routes
# ---------------------------
@app.route("/shorten", methods=["POST"])
@jwt_required(token_type="access")
@handle_errors
def shorten_url():
    user_id: str = request.environ["user_id"]
    data = request.get_json()
    original_url: str = data["url"]
    code: str = data.get("code")

    if not check_rate_limit(user_id):
        logger.warning(f"Rate limit exceeded for user {user_id}")
        return jsonify({"error": f"Rate limit exceeded: {RATE_LIMIT} requests per minute"}), 429

    if not validators.url(original_url):
        logger.warning(f"Invalid URL submitted by user {user_id}: {original_url}")
        return jsonify({"error": "Invalid URL"}), 400

    if not code:
        code = nanoid.generate(size=8)

    cursor.execute(
        "INSERT INTO urls (id, code, original_url, user_id) VALUES (%s, %s, %s, %s)",
        (str(uuid4()), code, original_url, user_id),
    )
    conn.commit()
    redis_client.set(code, original_url, ex=86400)  # cache 1 day
    logger.info(f"URL shortened by user {user_id}: {original_url} -> {code}")

    return jsonify({"short_url": f"http://localhost:5000/{code}"})


@app.route("/<code>")
@handle_errors
def redirect_url(code: str):
    # Try Redis first
    original_url = redis_client.get(code)
    url_id = None

    # Always query DB if Redis misses
    if not original_url:
        cursor.execute("SELECT * FROM urls WHERE code=%s", (code,))
        row = cursor.fetchone()
        if not row:
            logger.warning(f"Redirect failed, code not found: {code}")
            return "URL not found", 404
        original_url = row["original_url"]
        url_id = row["id"]
        redis_client.set(code, original_url, ex=86400)
    else:
        # Even if cached, get url_id from DB
        cursor.execute("SELECT id FROM urls WHERE code=%s", (code,))
        row = cursor.fetchone()
        url_id = row["id"] if row else None

    if not url_id:
        logger.warning(f"Redirect failed, URL ID not found in DB: {code}")
        return "URL not found", 404

    # Log click
    cursor.execute(
        """INSERT INTO url_clicks (id, url_id, ip, user_agent, referrer) 
           VALUES (%s, %s, %s, %s, %s)""",
        (
            str(uuid4()),
            url_id,
            request.remote_addr,
            request.headers.get("User-Agent"),
            request.referrer,
        ),
    )
    cursor.execute("UPDATE urls SET clicks = clicks + 1 WHERE id=%s", (url_id,))
    conn.commit()
    logger.info(f"URL clicked: {code} by IP {request.remote_addr}")

    return redirect(original_url)



# ---------------------------
# Protected analytics
# ---------------------------
@app.route("/stats/<code>")
@jwt_required(token_type="access")
@handle_errors
def stats(code: str):
    user_id: str = request.environ["user_id"]

    if not check_rate_limit(user_id):
        logger.warning(f"Rate limit exceeded for stats endpoint for user {user_id}")
        return jsonify({"error": f"Rate limit exceeded: {RATE_LIMIT} requests per minute"}), 429

    cursor.execute("SELECT * FROM urls WHERE code=%s", (code,))
    row = cast(Optional[URLRow], cursor.fetchone())

    if not row or row["user_id"] != user_id:
        logger.warning(f"Stats access unauthorized for user {user_id}, code {code}")
        return jsonify({"msg": "Not found or unauthorized"}), 404

    logger.info(f"Stats retrieved for user {user_id}, code {code}")
    return jsonify({
        "original_url": row["original_url"],
        "clicks": row["clicks"],
    })


# ---------------------------
# Entry
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
