"""Auth API — signup, login, logout, refresh, me (spec §4)."""

import re
from datetime import datetime, timezone

from flask import g, jsonify, make_response, request

from . import auth_bp
from ..extensions import db, limiter
from ..models.orm import RefreshToken, User
from ..utils.auth import (
    clear_auth_cookies,
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    refresh_expiry,
    require_auth,
    set_auth_cookies,
    REFRESH_COOKIE,
)
from ..utils.logger import get_logger

logger = get_logger("campaignsim.api.auth")

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _issue_session(user: User):
    """Create access + refresh tokens, persist the refresh hash, set cookies."""
    access = create_access_token(user.id)
    refresh_raw = generate_refresh_token()
    db.session.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(refresh_raw),
        expires_at=refresh_expiry(),
    ))
    db.session.commit()

    resp = make_response(jsonify({"success": True, "user": user.to_dict()}))
    return set_auth_cookies(resp, access, refresh_raw)


@auth_bp.route("/signup", methods=["POST"])
@limiter.limit("5/minute")
def signup():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    display_name = (data.get("display_name") or "").strip() or None

    if not _EMAIL_RE.match(email):
        return jsonify({"success": False, "error": "Invalid email address"}), 400
    if len(password) < 8:
        return jsonify({"success": False, "error": "Password must be at least 8 characters"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"success": False, "error": "An account with this email already exists"}), 409

    user = User(email=email, password_hash=hash_password(password), display_name=display_name)
    db.session.add(user)
    db.session.commit()
    logger.info(f"New user signed up: {email}")
    return _issue_session(user)


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("10/minute")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not _verify(user, password):
        return jsonify({"success": False, "error": "Invalid email or password"}), 401
    return _issue_session(user)


def _verify(user: User, password: str) -> bool:
    from ..utils.auth import verify_password
    return verify_password(password, user.password_hash)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    raw = request.cookies.get(REFRESH_COOKIE)
    if raw:
        token = RefreshToken.query.filter_by(token_hash=hash_refresh_token(raw)).first()
        if token:
            token.revoked = True
            db.session.commit()
    resp = make_response(jsonify({"success": True}))
    return clear_auth_cookies(resp)


@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    raw = request.cookies.get(REFRESH_COOKIE)
    if not raw:
        return jsonify({"success": False, "error": "No refresh token"}), 401

    token = RefreshToken.query.filter_by(token_hash=hash_refresh_token(raw)).first()
    now = datetime.now(timezone.utc)
    expires_at = token.expires_at if token else None
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if not token or token.revoked or (expires_at and expires_at < now):
        resp = make_response(jsonify({"success": False, "error": "Invalid refresh token"}))
        clear_auth_cookies(resp)
        return resp, 401

    user = User.query.get(token.user_id)
    if not user:
        return jsonify({"success": False, "error": "Invalid refresh token"}), 401

    # Rotate: revoke the used token, issue a fresh pair.
    token.revoked = True
    db.session.commit()
    return _issue_session(user)


@auth_bp.route("/me", methods=["GET"])
@require_auth
def me():
    return jsonify({"success": True, "user": g.current_user.to_dict()})
