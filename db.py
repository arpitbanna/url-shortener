import os
import logging
from mysql.connector import pooling, errors as mysql_errors
import redis
import mysql.connector
from consts import REDIS_HOST, DB_DATABASE, DB_HOST, DB_PASSWORD, DB_USER, REDIS_PORT

logger = logging.getLogger(__name__)

# Environment-configurable pool size (default 4)
DEFAULT_POOL_SIZE = int(os.getenv("MYSQL_POOL_SIZE", "4"))

# Globals (per-process)
_mysql_pool = None
_mysql_pool_pid = None

def _ensure_pool():
    global _mysql_pool, _mysql_pool_pid
    pid = os.getpid()
    if _mysql_pool is None or _mysql_pool_pid != pid:
        pool_name = f"mysql_pool_{pid}"
        logger.info("Creating MySQL pool for pid=%s (pool_name=%s, size=%s)", pid, pool_name, DEFAULT_POOL_SIZE)
        _mysql_pool = pooling.MySQLConnectionPool(
            pool_name=pool_name,
            pool_size=DEFAULT_POOL_SIZE,
            pool_reset_session=True,
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE,
            connection_timeout=10,
        )
        _mysql_pool_pid = pid

def get_connection():
    """
    Returns a *fresh* connection from a pool created in THIS process.
    Safe to call from Celery prefork worker processes.
    """
    _ensure_pool()
    try:
        conn = _mysql_pool.get_connection() # type: ignore
    except mysql_errors.PoolError as e:
        # fallback: try a direct connection if pool creation failed unexpectedly
        logger.exception("Pool get_connection failed, creating direct connection: %s", e)
        conn = mysql.connector.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_DATABASE, connection_timeout=10
        )
    # quick ping/reconnect if needed
    try:
        conn.ping(reconnect=True, attempts=3, delay=1)
    except Exception:
        try:
            conn.reconnect(attempts=3, delay=1)
        except Exception:
            logger.exception("Failed to ping/reconnect connection")
            # let caller handle exception
            raise
    return conn

def safe_close(conn):
    if not conn:
        return
    try:
        conn.close()
    except Exception:
        # reset_session() or close may fail if connection already died on server side
        logger.debug("Ignoring exception on conn.close()", exc_info=True)


# --- Redis Connection ---
redis_pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=0,
    decode_responses=True,
)

redis_client = redis.Redis(connection_pool=redis_pool)
