"""Flask extension singletons.

Kept in a separate module so blueprints and services can import them
without circular imports through app/__init__.py.
"""

from flask import request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()


def _rate_limit_key():
    """The app runs behind a Cloudflare Tunnel — request.remote_addr is always
    the tunnel's local address, which would collapse every client onto one
    rate-limit bucket. Prefer the header Cloudflare sets to the real client IP."""
    return request.headers.get("CF-Connecting-IP") or get_remote_address()


limiter = Limiter(key_func=_rate_limit_key, default_limits=[])
