import jwt
import bcrypt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from uuid import uuid4
PRIVATE_KEY = open(os.environ.get("JWT_PRIVATE_KEY", "private.pem"), "r").read()
PUBLIC_KEY = open(os.environ.get("JWT_PUBLIC_KEY", "public.pem"), "r").read()

JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "RS256")
JWT_EXP_DELTA = 900   # 15 minutes for access tokens
JWT_SES_EXP_DELTA = 3600 * 24 * 30  # 30 days for refresh tokens
JWT_ISSUER = os.environ.get("JWT_ISSUER","example.com")
JWT_AUDIENCE = os.environ.get("JWT_AUDIENCE","example.com")

# ---------------------------
# Password Hashing
# ---------------------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())

def hash_token(token:str)->str:
    return bcrypt.hashpw(token.encode(),bcrypt.gensalt()).decode()

# ---------------------------
# JWT Helpers
# ---------------------------
def create_access_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": datetime.utcnow(),
        "nbf": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(seconds=JWT_EXP_DELTA),
        "jti": str(uuid4()),  # unique token ID
        "type": "access",
    }
    return jwt.encode(payload, PRIVATE_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str,jti:str) -> str:
    payload = {
        "sub": user_id,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": datetime.utcnow(),
        "nbf": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(seconds=JWT_SES_EXP_DELTA),
        "jti": jti,
        "type": "refresh",
    }
    return jwt.encode(payload, PRIVATE_KEY, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str):
    try:
        return jwt.decode(
            token,
            PUBLIC_KEY,
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            audience=JWT_AUDIENCE,
        )
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
            request.environ["claims"]=payload

            return f(*args, **kwargs)
        return decorated
    return decorator