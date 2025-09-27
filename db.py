from mysql.connector import pooling
import redis
from consts import REDIS_HOST,DB_DATABASE,DB_HOST,DB_PASSWORD,DB_USER,REDIS_PORT

# MySQL connection pool
MYSQL_POOL = pooling.MySQLConnectionPool(
    pool_name="mysql_pool",
    pool_size=10,  # Adjust based on expected load
    pool_reset_session=True,
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_DATABASE,
)

redis_pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=0,
    decode_responses=True,
)

redis_client = redis.Redis(connection_pool=redis_pool)

def get_connection():
    """
    Get a connection from the pool
    """
    return MYSQL_POOL.get_connection()