"""Auth utility functions: JWT encode/decode, password hashing, token hashing,
and the require_auth Flask decorator.

JWT algorithm is always HS256 — never rely on library defaults.
"""

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps

import bcrypt
import jwt
from flask import current_app, g, jsonify, request


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def encode_access_jwt(user_id: str, secret: str, ttl_minutes: int) -> str:
    """Encode a short-lived access JWT. Algorithm: HS256 (explicit)."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=ttl_minutes),
        "type": "access",
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_jwt(token: str, secret: str) -> dict:
    """Decode and verify a JWT. Raises ValueError on invalid or expired tokens."""
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.InvalidTokenError as exc:
        raise ValueError(f"Invalid token: {exc}")


# ---------------------------------------------------------------------------
# Token hashing (for refresh tokens stored in DB)
# ---------------------------------------------------------------------------

def generate_opaque_token() -> str:
    """Generate a 256-bit cryptographically random opaque token."""
    return secrets.token_hex(32)


def hash_token(raw: str) -> str:
    """SHA-256 hex digest of a raw token. This is what gets stored in DB."""
    return hashlib.sha256(raw.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    """bcrypt hash a plaintext password. Returns a string."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def check_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ---------------------------------------------------------------------------
# Flask decorator
# ---------------------------------------------------------------------------

def require_auth(f):
    """Flask route decorator.

    Validates the cs_access JWT cookie, loads the User from DB,
    and injects it into flask.g.current_user.

    Returns 401 JSON on missing/invalid/expired token.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get("cs_access")
        if not token:
            return jsonify({"error": "Authentication required"}), 401

        secret = current_app.config["JWT_SECRET"]
        try:
            payload = decode_jwt(token, secret)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 401

        from app.db.models import User
        from app.db import db

        user = db.session.get(User, payload["sub"])
        if not user:
            return jsonify({"error": "User not found"}), 401

        g.current_user = user
        return f(*args, **kwargs)

    return decorated
