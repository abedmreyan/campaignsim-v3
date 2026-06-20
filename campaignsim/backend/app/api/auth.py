"""Auth API routes: signup, login, logout, refresh, /me.

Cookies:
  cs_access  -- httpOnly, Secure, SameSite=None, 15-min TTL
  cs_refresh -- httpOnly, Secure, SameSite=None, 30-day TTL
"""

from datetime import datetime, timedelta, timezone

from flask import Blueprint, current_app, g, jsonify, make_response, request
from flask_limiter import Limiter

from app.db import db
from app.db.models import RefreshToken, User
from app.utils.auth_utils import (
    check_password,
    decode_jwt,
    encode_access_jwt,
    generate_opaque_token,
    hash_password,
    hash_token,
    require_auth,
)

auth_bp = Blueprint("auth", __name__)


def _get_real_ip():
    """Rate-limit key: prefer CF-Connecting-IP (Cloudflare Tunnel)."""
    return request.headers.get("CF-Connecting-IP") or request.remote_addr


# Limiter is initialised per-blueprint; the app-level limiter is wired in app/__init__.py
limiter = Limiter(key_func=_get_real_ip)


def _set_auth_cookies(response, access_token: str, refresh_token: str | None = None):
    """Attach httpOnly auth cookies to a response object."""
    cfg = current_app.config
    cookie_kwargs = dict(httponly=True, secure=True, samesite="None", domain=None)

    response.set_cookie(
        "cs_access",
        value=access_token,
        max_age=cfg["JWT_ACCESS_TTL_MINUTES"] * 60,
        **cookie_kwargs,
    )
    if refresh_token is not None:
        response.set_cookie(
            "cs_refresh",
            value=refresh_token,
            max_age=cfg["JWT_REFRESH_TTL_DAYS"] * 86400,
            **cookie_kwargs,
        )
    return response


def _clear_auth_cookies(response):
    """Expire both auth cookies."""
    response.set_cookie("cs_access", "", max_age=0, httponly=True, secure=True, samesite="None")
    response.set_cookie("cs_refresh", "", max_age=0, httponly=True, secure=True, samesite="None")
    return response


def _issue_tokens(user: User):
    """Create access JWT + opaque refresh token, persist refresh hash to DB."""
    cfg = current_app.config
    access = encode_access_jwt(user.id, cfg["JWT_SECRET"], cfg["JWT_ACCESS_TTL_MINUTES"])
    raw_refresh = generate_opaque_token()

    rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(raw_refresh),
        expires_at=datetime.now(timezone.utc) + timedelta(days=cfg["JWT_REFRESH_TTL_DAYS"]),
    )
    db.session.add(rt)
    db.session.commit()
    return access, raw_refresh


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@auth_bp.route("/signup", methods=["POST"])
@limiter.limit("5/minute")
def signup():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    display_name = (body.get("display_name") or "").strip()

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400
    if len(password) < 8:
        return jsonify({"error": "password must be at least 8 characters"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    user = User(
        email=email,
        password_hash=hash_password(password),
        display_name=display_name or None,
    )
    db.session.add(user)
    db.session.flush()  # get user.id before token

    access, raw_refresh = _issue_tokens(user)

    resp = make_response(
        jsonify({"user": {"id": user.id, "email": user.email, "display_name": user.display_name}}),
        201,
    )
    return _set_auth_cookies(resp, access, raw_refresh)


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("10/minute")
def login():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not check_password(password, user.password_hash):
        return jsonify({"error": "Invalid credentials"}), 401

    access, raw_refresh = _issue_tokens(user)

    resp = make_response(
        jsonify({"user": {"id": user.id, "email": user.email, "display_name": user.display_name}}),
        200,
    )
    return _set_auth_cookies(resp, access, raw_refresh)


@auth_bp.route("/logout", methods=["POST"])
@require_auth
def logout():
    raw_refresh = request.cookies.get("cs_refresh")
    if raw_refresh:
        token_hash = hash_token(raw_refresh)
        rt = RefreshToken.query.filter_by(
            user_id=g.current_user.id,
            token_hash=token_hash,
            revoked=False,
        ).first()
        if rt:
            rt.revoked = True
            db.session.commit()

    resp = make_response(jsonify({"ok": True}), 200)
    return _clear_auth_cookies(resp)


@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    raw_refresh = request.cookies.get("cs_refresh")
    if not raw_refresh:
        return jsonify({"error": "No refresh token"}), 401

    token_hash = hash_token(raw_refresh)
    now = datetime.now(timezone.utc)
    rt = RefreshToken.query.filter_by(token_hash=token_hash, revoked=False).first()

    if not rt or rt.expires_at.replace(tzinfo=timezone.utc) < now:
        return jsonify({"error": "Refresh token expired or revoked"}), 401

    cfg = current_app.config
    access = encode_access_jwt(rt.user_id, cfg["JWT_SECRET"], cfg["JWT_ACCESS_TTL_MINUTES"])

    resp = make_response(jsonify({"ok": True}), 200)
    resp.set_cookie(
        "cs_access",
        value=access,
        max_age=cfg["JWT_ACCESS_TTL_MINUTES"] * 60,
        httponly=True,
        secure=True,
        samesite="None",
        domain=None,
    )
    return resp


@auth_bp.route("/me", methods=["GET"])
@require_auth
def me():
    u = g.current_user
    return jsonify({"id": u.id, "email": u.email, "display_name": u.display_name})
