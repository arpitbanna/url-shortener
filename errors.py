from flask import jsonify
from functools import wraps
import logging
import mysql.connector
import redis


# Custom exceptions
class APIError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

def handle_errors(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except APIError as e:
            return jsonify({"error": e.message}), e.status_code
        except mysql.connector.Error as e:
            logging.error(f"MySQL error: {e}")
            return jsonify({"error": "Internal server error"}), 500
        except redis.RedisError as e:
            logging.error(f"Redis error: {e}")
            return jsonify({"error": "Internal server error"}), 500
        except Exception as e:
            logging.exception(f"Unhandled exception: {e}")
            return jsonify({"error": "Internal server error"}), 500
    return decorated