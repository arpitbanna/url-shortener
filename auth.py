import jwt
import bcrypt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import validators

JWT_SECRET = os.environ.get("JWT_SECRET", "secret")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_EXP_DELTA = 3600  # 1 hour
JWT_SES_EXP_DELTA=3600*24*30


# ---------------------------
# Password Hashing
# ---------------------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


# ---------------------------
# JWT Helpers
# ---------------------------
def create_access_token(user_id:str)->str:
    payload = {
        "sub": user_id,  # subject = user id
        "exp": datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA),
        "type": "access",
    }
    return jwt.encode(payload,JWT_SECRET,algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id:str)->str:
    payload = {
        "sub": user_id,  # subject = user id
        "exp": datetime.utcnow() + timedelta(seconds=JWT_SES_EXP_DELTA),
        "type": "refresh",
    }
    return jwt.encode(payload,JWT_SECRET,algorithm=JWT_ALGORITHM)

def decode_jwt(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ---------------------------
# JWT Decorator
# ---------------------------
def jwt_required(token_type: str = "access"):
    """
    token_type: "access" or "refresh"
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return jsonify({"error": "Authorization header missing"}), 401

            token = auth_header[7:] if auth_header.startswith("Bearer ") else None
            if not token:
                return jsonify({"error": "Invalid or expired token"}), 401

            payload = decode_jwt(token)
            if not payload:
                return jsonify({"error": "Invalid or expired token"}), 401

            # Check the token type
            if payload.get("type") != token_type:
                return jsonify({"error": f"Expected {token_type} token"}), 401

            # Attach user_id for route handlers
            request.environ["user_id"] = payload["sub"]

            return f(*args, **kwargs)
        return decorated
    return decorator