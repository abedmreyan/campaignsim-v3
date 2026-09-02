"""Authentication helpers: password hashing, JWT access tokens, refresh
tokens, cookie handling, and the require_auth decorator.

Token strategy (spec §4):
- Access token: JWT, short TTL, httpOnly cookie `cs_access`.
- Refresh token: opaque 256-bit random string, httpOnly cookie `cs_refresh`;
  only its SHA-256 hash is stored (refresh_tokens table) so it can be revoked.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from functools import wraps

import bcrypt
import jwt
from flask import g, jsonify, request

from ..config import Config

ACCESS_COOKIE = "cs_access"
REFRESH_COOKIE = "cs_refresh"


# --- passwords ---------------------------------------------------------------

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


# --- access tokens (JWT) ------------------------------------------------------

def create_access_token(user_id) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=Config.JWT_ACCESS_TTL_MINUTES),
        "type": "access",
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")


def decode_access_token(token: str):
    """Return the user id (str) or None if invalid/expired."""
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
    if payload.get("type") != "access":
        return None
    return payload.get("sub")


# --- refresh tokens ------------------------------------------------------------

def generate_refresh_token() -> str:
    return secrets.token_urlsafe(32)  # 256 bits


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def refresh_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=Config.JWT_REFRESH_TTL_DAYS)


# --- cookies -------------------------------------------------------------------

def set_auth_cookies(response, access_token: str, refresh_token: str):
    common = dict(
        httponly=True,
        secure=Config.AUTH_COOKIE_SECURE,
        samesite=Config.AUTH_COOKIE_SAMESITE,
        path="/",
    )
    response.set_cookie(
        ACCESS_COOKIE, access_token,
        max_age=Config.JWT_ACCESS_TTL_MINUTES * 60, **common,
    )
    response.set_cookie(
        REFRESH_COOKIE, refresh_token,
        max_age=Config.JWT_REFRESH_TTL_DAYS * 86400, **common,
    )
    return response


def clear_auth_cookies(response):
    for name in (ACCESS_COOKIE, REFRESH_COOKIE):
        response.set_cookie(
            name, "", max_age=0, httponly=True,
            secure=Config.AUTH_COOKIE_SECURE,
            samesite=Config.AUTH_COOKIE_SAMESITE, path="/",
        )
    return response


# --- decorator -------------------------------------------------------------------

def require_auth(f):
    """Validate the cs_access JWT and inject g.current_user.

    Import of the User model is deferred to avoid circular imports at
    blueprint registration time.
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.cookies.get(ACCESS_COOKIE)
        user_id = decode_access_token(token) if token else None
        if not user_id:
            return jsonify({"success": False, "error": "Authentication required"}), 401

        from ..models.orm import User
        try:
            user = User.query.get(uuid.UUID(user_id))
        except (ValueError, TypeError):
            user = None
        if user is None:
            return jsonify({"success": False, "error": "Authentication required"}), 401

        g.current_user = user
        return f(*args, **kwargs)

    return wrapper
