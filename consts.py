import os
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

#Redis  
REDIS_HOST=os.environ.get("REDIS_HOST", "redis")
REDIS_PORT=int(os.environ.get("REDIS_PORT", 6379))

#Database
DB_HOST=os.environ.get("MYSQL_HOST", "db")
DB_USER=os.environ.get("MYSQL_USER", "root")
DB_PASSWORD=os.environ.get("MYSQL_PASSWORD", "example")
DB_DATABASE=os.environ.get("MYSQL_DB", "urlshortener")

#Rate limiting
RATE_LIMIT = 10 

# Config thresholds
MAX_CLICKS_PER_MINUTE_PER_IP = 10
MAX_CLICKS_PER_MINUTE_PER_IP_URL = 5
RATE_THRESHOLD = 10          # clicks per minute per IP
UNUSUAL_USER_AGENTS = ["python-requests", "curl", "bot", "spider"]
VELOCITY_THRESHOLD = 1.0  # seconds between clicks
MAX_CLICKS_PER_WINDOW = 5
WINDOW_SECONDS = 10
MAX_SEQUENCE_LENGTH = 5
