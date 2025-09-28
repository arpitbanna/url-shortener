import pytest
from flask import Flask, jsonify, request
from auth import (
    hash_password,
    check_password,
    hash_token,
    create_access_token,
    create_refresh_token,
    decode_jwt,
    jwt_required,
    JWT_ALGORITHM,
)

# -----------------------------
# Password Hashing Tests
# -----------------------------
def test_hash_and_check_password():
    password = "supersecret"
    hashed = hash_password(password)
    assert hashed != password  # hashed should not equal plain password
    assert check_password(password, hashed) is True
    assert check_password("wrongpassword", hashed) is False

def test_hash_token_returns_string():
    token = "mytoken"
    hashed = hash_token(token)
    assert isinstance(hashed, str)
    assert hashed != token  # should be hashed

# -----------------------------
# JWT Token Tests
# -----------------------------
@pytest.fixture
def user_id():
    return "user123"

def test_create_and_decode_access_token(user_id):
    token = create_access_token(user_id)
    payload = decode_jwt(token)
    assert payload is not None
    assert payload["sub"] == user_id
    assert payload["type"] == "access"

def test_create_and_decode_refresh_token(user_id):
    jti = "unique-jti-123"
    token = create_refresh_token(user_id, jti)
    payload = decode_jwt(token)
    assert payload is not None
    assert payload["sub"] == user_id
    assert payload["jti"] == jti
    assert payload["type"] == "refresh"

def test_decode_invalid_token_returns_none():
    assert decode_jwt("invalidtoken") is None

# -----------------------------
# JWT Decorator Tests
# -----------------------------
@pytest.fixture
def app():
    app = Flask(__name__)

    @app.route("/protected")
    @jwt_required(token_type="access")
    def protected():
        return jsonify({"user_id": request.environ.get("user_id")})

    return app

def test_jwt_required_with_valid_token(app, user_id):
    client = app.test_client()
    token = create_access_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 200
    assert response.get_json()["user_id"] == user_id

def test_jwt_required_missing_header(app):
    client = app.test_client()
    response = client.get("/protected")
    assert response.status_code == 401
    assert "Authorization header missing" in response.get_json()["error"]

def test_jwt_required_wrong_token_type(app, user_id):
    client = app.test_client()
    token = create_refresh_token(user_id, "jti123")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 401
    assert "Expected access token" in response.get_json()["error"]

def test_jwt_required_invalid_token(app):
    client = app.test_client()
    headers = {"Authorization": "Bearer invalidtoken"}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 401
    assert "Invalid or expired token" in response.get_json()["error"]
