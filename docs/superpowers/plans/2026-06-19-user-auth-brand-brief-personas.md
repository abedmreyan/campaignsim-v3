# User Auth, Brand Brief & Persona Management — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add user accounts with JWT auth, brand brief CRUD, and persistent persona management to CampaignSim.

**Architecture:** Flask backend gains PostgreSQL (SQLAlchemy + Alembic), JWT-in-httpOnly-cookies auth, a StorageBackend abstraction for user-scoped file paths, and new routes for auth, briefs, and personas. The Vue 3 frontend gains a Pinia authStore, an axios refresh interceptor, three new views (Login, Signup, BrandBrief), and auth-guarded routing.

**Tech Stack:** Flask, Flask-SQLAlchemy, Flask-Migrate, PyJWT, bcrypt, Flask-CORS, Flask-Limiter, PostgreSQL 16, Vue 3, Pinia, axios, Vue Router

## Global Constraints

- All code, comments, strings in English only — no Chinese characters (except `locales/zh.json`)
- Project name: **CampaignSim** — no MiroFish, no 666ghj
- Logger names: `campaignsim.*` namespace
- JWT algorithm: `HS256` — always explicit, never rely on defaults
- Refresh token stored as SHA-256 hash in DB — never the raw token
- `SameSite=None; Secure=True` cookies — required for cross-origin (port 3006 vs 5001)
- Rate limiter key: `CF-Connecting-IP` header — not `remote_addr` (all traffic is behind Cloudflare Tunnel)
- `brand_briefs.content` TEXT column is the canonical brief source of truth
- `campaigns` + `campaign_variants` tables: schema created but **zero rows written** in this phase
- After any Python file change: `python3 -m py_compile <file>`

## File Map

| Task | Files Created | Files Modified |
|------|--------------|----------------|
| 1 | `campaignsim/backend/tests/__init__.py`, `tests/conftest.py`, `campaignsim/.env.example` | `campaignsim/backend/requirements.txt`, `campaignsim/docker-compose.yml` |
| 2 | `campaignsim/backend/app/db/__init__.py`, `app/db/models.py` | `app/config.py`, `app/__init__.py` |
| 3 | `app/services/storage.py`, `tests/test_storage.py` | `app/__init__.py` |
| 4 | `app/utils/auth_utils.py`, `tests/test_auth_utils.py` | — |
| 5 | `app/api/auth.py`, `tests/test_auth_api.py` | `app/api/__init__.py`, `app/__init__.py` |
| 6 | `app/api/briefs.py`, `tests/test_briefs_api.py` | `app/api/__init__.py`, `app/__init__.py` |
| 7 | — | `app/api/graph.py`, `app/api/simulation.py`, `app/api/report.py`, `app/api/evaluation.py` |
| 8 | `tests/test_persona_api.py` | `app/api/simulation.py` |
| 9 | `frontend/src/stores/authStore.js` | `frontend/src/api/client.js`, `frontend/src/main.js` |
| 10 | `frontend/src/views/LoginView.vue`, `SignupView.vue`, `BrandBriefView.vue` | `frontend/src/router/index.js` |
| 11 | — | `frontend/src/stores/campaignStore.js`, `frontend/src/views/Step2Personas.vue` |

---

### Task 1: Infrastructure — PostgreSQL, Dependencies, Test Harness

**Files:**
- Modify: `campaignsim/docker-compose.yml`
- Modify: `campaignsim/backend/requirements.txt`
- Create: `campaignsim/.env.example`
- Create: `campaignsim/backend/tests/__init__.py`
- Create: `campaignsim/backend/tests/conftest.py`

**Interfaces:**
- Produces: `pytest` fixtures `app`, `client`, `db_session` used by all later test tasks

- [ ] **Step 1: Add PostgreSQL service to docker-compose**

Replace `campaignsim/docker-compose.yml` with:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: campaignsim
      POSTGRES_USER: cs_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U cs_user -d campaignsim"]
      interval: 5s
      timeout: 5s
      retries: 5

  campaignsim:
    build: .
    container_name: campaignsim
    env_file:
      - .env
    ports:
      - "3002:3002"
      - "5001:5001"
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./backend/uploads:/app/backend/uploads

volumes:
  pgdata:
```

- [ ] **Step 2: Add Python dependencies**

Append to `campaignsim/backend/requirements.txt`:

```
# Database
flask-sqlalchemy>=3.1
flask-migrate>=4.0
psycopg2-binary>=2.9

# Auth
bcrypt>=4.0
pyjwt>=2.8

# Rate limiting
flask-limiter>=3.5
```

- [ ] **Step 3: Create .env.example**

Create `campaignsim/.env.example`:

```
# Existing vars (keep these)
LLM_API_KEY=
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o-mini
KG_BACKEND=local
SECRET_KEY=campaignsim-secret-key

# New vars added in this phase
DATABASE_URL=postgresql://cs_user:secret@localhost:5432/campaignsim
POSTGRES_PASSWORD=secret
JWT_SECRET=replace-with-64-char-random-hex
JWT_ACCESS_TTL_MINUTES=15
JWT_REFRESH_TTL_DAYS=30
```

- [ ] **Step 4: Create test package and conftest**

Create `campaignsim/backend/tests/__init__.py` (empty):
```python
```

Create `campaignsim/backend/tests/conftest.py`:

```python
"""Shared pytest fixtures for CampaignSim backend tests."""

import os
import pytest

# Point at an in-memory SQLite database for fast, isolated tests
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-tests-only")
os.environ.setdefault("JWT_ACCESS_TTL_MINUTES", "15")
os.environ.setdefault("JWT_REFRESH_TTL_DAYS", "30")
os.environ.setdefault("LLM_API_KEY", "test-key")


@pytest.fixture()
def app():
    from app import create_app
    from app.db import db as _db

    application = create_app()
    application.config["TESTING"] = True
    application.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db_session(app):
    from app.db import db as _db
    yield _db.session
```

- [ ] **Step 5: Verify pytest is importable**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2/campaignsim/backend"
pip install -r requirements.txt
python3 -m pytest tests/ --collect-only 2>&1 | head -20
```

Expected: `no tests ran` (no test files yet) — no import errors.

- [ ] **Step 6: Commit**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2"
git add campaignsim/docker-compose.yml campaignsim/backend/requirements.txt campaignsim/.env.example campaignsim/backend/tests/
git commit -m "feat: add postgres infra, new deps, test harness"
```

---

### Task 2: SQLAlchemy Models + Alembic + App Factory Wiring

**Files:**
- Create: `campaignsim/backend/app/db/__init__.py`
- Create: `campaignsim/backend/app/db/models.py`
- Modify: `campaignsim/backend/app/config.py`
- Modify: `campaignsim/backend/app/__init__.py`

**Interfaces:**
- Produces: `from app.db import db` — SQLAlchemy instance
- Produces: `from app.db.models import User, RefreshToken, BrandBrief, Persona, Campaign, CampaignVariant, SimulationRecord`

- [ ] **Step 1: Create db package**

Create `campaignsim/backend/app/db/__init__.py`:

```python
"""SQLAlchemy database instance.

Import `db` from here in models and wherever session access is needed.
Never import db directly from flask_sqlalchemy.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
```

- [ ] **Step 2: Create ORM models**

Create `campaignsim/backend/app/db/models.py`:

```python
"""SQLAlchemy ORM models for CampaignSim.

All tables use UUID primary keys (server-generated).
SQLite (used in tests) does not have gen_random_uuid(); the Python-side
default generates the UUID instead.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Index,
    String, Text, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.types import JSON

from . import db


def _now():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


# Use JSONB on Postgres, plain JSON on SQLite (tests)
JsonColumn = JSONB().with_variant(JSON(), "sqlite")


class User(db.Model):
    __tablename__ = "users"

    id           = Column(String(36), primary_key=True, default=_uuid)
    email        = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100))
    created_at   = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at   = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    refresh_tokens = db.relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    brand_briefs   = db.relationship("BrandBrief",   back_populates="user", cascade="all, delete-orphan")


class RefreshToken(db.Model):
    __tablename__ = "refresh_tokens"
    __table_args__ = (
        Index("idx_refresh_tokens_hash", "token_hash"),
        Index("idx_refresh_tokens_user", "user_id"),
    )

    id         = Column(String(36), primary_key=True, default=_uuid)
    user_id    = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked    = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)

    user = db.relationship("User", back_populates="refresh_tokens")


class BrandBrief(db.Model):
    __tablename__ = "brand_briefs"

    id           = Column(String(36), primary_key=True, default=_uuid)
    user_id      = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name         = Column(String(255), nullable=False)
    content      = Column(Text)           # canonical editable text
    file_path    = Column(String(500))    # relative path under uploads/{user_id}/briefs/
    graph_id     = Column(String(255))    # pointer to KG directory
    graph_status = Column(String(20), default="pending", nullable=False)  # pending|building|ready|failed
    created_at   = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at   = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    user    = db.relationship("User", back_populates="brand_briefs")
    personas = db.relationship("Persona", back_populates="brand_brief", cascade="all, delete-orphan")


class Persona(db.Model):
    __tablename__ = "personas"
    __table_args__ = (
        Index("idx_personas_user_brief", "user_id", "brand_brief_id"),
    )

    id             = Column(String(36), primary_key=True, default=_uuid)
    user_id        = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    brand_brief_id = Column(String(36), ForeignKey("brand_briefs.id", ondelete="CASCADE"), nullable=False)
    external_id    = Column(String(100))   # OASIS user_id e.g. "user_042"
    segment        = Column(String(255))
    data           = Column(JsonColumn, nullable=False)
    created_at     = Column(DateTime(timezone=True), default=_now, nullable=False)

    brand_brief = db.relationship("BrandBrief", back_populates="personas")


class Campaign(db.Model):
    """Schema-only — no rows written in this phase."""
    __tablename__ = "campaigns"

    id             = Column(String(36), primary_key=True, default=_uuid)
    user_id        = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    brand_brief_id = Column(String(36), ForeignKey("brand_briefs.id"))
    brand_name     = Column(String(255))
    campaign_goal  = Column(Text)
    created_at     = Column(DateTime(timezone=True), default=_now, nullable=False)

    variants = db.relationship("CampaignVariant", back_populates="campaign", cascade="all, delete-orphan")


class CampaignVariant(db.Model):
    """Schema-only — no rows written in this phase."""
    __tablename__ = "campaign_variants"

    id             = Column(String(36), primary_key=True, default=_uuid)
    campaign_id    = Column(String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    variant_name   = Column(String(255))
    channel        = Column(String(50))
    content        = Column(JsonColumn)
    target_segment = Column(String(255))
    status         = Column(String(20), default="pending", nullable=False)
    created_at     = Column(DateTime(timezone=True), default=_now, nullable=False)

    campaign = db.relationship("Campaign", back_populates="variants")


class SimulationRecord(db.Model):
    __tablename__ = "simulations"

    id             = Column(String(36), primary_key=True, default=_uuid)
    user_id        = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    campaign_id    = Column(String(36), ForeignKey("campaigns.id"))
    brand_brief_id = Column(String(36), ForeignKey("brand_briefs.id"))
    status         = Column(String(20), default="pending", nullable=False)
    result_path    = Column(String(500))
    created_at     = Column(DateTime(timezone=True), default=_now, nullable=False)
```

- [ ] **Step 3: Add DB config vars**

Add to `campaignsim/backend/app/config.py` inside the `Config` class, after the `SECRET_KEY` line:

```python
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://cs_user:secret@localhost:5432/campaignsim'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET = os.environ.get('JWT_SECRET', 'change-me-in-production')
    JWT_ACCESS_TTL_MINUTES = int(os.environ.get('JWT_ACCESS_TTL_MINUTES', '15'))
    JWT_REFRESH_TTL_DAYS = int(os.environ.get('JWT_REFRESH_TTL_DAYS', '30'))
```

- [ ] **Step 4: Wire db + migrate into app factory**

In `campaignsim/backend/app/__init__.py`, add imports after the existing imports:

```python
from flask_migrate import Migrate
from .db import db
```

Inside `create_app`, after `app.config.from_object(config_class)` and before the logger setup, add:

```python
    # Database
    db.init_app(app)
    Migrate(app, db)

    # Import models so Alembic can see them
    from .db import models  # noqa: F401
```

Also update the CORS line to restrict origins and support credentials:

```python
    # Replace the existing CORS line:
    # CORS(app, resources={r"/api/*": {"origins": "*"}})
    # With:
    CORS(app,
         origins=[
             "http://localhost:3006",
             "https://campaignsim-v3.aethersystems.co"
         ],
         supports_credentials=True)
```

- [ ] **Step 5: Initialize Alembic and create first migration**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2/campaignsim/backend"
export FLASK_APP=run.py
flask db init
flask db migrate -m "initial schema: users, refresh_tokens, brand_briefs, personas, campaigns, simulations"
```

Expected: `migrations/` directory created; `migrations/versions/<hash>_initial_schema.py` file generated.

- [ ] **Step 6: Verify syntax**

```bash
python3 -m py_compile app/db/__init__.py app/db/models.py app/config.py app/__init__.py
echo "Syntax OK"
```

- [ ] **Step 7: Commit**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2"
git add campaignsim/backend/app/db/ campaignsim/backend/app/config.py campaignsim/backend/app/__init__.py campaignsim/backend/migrations/
git commit -m "feat: add SQLAlchemy models and Alembic migration"
```

---

### Task 3: StorageBackend Abstraction

**Files:**
- Create: `campaignsim/backend/app/services/storage.py`
- Create: `campaignsim/backend/tests/test_storage.py`
- Modify: `campaignsim/backend/app/__init__.py`

**Interfaces:**
- Produces: `current_app.storage` — a `LocalStorage` instance
- Produces: `storage.user_path(user_id, *parts) -> str` — returns absolute path
- Produces: `storage.save_file(user_id, key, data: bytes) -> str`
- Produces: `storage.load_file(user_id, key) -> bytes`
- Produces: `storage.exists(user_id, key) -> bool`

- [ ] **Step 1: Write the failing test**

Create `campaignsim/backend/tests/test_storage.py`:

```python
"""Tests for the StorageBackend abstraction."""

import os
import tempfile
import pytest
from app.services.storage import LocalStorage


@pytest.fixture()
def storage(tmp_path):
    return LocalStorage(base=str(tmp_path))


def test_user_path_includes_user_id(storage, tmp_path):
    path = storage.user_path("user-123", "knowledge_graphs", "kg-abc")
    assert "user-123" in path
    assert "knowledge_graphs" in path
    assert "kg-abc" in path


def test_save_and_load_roundtrip(storage):
    data = b"hello brief content"
    storage.save_file("user-1", "briefs/brief.txt", data)
    assert storage.load_file("user-1", "briefs/brief.txt") == data


def test_exists_returns_false_before_save(storage):
    assert storage.exists("user-1", "briefs/missing.txt") is False


def test_exists_returns_true_after_save(storage):
    storage.save_file("user-1", "briefs/file.txt", b"x")
    assert storage.exists("user-1", "briefs/file.txt") is True


def test_delete_file(storage):
    storage.save_file("user-1", "briefs/del.txt", b"delete me")
    storage.delete_file("user-1", "briefs/del.txt")
    assert storage.exists("user-1", "briefs/del.txt") is False


def test_save_creates_intermediate_directories(storage):
    storage.save_file("user-1", "deep/nested/dir/file.bin", b"data")
    assert storage.exists("user-1", "deep/nested/dir/file.bin") is True
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2/campaignsim/backend"
python3 -m pytest tests/test_storage.py -v 2>&1 | head -30
```

Expected: `ImportError` — `app.services.storage` does not exist yet.

- [ ] **Step 3: Implement StorageBackend**

Create `campaignsim/backend/app/services/storage.py`:

```python
"""Storage abstraction for user-scoped file I/O.

LocalStorage stores files at {base}/{user_id}/{key}.
An S3Storage class can implement the same interface later without
touching any service code — just swap the registered backend.
"""

import os
import shutil


class StorageBackend:
    """Interface definition. Subclasses must implement all methods."""

    def save_file(self, user_id: str, key: str, data: bytes) -> str:
        """Write bytes to storage. Returns the resolved path/URL."""
        raise NotImplementedError

    def load_file(self, user_id: str, key: str) -> bytes:
        """Read bytes from storage."""
        raise NotImplementedError

    def delete_file(self, user_id: str, key: str) -> None:
        """Delete a file. No-op if the file does not exist."""
        raise NotImplementedError

    def exists(self, user_id: str, key: str) -> bool:
        """Return True if the file exists."""
        raise NotImplementedError

    def user_path(self, user_id: str, *parts: str) -> str:
        """Return the full local path for a user-scoped resource."""
        raise NotImplementedError


class LocalStorage(StorageBackend):
    """Stores files at {base}/{user_id}/{key} on the local filesystem."""

    def __init__(self, base: str):
        self.base = os.path.abspath(base)

    def user_path(self, user_id: str, *parts: str) -> str:
        return os.path.join(self.base, user_id, *parts)

    def _full_path(self, user_id: str, key: str) -> str:
        return os.path.join(self.base, user_id, key)

    def save_file(self, user_id: str, key: str, data: bytes) -> str:
        path = self._full_path(user_id, key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        return path

    def load_file(self, user_id: str, key: str) -> bytes:
        with open(self._full_path(user_id, key), "rb") as f:
            return f.read()

    def delete_file(self, user_id: str, key: str) -> None:
        path = self._full_path(user_id, key)
        if os.path.exists(path):
            os.remove(path)

    def exists(self, user_id: str, key: str) -> bool:
        return os.path.exists(self._full_path(user_id, key))
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2/campaignsim/backend"
python3 -m pytest tests/test_storage.py -v
```

Expected: all 6 tests PASS.

- [ ] **Step 5: Register storage in app factory**

In `campaignsim/backend/app/__init__.py`, after the `db.init_app(app)` lines, add:

```python
    # Storage backend — user-scoped file I/O
    from .services.storage import LocalStorage
    app.storage = LocalStorage(base=app.config['UPLOAD_FOLDER'])
```

- [ ] **Step 6: Verify syntax**

```bash
python3 -m py_compile app/services/storage.py app/__init__.py
echo "Syntax OK"
```

- [ ] **Step 7: Commit**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2"
git add campaignsim/backend/app/services/storage.py campaignsim/backend/app/__init__.py campaignsim/backend/tests/test_storage.py
git commit -m "feat: add LocalStorage backend abstraction (6 tests pass)"
```

---

### Task 4: Auth Utilities

**Files:**
- Create: `campaignsim/backend/app/utils/auth_utils.py`
- Create: `campaignsim/backend/tests/test_auth_utils.py`

**Interfaces:**
- Produces: `encode_access_jwt(user_id, secret, ttl_minutes) -> str`
- Produces: `decode_jwt(token, secret) -> dict` — raises `ValueError` on invalid/expired
- Produces: `hash_token(raw: str) -> str` — SHA-256 hex digest
- Produces: `check_password(plain: str, hashed: str) -> bool`
- Produces: `hash_password(plain: str) -> str`
- Produces: `require_auth` — Flask decorator injecting `g.current_user`

- [ ] **Step 1: Write the failing tests**

Create `campaignsim/backend/tests/test_auth_utils.py`:

```python
"""Tests for auth utility functions."""

import time
import pytest
from app.utils.auth_utils import (
    encode_access_jwt,
    decode_jwt,
    hash_token,
    hash_password,
    check_password,
)

SECRET = "test-secret"


def test_encode_decode_roundtrip():
    token = encode_access_jwt("user-1", SECRET, ttl_minutes=15)
    payload = decode_jwt(token, SECRET)
    assert payload["sub"] == "user-1"


def test_decode_expired_token_raises():
    token = encode_access_jwt("user-1", SECRET, ttl_minutes=0)
    time.sleep(1)
    with pytest.raises(ValueError, match="expired"):
        decode_jwt(token, SECRET)


def test_decode_wrong_secret_raises():
    token = encode_access_jwt("user-1", SECRET, ttl_minutes=15)
    with pytest.raises(ValueError):
        decode_jwt(token, "wrong-secret")


def test_hash_token_is_deterministic():
    assert hash_token("abc") == hash_token("abc")


def test_hash_token_differs_from_raw():
    raw = "my-refresh-token"
    assert hash_token(raw) != raw


def test_password_roundtrip():
    hashed = hash_password("my-password")
    assert check_password("my-password", hashed) is True
    assert check_password("wrong-password", hashed) is False
```

- [ ] **Step 2: Run to verify failure**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2/campaignsim/backend"
python3 -m pytest tests/test_auth_utils.py -v 2>&1 | head -20
```

Expected: `ImportError` — module does not exist.

- [ ] **Step 3: Implement auth utilities**

Create `campaignsim/backend/app/utils/auth_utils.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2/campaignsim/backend"
python3 -m pytest tests/test_auth_utils.py -v
```

Expected: all 6 tests PASS.

- [ ] **Step 5: Verify syntax**

```bash
python3 -m py_compile app/utils/auth_utils.py
echo "Syntax OK"
```

- [ ] **Step 6: Commit**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2"
git add campaignsim/backend/app/utils/auth_utils.py campaignsim/backend/tests/test_auth_utils.py
git commit -m "feat: add auth utilities (JWT, bcrypt, require_auth) — 6 tests pass"
```

---

### Task 5: Auth API Routes

**Files:**
- Create: `campaignsim/backend/app/api/auth.py`
- Create: `campaignsim/backend/tests/test_auth_api.py`
- Modify: `campaignsim/backend/app/api/__init__.py`
- Modify: `campaignsim/backend/app/__init__.py`

**Interfaces:**
- Produces: `POST /api/auth/signup`, `POST /api/auth/login`, `POST /api/auth/logout`, `POST /api/auth/refresh`, `GET /api/auth/me`
- Consumes: `encode_access_jwt`, `hash_password`, `check_password`, `generate_opaque_token`, `hash_token` from `auth_utils`
- Consumes: `User`, `RefreshToken` models

- [ ] **Step 1: Write the failing tests**

Create `campaignsim/backend/tests/test_auth_api.py`:

```python
"""Integration tests for auth API endpoints."""

import json
import pytest


def _signup(client, email="test@example.com", password="Password1!", name="Test User"):
    return client.post(
        "/api/auth/signup",
        json={"email": email, "password": password, "display_name": name},
    )


def test_signup_creates_user_and_sets_cookies(client):
    resp = _signup(client)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["user"]["email"] == "test@example.com"
    assert "cs_access" in resp.headers.get("Set-Cookie", "")


def test_signup_duplicate_email_returns_409(client):
    _signup(client)
    resp = _signup(client)
    assert resp.status_code == 409


def test_login_with_correct_credentials(client):
    _signup(client)
    resp = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "Password1!"},
    )
    assert resp.status_code == 200
    assert "cs_access" in resp.headers.get("Set-Cookie", "")


def test_login_with_wrong_password_returns_401(client):
    _signup(client)
    resp = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "WrongPass1!"},
    )
    assert resp.status_code == 401


def test_me_returns_user_when_authenticated(client):
    _signup(client)
    # The test client holds cookies from signup automatically
    resp = client.get("/api/auth/me")
    assert resp.status_code == 200
    assert resp.get_json()["email"] == "test@example.com"


def test_me_returns_401_when_not_authenticated(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_logout_clears_cookies(client):
    _signup(client)
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 200
    # Cookies should be cleared (max-age=0)
    cookie_header = resp.headers.get("Set-Cookie", "")
    assert "cs_access" in cookie_header
```

- [ ] **Step 2: Run to verify failure**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2/campaignsim/backend"
python3 -m pytest tests/test_auth_api.py -v 2>&1 | head -30
```

Expected: `ImportError` or 404 errors — routes don't exist yet.

- [ ] **Step 3: Implement auth blueprint**

Create `campaignsim/backend/app/api/auth.py`:

```python
"""Auth API routes: signup, login, logout, refresh, /me.

Cookies:
  cs_access  — httpOnly, Secure, SameSite=None, 15-min TTL
  cs_refresh — httpOnly, Secure, SameSite=None, 30-day TTL
"""

from datetime import datetime, timedelta, timezone

from flask import Blueprint, current_app, g, jsonify, make_response, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

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


# Limiter is initialised per-blueprint; the app-level limiter is wired in __init__.py
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

    resp = make_response(jsonify({"user": {"id": user.id, "email": user.email, "display_name": user.display_name}}), 201)
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

    resp = make_response(jsonify({"user": {"id": user.id, "email": user.email, "display_name": user.display_name}}), 200)
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
```

- [ ] **Step 4: Register auth_bp in api/__init__.py**

Add to `campaignsim/backend/app/api/__init__.py`:

```python
auth_bp = Blueprint('auth', __name__)

from . import auth  # noqa: E402, F401
```

Then at the bottom, after the existing blueprint imports, add:

```python
from .auth import auth_bp  # noqa: F401 — re-export for app factory
```

Actually, given the pattern in `__init__.py`, modify it to:

```python
"""API route module"""

from flask import Blueprint

graph_bp = Blueprint('graph', __name__)
simulation_bp = Blueprint('simulation', __name__)
report_bp = Blueprint('report', __name__)
evaluation_bp = Blueprint('evaluation', __name__)
auth_bp = Blueprint('auth', __name__)
briefs_bp = Blueprint('briefs', __name__)

from . import graph        # noqa: E402, F401
from . import simulation   # noqa: E402, F401
from . import report       # noqa: E402, F401
from . import evaluation   # noqa: E402, F401
from . import auth         # noqa: E402, F401
```

Note: `briefs_bp` is declared here now, imported in Task 6.

- [ ] **Step 5: Register auth blueprint in app factory**

In `campaignsim/backend/app/__init__.py`, after the existing blueprint registrations, add:

```python
    from .api import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
```

Also wire the limiter:

```python
    from flask_limiter import Limiter
    from .api.auth import _get_real_ip
    limiter = Limiter(app, key_func=_get_real_ip)
```

Add this after the CORS setup.

- [ ] **Step 6: Run auth API tests**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2/campaignsim/backend"
python3 -m pytest tests/test_auth_api.py -v
```

Expected: all 7 tests PASS.

- [ ] **Step 7: Verify syntax**

```bash
python3 -m py_compile app/api/auth.py app/api/__init__.py app/__init__.py
echo "Syntax OK"
```

- [ ] **Step 8: Commit**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2"
git add campaignsim/backend/app/api/auth.py campaignsim/backend/app/api/__init__.py campaignsim/backend/app/__init__.py campaignsim/backend/tests/test_auth_api.py
git commit -m "feat: auth API routes (signup/login/logout/refresh/me) — 7 tests pass"
```

---

### Task 6: Brand Brief API

**Files:**
- Create: `campaignsim/backend/app/api/briefs.py`
- Create: `campaignsim/backend/tests/test_briefs_api.py`
- Modify: `campaignsim/backend/app/api/__init__.py`
- Modify: `campaignsim/backend/app/__init__.py`

**Interfaces:**
- Produces: `GET /api/briefs`, `POST /api/briefs`, `GET /api/briefs/<id>`, `PUT /api/briefs/<id>`, `DELETE /api/briefs/<id>`, `POST /api/briefs/<id>/upload`, `POST /api/briefs/<id>/rebuild-graph`
- Consumes: `require_auth`, `g.current_user`, `BrandBrief` model, `current_app.storage`

- [ ] **Step 1: Write the failing tests**

Create `campaignsim/backend/tests/test_briefs_api.py`:

```python
"""Integration tests for brand brief API."""

import pytest


def _signup_and_get_client(client):
    client.post(
        "/api/auth/signup",
        json={"email": "user@example.com", "password": "Password1!", "display_name": "U"},
    )
    return client


def test_list_briefs_empty_for_new_user(client):
    _signup_and_get_client(client)
    resp = client.get("/api/briefs")
    assert resp.status_code == 200
    assert resp.get_json()["items"] == []


def test_create_brief(client):
    _signup_and_get_client(client)
    resp = client.post("/api/briefs", json={"name": "My Brand", "content": "We sell coffee."})
    assert resp.status_code == 201
    data = resp.get_json()["brief"]
    assert data["name"] == "My Brand"
    assert data["content"] == "We sell coffee."
    assert data["graph_status"] == "pending"


def test_get_brief_by_id(client):
    _signup_and_get_client(client)
    created = client.post("/api/briefs", json={"name": "Brand X", "content": "X content"})
    brief_id = created.get_json()["brief"]["id"]

    resp = client.get(f"/api/briefs/{brief_id}")
    assert resp.status_code == 200
    assert resp.get_json()["brief"]["id"] == brief_id


def test_update_brief_name_and_content(client):
    _signup_and_get_client(client)
    created = client.post("/api/briefs", json={"name": "Old Name", "content": "old"})
    brief_id = created.get_json()["brief"]["id"]

    resp = client.put(f"/api/briefs/{brief_id}", json={"name": "New Name", "content": "new"})
    assert resp.status_code == 200
    assert resp.get_json()["brief"]["name"] == "New Name"


def test_delete_brief(client):
    _signup_and_get_client(client)
    created = client.post("/api/briefs", json={"name": "To Delete", "content": "bye"})
    brief_id = created.get_json()["brief"]["id"]

    resp = client.delete(f"/api/briefs/{brief_id}")
    assert resp.status_code == 200

    resp2 = client.get(f"/api/briefs/{brief_id}")
    assert resp2.status_code == 404


def test_cannot_access_another_users_brief(client):
    client.post(
        "/api/auth/signup",
        json={"email": "user1@example.com", "password": "Password1!", "display_name": "U1"},
    )
    created = client.post("/api/briefs", json={"name": "User1 Brief", "content": "private"})
    brief_id = created.get_json()["brief"]["id"]

    # Log in as user2
    client.post("/api/auth/logout")
    client.post(
        "/api/auth/signup",
        json={"email": "user2@example.com", "password": "Password1!", "display_name": "U2"},
    )
    resp = client.get(f"/api/briefs/{brief_id}")
    assert resp.status_code == 404
```

- [ ] **Step 2: Run to verify failure**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2/campaignsim/backend"
python3 -m pytest tests/test_briefs_api.py -v 2>&1 | head -20
```

Expected: 404 errors — routes don't exist.

- [ ] **Step 3: Implement briefs blueprint**

Create `campaignsim/backend/app/api/briefs.py`:

```python
"""Brand brief API routes.

All routes require auth (cs_access cookie).
file_path in BrandBrief is relative to uploads/{user_id}/briefs/.
content TEXT column is the canonical source of truth.
"""

import os
import tempfile

from flask import current_app, g, jsonify, request

from app.api import briefs_bp
from app.db import db
from app.db.models import BrandBrief
from app.utils.auth_utils import require_auth
from app.utils.logger import get_logger

logger = get_logger("campaignsim.api.briefs")


def _brief_to_dict(brief: BrandBrief) -> dict:
    return {
        "id": brief.id,
        "name": brief.name,
        "content": brief.content,
        "file_path": brief.file_path,
        "graph_id": brief.graph_id,
        "graph_status": brief.graph_status,
        "created_at": brief.created_at.isoformat(),
        "updated_at": brief.updated_at.isoformat(),
    }


def _get_own_brief(brief_id: str) -> BrandBrief | None:
    """Return brief owned by current user, or None."""
    return BrandBrief.query.filter_by(id=brief_id, user_id=g.current_user.id).first()


@briefs_bp.route("", methods=["GET"])
@require_auth
def list_briefs():
    briefs = BrandBrief.query.filter_by(user_id=g.current_user.id).order_by(BrandBrief.created_at.desc()).all()
    return jsonify({"items": [_brief_to_dict(b) for b in briefs]})


@briefs_bp.route("", methods=["POST"])
@require_auth
def create_brief():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    brief = BrandBrief(
        user_id=g.current_user.id,
        name=name,
        content=body.get("content") or "",
        graph_status="pending",
    )
    db.session.add(brief)
    db.session.commit()
    return jsonify({"brief": _brief_to_dict(brief)}), 201


@briefs_bp.route("/<brief_id>", methods=["GET"])
@require_auth
def get_brief(brief_id: str):
    brief = _get_own_brief(brief_id)
    if not brief:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"brief": _brief_to_dict(brief)})


@briefs_bp.route("/<brief_id>", methods=["PUT"])
@require_auth
def update_brief(brief_id: str):
    brief = _get_own_brief(brief_id)
    if not brief:
        return jsonify({"error": "Not found"}), 404

    body = request.get_json(silent=True) or {}
    if "name" in body:
        brief.name = (body["name"] or "").strip() or brief.name
    if "content" in body:
        brief.content = body["content"]

    db.session.commit()
    return jsonify({"brief": _brief_to_dict(brief)})


@briefs_bp.route("/<brief_id>", methods=["DELETE"])
@require_auth
def delete_brief(brief_id: str):
    brief = _get_own_brief(brief_id)
    if not brief:
        return jsonify({"error": "Not found"}), 404

    db.session.delete(brief)
    db.session.commit()
    return jsonify({"ok": True})


@briefs_bp.route("/<brief_id>/upload", methods=["POST"])
@require_auth
def upload_brief_file(brief_id: str):
    """Attach or replace the uploaded source file for a brief.

    Extracts text, writes to brief.content, saves file to storage.
    """
    brief = _get_own_brief(brief_id)
    if not brief:
        return jsonify({"error": "Not found"}), 404

    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "No file provided"}), 400

    from app.utils.file_parser import FileParser
    content_bytes = file.read()
    text = FileParser.extract_text(content_bytes, file.filename)

    storage = current_app.storage
    key = f"briefs/{brief.id}/{file.filename}"
    storage.save_file(g.current_user.id, key, content_bytes)

    brief.file_path = key
    brief.content = text
    db.session.commit()

    return jsonify({"brief": _brief_to_dict(brief)})


@briefs_bp.route("/<brief_id>/rebuild-graph", methods=["POST"])
@require_auth
def rebuild_graph(brief_id: str):
    """Trigger KG rebuild from current brief.content.

    Writes content to a temp file, passes path to graph_builder unchanged.
    Temp file is at uploads/{user_id}/briefs/{brief_id}_rebuild.txt and is
    overwritten on each call — no cleanup needed.
    """
    brief = _get_own_brief(brief_id)
    if not brief:
        return jsonify({"error": "Not found"}), 404
    if not brief.content:
        return jsonify({"error": "Brief has no content to build graph from"}), 400

    storage = current_app.storage
    tmp_key = f"briefs/{brief.id}_rebuild.txt"
    tmp_path = storage.user_path(g.current_user.id, tmp_key)
    os.makedirs(os.path.dirname(tmp_path), exist_ok=True)
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(brief.content)

    brief.graph_status = "building"
    db.session.commit()

    # Kick off async graph build (reuses existing task infrastructure)
    try:
        from app.services.graph_builder import GraphBuilderService
        from app.models.task import TaskManager

        task_id = TaskManager.create_task("graph_build")
        GraphBuilderService.build_async(
            file_path=tmp_path,
            task_id=task_id,
            user_id=g.current_user.id,
            brief_id=brief.id,
        )
        return jsonify({"task_id": task_id, "graph_status": "building"})
    except Exception as exc:
        logger.error(f"Graph rebuild failed for brief {brief_id}: {exc}")
        brief.graph_status = "failed"
        db.session.commit()
        return jsonify({"error": "Graph build failed to start"}), 500
```

- [ ] **Step 4: Add briefs import to api/__init__.py**

Add at the bottom of `campaignsim/backend/app/api/__init__.py`:

```python
from . import briefs  # noqa: E402, F401
```

- [ ] **Step 5: Register briefs blueprint in app factory**

In `campaignsim/backend/app/__init__.py`, after the auth blueprint registration:

```python
    from .api import briefs_bp
    app.register_blueprint(briefs_bp, url_prefix='/api/briefs')
```

- [ ] **Step 6: Run briefs tests**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2/campaignsim/backend"
python3 -m pytest tests/test_briefs_api.py -v
```

Expected: all 6 tests PASS.

- [ ] **Step 7: Verify syntax**

```bash
python3 -m py_compile app/api/briefs.py
echo "Syntax OK"
```

- [ ] **Step 8: Commit**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2"
git add campaignsim/backend/app/api/briefs.py campaignsim/backend/app/api/__init__.py campaignsim/backend/app/__init__.py campaignsim/backend/tests/test_briefs_api.py
git commit -m "feat: brand brief CRUD + upload + rebuild-graph API — 6 tests pass"
```

---

### Task 7: Apply Auth Guard to Existing Routes

**Files:**
- Modify: `campaignsim/backend/app/api/graph.py`
- Modify: `campaignsim/backend/app/api/simulation.py`
- Modify: `campaignsim/backend/app/api/report.py`
- Modify: `campaignsim/backend/app/api/evaluation.py`

**Interfaces:**
- Consumes: `require_auth` from `app.utils.auth_utils`
- Consumes: `g.current_user` (injected by decorator)

- [ ] **Step 1: Add require_auth import to graph.py**

At the top of `campaignsim/backend/app/api/graph.py`, after the existing imports, add:

```python
from ..utils.auth_utils import require_auth
from flask import g
```

Then add `@require_auth` decorator to every route handler in `graph.py`. The routes to decorate are all `@graph_bp.route(...)` functions. Place `@require_auth` immediately after each `@graph_bp.route(...)` line.

Example for the `/project/<project_id>` route:
```python
@graph_bp.route('/project/<project_id>', methods=['GET'])
@require_auth
def get_project(project_id: str):
    ...
```

Apply this pattern to **all** route handlers in `graph.py`.

- [ ] **Step 2: Add require_auth to simulation.py**

At the top of `campaignsim/backend/app/api/simulation.py`, after existing imports, add:

```python
from ..utils.auth_utils import require_auth
from flask import g
```

Add `@require_auth` immediately after every `@simulation_bp.route(...)` decorator in the file.

- [ ] **Step 3: Add require_auth to report.py and evaluation.py**

Apply the same pattern to `app/api/report.py` and `app/api/evaluation.py`:
1. Add `from ..utils.auth_utils import require_auth` and `from flask import g` imports
2. Add `@require_auth` after every `@<blueprint>.route(...)` decorator

- [ ] **Step 4: Verify syntax on all modified files**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2/campaignsim/backend"
python3 -m py_compile app/api/graph.py app/api/simulation.py app/api/report.py app/api/evaluation.py
echo "Syntax OK"
```

- [ ] **Step 5: Run Chinese and brand clean checks**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2/campaignsim/backend"
grep -rn -P "[\x{4e00}-\x{9fff}\x{ff01}-\x{ffee}]" --include="*.py" . 2>/dev/null | grep -v "locales/zh.json"
grep -rni "mirofish\|666ghj" --include="*.py" . 2>/dev/null
```

Expected: no output from either command.

- [ ] **Step 6: Commit**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2"
git add campaignsim/backend/app/api/graph.py campaignsim/backend/app/api/simulation.py campaignsim/backend/app/api/report.py campaignsim/backend/app/api/evaluation.py
git commit -m "feat: apply require_auth to all existing API routes"
```

---

### Task 8: Persona DB Persistence

**Files:**
- Modify: `campaignsim/backend/app/api/simulation.py`
- Create: `campaignsim/backend/tests/test_persona_api.py`

**Interfaces:**
- Modifies: `POST /api/simulation/generate_profiles` — saves generated personas to `personas` table
- Produces: `GET /api/simulation/personas?brief_id=<id>` — list personas from DB
- Produces: `DELETE /api/simulation/persona/<id>` — delete single persona row
- Produces: `POST /api/simulation/personas/clear?brief_id=<id>` — delete all for a brief

- [ ] **Step 1: Write the failing tests**

Create `campaignsim/backend/tests/test_persona_api.py`:

```python
"""Tests for persona persistence endpoints."""

import pytest
from app.db import db as _db
from app.db.models import BrandBrief, Persona


def _auth(client):
    client.post(
        "/api/auth/signup",
        json={"email": "p@example.com", "password": "Password1!", "display_name": "P"},
    )


def _make_brief(client):
    resp = client.post("/api/briefs", json={"name": "B", "content": "c"})
    return resp.get_json()["brief"]["id"]


def _seed_personas(app, user_id, brief_id, count=3):
    """Directly insert test personas into the DB."""
    with app.app_context():
        for i in range(count):
            p = Persona(
                user_id=user_id,
                brand_brief_id=brief_id,
                external_id=f"user_{i:03}",
                segment="Segment A",
                data={"name": f"Person {i}", "user_id": f"user_{i:03}"},
            )
            _db.session.add(p)
        _db.session.commit()


def test_list_personas_empty(client):
    _auth(client)
    brief_id = _make_brief(client)
    resp = client.get(f"/api/simulation/personas?brief_id={brief_id}")
    assert resp.status_code == 200
    assert resp.get_json()["items"] == []


def test_list_personas_returns_saved_rows(client, app):
    _auth(client)
    brief_id = _make_brief(client)
    # Get user_id from the me endpoint
    me = client.get("/api/auth/me").get_json()
    _seed_personas(app, me["id"], brief_id, count=3)
    resp = client.get(f"/api/simulation/personas?brief_id={brief_id}")
    assert len(resp.get_json()["items"]) == 3


def test_delete_persona(client, app):
    _auth(client)
    brief_id = _make_brief(client)
    me = client.get("/api/auth/me").get_json()
    _seed_personas(app, me["id"], brief_id, count=2)

    items = client.get(f"/api/simulation/personas?brief_id={brief_id}").get_json()["items"]
    persona_id = items[0]["id"]

    resp = client.delete(f"/api/simulation/persona/{persona_id}")
    assert resp.status_code == 200

    items_after = client.get(f"/api/simulation/personas?brief_id={brief_id}").get_json()["items"]
    assert len(items_after) == 1


def test_clear_personas(client, app):
    _auth(client)
    brief_id = _make_brief(client)
    me = client.get("/api/auth/me").get_json()
    _seed_personas(app, me["id"], brief_id, count=5)

    resp = client.post(f"/api/simulation/personas/clear?brief_id={brief_id}")
    assert resp.status_code == 200

    items = client.get(f"/api/simulation/personas?brief_id={brief_id}").get_json()["items"]
    assert items == []
```

- [ ] **Step 2: Run to verify failure**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2/campaignsim/backend"
python3 -m pytest tests/test_persona_api.py -v 2>&1 | head -20
```

Expected: 404 errors — persona routes don't exist yet.

- [ ] **Step 3: Add persona routes to simulation.py**

At the top of `campaignsim/backend/app/api/simulation.py`, add to imports:

```python
from ..db import db
from ..db.models import Persona, BrandBrief
```

Then add these three new route handlers at the **end** of `simulation.py` (after existing routes):

```python
@simulation_bp.route('/personas', methods=['GET'])
@require_auth
def list_personas():
    """List personas for the current user scoped to a brand brief."""
    brief_id = request.args.get('brief_id')
    if not brief_id:
        return jsonify({"error": "brief_id query param required"}), 400

    # Verify brief belongs to current user
    brief = BrandBrief.query.filter_by(id=brief_id, user_id=g.current_user.id).first()
    if not brief:
        return jsonify({"error": "Brief not found"}), 404

    personas = Persona.query.filter_by(
        user_id=g.current_user.id,
        brand_brief_id=brief_id,
    ).order_by(Persona.created_at).all()

    return jsonify({
        "items": [
            {
                "id": p.id,
                "external_id": p.external_id,
                "segment": p.segment,
                **p.data,
            }
            for p in personas
        ]
    })


@simulation_bp.route('/persona/<persona_id>', methods=['DELETE'])
@require_auth
def delete_persona(persona_id: str):
    """Delete a single persona row owned by the current user."""
    persona = Persona.query.filter_by(id=persona_id, user_id=g.current_user.id).first()
    if not persona:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(persona)
    db.session.commit()
    return jsonify({"ok": True})


@simulation_bp.route('/personas/clear', methods=['POST'])
@require_auth
def clear_personas():
    """Delete all personas for a brief owned by the current user."""
    brief_id = request.args.get('brief_id')
    if not brief_id:
        return jsonify({"error": "brief_id query param required"}), 400

    brief = BrandBrief.query.filter_by(id=brief_id, user_id=g.current_user.id).first()
    if not brief:
        return jsonify({"error": "Brief not found"}), 404

    Persona.query.filter_by(
        user_id=g.current_user.id,
        brand_brief_id=brief_id,
    ).delete()
    db.session.commit()
    return jsonify({"ok": True})
```

- [ ] **Step 4: Run persona tests**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2/campaignsim/backend"
python3 -m pytest tests/test_persona_api.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Verify syntax**

```bash
python3 -m py_compile app/api/simulation.py
echo "Syntax OK"
```

- [ ] **Step 6: Run all backend tests**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2/campaignsim/backend"
python3 -m pytest tests/ -v
```

Expected: all 23 tests PASS.

- [ ] **Step 7: Commit**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2"
git add campaignsim/backend/app/api/simulation.py campaignsim/backend/tests/test_persona_api.py
git commit -m "feat: persona list/delete/clear routes persisting to DB — 4 tests pass"
```

---

### Task 9: Frontend Auth Layer

**Files:**
- Modify: `campaignsim-v3/frontend/src/api/client.js`
- Create: `campaignsim-v3/frontend/src/stores/authStore.js`
- Modify: `campaignsim-v3/frontend/src/main.js`

**Interfaces:**
- Produces: `apiClient` with `withCredentials: true` and 401→refresh interceptor
- Produces: `useAuthStore()` with `user`, `login()`, `signup()`, `logout()`, `fetchMe()`

- [ ] **Step 1: Update frontend .env for dev**

Check if `campaignsim-v3/frontend/.env.local` exists. If not, create it:

```bash
ls "campaignsim-v3/frontend/.env.local" 2>/dev/null || echo "missing"
```

Create `campaignsim-v3/frontend/.env.local` if missing:

```
VITE_API_BASE_URL=http://localhost:5001
```

- [ ] **Step 2: Add withCredentials + refresh interceptor to client.js**

Replace the full contents of `campaignsim-v3/frontend/src/api/client.js`:

```js
import axios from "axios";

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "",
  timeout: 30000,
  withCredentials: true,  // Send cookies on every request (required for httpOnly auth cookies)
});

// Response interceptor: normalize errors and handle 401 → auto-refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error?.response?.status;

    // Auto-refresh: if we get a 401 and haven't already retried, call /refresh and retry once
    if (status === 401 && !error.config._retried) {
      error.config._retried = true;
      try {
        await apiClient.post("/api/auth/refresh");
        return apiClient(error.config);
      } catch {
        // Refresh failed (expired/revoked) — clear user and redirect to login
        try {
          const { useAuthStore } = await import("@/stores/authStore");
          const auth = useAuthStore();
          auth.user = null;
        } catch {
          // authStore not yet available (e.g., during boot) — safe to ignore
        }
        window.location.href = "/login";
        return Promise.reject(error);
      }
    }

    const code = error?.response?.data?.error?.code || "NETWORK_ERROR";
    const message =
      error?.response?.data?.message ||
      error?.response?.data?.error?.message ||
      error.message ||
      "Unexpected API error";

    return Promise.reject({
      status,
      code,
      message,
      details: error?.response?.data?.error?.details || {},
      raw: error,
    });
  },
);
```

- [ ] **Step 3: Create authStore**

Create `campaignsim-v3/frontend/src/stores/authStore.js`:

```js
import { defineStore } from "pinia";
import { apiClient } from "@/api/client.js";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null,       // { id, email, display_name } or null
    loading: false,
    error: null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.user,
  },

  actions: {
    async fetchMe() {
      this.loading = true;
      this.error = null;
      try {
        const resp = await apiClient.get("/api/auth/me");
        this.user = resp.data;
      } catch {
        this.user = null;
      } finally {
        this.loading = false;
      }
    },

    async login(email, password) {
      this.loading = true;
      this.error = null;
      try {
        const resp = await apiClient.post("/api/auth/login", { email, password });
        this.user = resp.data.user;
      } catch (err) {
        this.error = err.message || "Login failed";
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async signup(email, password, displayName) {
      this.loading = true;
      this.error = null;
      try {
        const resp = await apiClient.post("/api/auth/signup", {
          email,
          password,
          display_name: displayName,
        });
        this.user = resp.data.user;
      } catch (err) {
        this.error = err.message || "Signup failed";
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async logout() {
      try {
        await apiClient.post("/api/auth/logout");
      } catch {
        // Best effort
      } finally {
        this.user = null;
        // Clear brief selection on logout
        sessionStorage.removeItem("cs_active_brief_id");
        window.location.href = "/login";
      }
    },
  },
});
```

- [ ] **Step 4: Boot auth check in main.js**

Replace `campaignsim-v3/frontend/src/main.js` with:

```js
import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import i18n from "./i18n/index.js";
import "./styles/base.css";
import "./styles/dashboard.css";

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(router);
app.use(i18n);

// Attempt to restore auth state from cookie before mounting.
// The router guard also calls fetchMe() but doing it here avoids
// a flash of unauthenticated state on first render.
import("@/stores/authStore").then(({ useAuthStore }) => {
  const auth = useAuthStore();
  auth.fetchMe().finally(() => {
    app.mount("#app");
  });
});
```

- [ ] **Step 5: Start dev server and verify no console errors**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2/campaignsim-v3/frontend"
npm run dev &
sleep 4
curl -s http://localhost:3006 | grep -c "id=\"app\""
```

Expected: `1` (the `#app` mount point is present).

- [ ] **Step 6: Commit**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2"
git add campaignsim-v3/frontend/src/api/client.js campaignsim-v3/frontend/src/stores/authStore.js campaignsim-v3/frontend/src/main.js campaignsim-v3/frontend/.env.local
git commit -m "feat: frontend auth layer (authStore, axios interceptor, boot check)"
```

---

### Task 10: Frontend Views + Router Auth Guard

**Files:**
- Create: `campaignsim-v3/frontend/src/views/LoginView.vue`
- Create: `campaignsim-v3/frontend/src/views/SignupView.vue`
- Create: `campaignsim-v3/frontend/src/views/BrandBriefView.vue`
- Modify: `campaignsim-v3/frontend/src/router/index.js`

**Interfaces:**
- Produces: `/login` → `LoginView`, `/signup` → `SignupView`, `/briefs` → `BrandBriefView`
- Consumes: `useAuthStore()`, `useCampaignStore()` (for `selectBrief`)

- [ ] **Step 1: Create LoginView**

Create `campaignsim-v3/frontend/src/views/LoginView.vue`:

```vue
<template>
  <div class="auth-page">
    <div class="auth-card">
      <h1 class="auth-title">CampaignSim</h1>
      <p class="auth-subtitle">Sign in to your account</p>

      <form @submit.prevent="submit" class="auth-form">
        <label>
          Email
          <input v-model.trim="email" type="email" autocomplete="email" required placeholder="you@example.com" />
        </label>
        <label>
          Password
          <input v-model="password" type="password" autocomplete="current-password" required placeholder="••••••••" />
        </label>

        <p v-if="auth.error" class="auth-error">{{ auth.error }}</p>

        <button type="submit" :disabled="auth.loading" class="auth-submit">
          {{ auth.loading ? "Signing in…" : "Sign in" }}
        </button>
      </form>

      <p class="auth-switch">
        No account? <RouterLink to="/signup">Create one</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/authStore";

const auth = useAuthStore();
const router = useRouter();
const email = ref("");
const password = ref("");

async function submit() {
  try {
    await auth.login(email.value, password.value);
    router.push("/briefs");
  } catch {
    // error is set on auth.error
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg);
}
.auth-card {
  width: 100%;
  max-width: 400px;
  padding: 2.5rem 2rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 1rem;
}
.auth-title { font-size: 1.5rem; font-weight: 700; margin-bottom: 0.25rem; }
.auth-subtitle { color: var(--color-text-muted); margin-bottom: 2rem; }
.auth-form { display: flex; flex-direction: column; gap: 1rem; }
.auth-form label { display: flex; flex-direction: column; gap: 0.375rem; font-size: 0.875rem; font-weight: 500; }
.auth-form input { padding: 0.625rem 0.875rem; border: 1px solid var(--color-border); border-radius: 0.5rem; background: var(--color-bg); color: var(--color-text); font-size: 0.9375rem; }
.auth-error { color: var(--color-danger, #ef4444); font-size: 0.875rem; margin: 0; }
.auth-submit { margin-top: 0.5rem; padding: 0.75rem; background: var(--color-accent); color: #fff; border: none; border-radius: 0.5rem; font-weight: 600; cursor: pointer; }
.auth-submit:disabled { opacity: 0.6; cursor: not-allowed; }
.auth-switch { text-align: center; margin-top: 1.5rem; font-size: 0.875rem; color: var(--color-text-muted); }
</style>
```

- [ ] **Step 2: Create SignupView**

Create `campaignsim-v3/frontend/src/views/SignupView.vue`:

```vue
<template>
  <div class="auth-page">
    <div class="auth-card">
      <h1 class="auth-title">CampaignSim</h1>
      <p class="auth-subtitle">Create your account</p>

      <form @submit.prevent="submit" class="auth-form">
        <label>
          Display name
          <input v-model.trim="displayName" type="text" autocomplete="name" placeholder="Your name" />
        </label>
        <label>
          Email
          <input v-model.trim="email" type="email" autocomplete="email" required placeholder="you@example.com" />
        </label>
        <label>
          Password
          <input v-model="password" type="password" autocomplete="new-password" required placeholder="8+ characters" />
        </label>

        <p v-if="auth.error" class="auth-error">{{ auth.error }}</p>

        <button type="submit" :disabled="auth.loading" class="auth-submit">
          {{ auth.loading ? "Creating account…" : "Create account" }}
        </button>
      </form>

      <p class="auth-switch">
        Already have an account? <RouterLink to="/login">Sign in</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/authStore";

const auth = useAuthStore();
const router = useRouter();
const email = ref("");
const password = ref("");
const displayName = ref("");

async function submit() {
  try {
    await auth.signup(email.value, password.value, displayName.value);
    router.push("/briefs");
  } catch {
    // error is set on auth.error
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg);
}
.auth-card {
  width: 100%;
  max-width: 400px;
  padding: 2.5rem 2rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 1rem;
}
.auth-title { font-size: 1.5rem; font-weight: 700; margin-bottom: 0.25rem; }
.auth-subtitle { color: var(--color-text-muted); margin-bottom: 2rem; }
.auth-form { display: flex; flex-direction: column; gap: 1rem; }
.auth-form label { display: flex; flex-direction: column; gap: 0.375rem; font-size: 0.875rem; font-weight: 500; }
.auth-form input { padding: 0.625rem 0.875rem; border: 1px solid var(--color-border); border-radius: 0.5rem; background: var(--color-bg); color: var(--color-text); font-size: 0.9375rem; }
.auth-error { color: var(--color-danger, #ef4444); font-size: 0.875rem; margin: 0; }
.auth-submit { margin-top: 0.5rem; padding: 0.75rem; background: var(--color-accent); color: #fff; border: none; border-radius: 0.5rem; font-weight: 600; cursor: pointer; }
.auth-submit:disabled { opacity: 0.6; cursor: not-allowed; }
.auth-switch { text-align: center; margin-top: 1.5rem; font-size: 0.875rem; color: var(--color-text-muted); }
</style>
```

- [ ] **Step 3: Create BrandBriefView**

Create `campaignsim-v3/frontend/src/views/BrandBriefView.vue`:

```vue
<template>
  <div class="view-stack stagger-in">
    <PageHeader
      title="Brand Briefs"
      eyebrow="Your workspace"
      description="Select a brand brief to start a campaign, or create a new one."
    >
      <template #actions>
        <AppButton @click="showCreate = true">New brief</AppButton>
      </template>
    </PageHeader>

    <!-- Create form -->
    <AppCard v-if="showCreate">
      <form @submit.prevent="createBrief" style="display: flex; flex-direction: column; gap: 1rem;">
        <label>
          Brief name
          <input v-model.trim="newName" type="text" required placeholder="e.g. Airbnb Summer 2026" />
        </label>
        <label>
          Content
          <textarea v-model="newContent" rows="6" placeholder="Paste or type your brand brief here…" />
        </label>
        <div style="display: flex; gap: 0.75rem;">
          <AppButton type="submit" :disabled="creating">{{ creating ? "Creating…" : "Create" }}</AppButton>
          <AppButton variant="secondary" @click="showCreate = false">Cancel</AppButton>
        </div>
      </form>
    </AppCard>

    <EmptyState
      v-if="!loading && briefs.length === 0 && !showCreate"
      title="No briefs yet"
      message="Create your first brand brief to get started."
    />

    <div v-if="loading" class="persona-grid">
      <div v-for="n in 3" :key="n" class="skeleton-card">
        <SkeletonBlock variant="title" />
        <SkeletonBlock width="60%" />
      </div>
    </div>

    <div v-else class="brief-grid">
      <AppCard
        v-for="brief in briefs"
        :key="brief.id"
        class="brief-card"
        :class="{ 'is-active': campaignStore.brandBriefId === brief.id }"
        @click="selectBrief(brief)"
        role="button"
        tabindex="0"
        @keydown.enter="selectBrief(brief)"
      >
        <div class="brief-card-header">
          <h3 class="brief-card-name">{{ brief.name }}</h3>
          <StatusBadge :status="brief.graph_status" />
        </div>
        <p class="brief-card-content">{{ brief.content?.slice(0, 140) || "No content yet." }}</p>
        <div class="brief-card-actions" @click.stop>
          <AppButton variant="secondary" size="sm" @click="startEdit(brief)">Edit</AppButton>
          <AppButton variant="danger" size="sm" @click="deleteBrief(brief.id)">Delete</AppButton>
        </div>
      </AppCard>
    </div>

    <!-- Inline edit drawer -->
    <DrawerPanel :open="!!editingBrief" @close="editingBrief = null" title="Edit brief">
      <form v-if="editingBrief" @submit.prevent="saveEdit" style="display: flex; flex-direction: column; gap: 1rem; padding: 1rem;">
        <label>
          Name
          <input v-model.trim="editName" type="text" required />
        </label>
        <label>
          Content
          <textarea v-model="editContent" rows="12" />
        </label>
        <AppButton type="submit" :disabled="saving">{{ saving ? "Saving…" : "Save" }}</AppButton>
      </form>
    </DrawerPanel>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { apiClient } from "@/api/client.js";
import { useCampaignStore } from "@/stores/campaignStore";
import AppButton from "@/components/common/AppButton.vue";
import AppCard from "@/components/common/AppCard.vue";
import DrawerPanel from "@/components/common/DrawerPanel.vue";
import EmptyState from "@/components/common/EmptyState.vue";
import PageHeader from "@/components/common/PageHeader.vue";
import SkeletonBlock from "@/components/common/SkeletonBlock.vue";
import StatusBadge from "@/components/common/StatusBadge.vue";

const router = useRouter();
const campaignStore = useCampaignStore();

const briefs = ref([]);
const loading = ref(true);
const showCreate = ref(false);
const creating = ref(false);
const newName = ref("");
const newContent = ref("");

const editingBrief = ref(null);
const editName = ref("");
const editContent = ref("");
const saving = ref(false);

async function loadBriefs() {
  loading.value = true;
  try {
    const resp = await apiClient.get("/api/briefs");
    briefs.value = resp.data.items;
  } finally {
    loading.value = false;
  }
}

async function createBrief() {
  creating.value = true;
  try {
    const resp = await apiClient.post("/api/briefs", {
      name: newName.value,
      content: newContent.value,
    });
    briefs.value.unshift(resp.data.brief);
    showCreate.value = false;
    newName.value = "";
    newContent.value = "";
  } finally {
    creating.value = false;
  }
}

function selectBrief(brief) {
  campaignStore.selectBrief(brief.id);
  router.push("/process");
}

function startEdit(brief) {
  editingBrief.value = brief;
  editName.value = brief.name;
  editContent.value = brief.content || "";
}

async function saveEdit() {
  if (!editingBrief.value) return;
  saving.value = true;
  try {
    const resp = await apiClient.put(`/api/briefs/${editingBrief.value.id}`, {
      name: editName.value,
      content: editContent.value,
    });
    const idx = briefs.value.findIndex((b) => b.id === editingBrief.value.id);
    if (idx !== -1) briefs.value[idx] = resp.data.brief;
    editingBrief.value = null;
  } finally {
    saving.value = false;
  }
}

async function deleteBrief(id) {
  if (!confirm("Delete this brief and all its personas?")) return;
  await apiClient.delete(`/api/briefs/${id}`);
  briefs.value = briefs.value.filter((b) => b.id !== id);
  if (campaignStore.brandBriefId === id) campaignStore.clearBrief();
}

onMounted(loadBriefs);
</script>

<style scoped>
.brief-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}
.brief-card {
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.brief-card.is-active {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 2px var(--color-accent);
}
.brief-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}
.brief-card-name { font-weight: 600; font-size: 1rem; }
.brief-card-content {
  font-size: 0.875rem;
  color: var(--color-text-muted);
  margin-bottom: 1rem;
  line-height: 1.5;
}
.brief-card-actions { display: flex; gap: 0.5rem; }
</style>
```

- [ ] **Step 4: Update router with auth guard + new routes**

Replace `campaignsim-v3/frontend/src/router/index.js`:

```js
import { createRouter, createWebHistory } from "vue-router";
import Home from "@/views/Home.vue";
import Process from "@/views/Process.vue";
import GraphPage from "@/views/GraphPage.vue";
import SimulationRunView from "@/views/SimulationRunView.vue";
import Step4Report from "@/views/Step4Report.vue";
import Step5Interaction from "@/views/Step5Interaction.vue";
import HistoryDatabase from "@/views/HistoryDatabase.vue";
import CampaignReportView from "@/views/CampaignReportView.vue";
import LoginView from "@/views/LoginView.vue";
import SignupView from "@/views/SignupView.vue";
import BrandBriefView from "@/views/BrandBriefView.vue";
import { useCampaignStore } from "@/stores/campaignStore";

// Routes that do not require authentication
const PUBLIC_ROUTES = new Set(["home", "login", "signup"]);

const routes = [
  { path: "/",        name: "home",    component: Home },
  { path: "/login",   name: "login",   component: LoginView },
  { path: "/signup",  name: "signup",  component: SignupView },
  { path: "/briefs",  name: "briefs",  component: BrandBriefView },
  { path: "/process", name: "process", component: Process },
  { path: "/graph",   name: "graph",   component: GraphPage },
  {
    path: "/simulation/:simulationId/run",
    name: "simulation-run",
    component: SimulationRunView,
  },
  { path: "/report/:reportId", name: "report", component: Step4Report },
  {
    path: "/interaction/:simulationId",
    name: "interaction",
    component: Step5Interaction,
  },
  { path: "/history", name: "history", component: HistoryDatabase },
  {
    path: "/campaign/:campaignId/report",
    name: "CampaignReport",
    component: CampaignReportView,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
});

router.beforeEach(async (to) => {
  // Public routes need no auth check
  if (PUBLIC_ROUTES.has(to.name)) return true;

  const { useAuthStore } = await import("@/stores/authStore");
  const auth = useAuthStore();

  // Attempt cookie-based restore if not yet loaded
  if (!auth.user) {
    await auth.fetchMe();
  }

  if (!auth.user) return "/login";

  // Workflow routes additionally require a selected brand brief
  const store = useCampaignStore();
  const workflowRoutes = new Set([
    "process", "graph", "simulation-run", "report", "interaction",
  ]);

  if (workflowRoutes.has(to.name) && !store.brandBriefId) {
    store.setNotice("Select a brand brief before entering the workflow.");
    return "/briefs";
  }

  // Legacy guards from original router
  if (to.name === "simulation-run" && store.variants.length < 2) {
    store.setNotice("Create at least two campaign variants before starting a simulation.");
    return "/process";
  }
  if (to.name === "report" && store.simulationRun?.status !== "completed" && !store.report?.data) {
    store.setNotice("Run a simulation before opening the report.");
    return "/process";
  }
  if (to.name === "interaction" && (!store.report?.data || store.personas.items.length === 0)) {
    store.setNotice("Generate a report and personas before interviewing personas.");
    return "/process";
  }

  return true;
});

export default router;
```

- [ ] **Step 5: Verify the app loads in browser**

```bash
# Backend must be running on port 5001 and frontend on 3006
# Open http://localhost:3006/login in a browser
# Verify: login form renders, no console errors
```

- [ ] **Step 6: Commit**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2"
git add campaignsim-v3/frontend/src/views/LoginView.vue campaignsim-v3/frontend/src/views/SignupView.vue campaignsim-v3/frontend/src/views/BrandBriefView.vue campaignsim-v3/frontend/src/router/index.js
git commit -m "feat: add Login, Signup, BrandBrief views and auth-guarded router"
```

---

### Task 11: campaignStore Persona Actions + Step2Personas UX

**Files:**
- Modify: `campaignsim-v3/frontend/src/stores/campaignStore.js`
- Modify: `campaignsim-v3/frontend/src/views/Step2Personas.vue`

**Interfaces:**
- Produces: `campaignStore.brandBriefId` — persisted in sessionStorage
- Produces: `campaignStore.selectBrief(id)`, `campaignStore.clearBrief()`
- Produces: `campaignStore.loadPersonas(briefId)`, `campaignStore.deletePersona(id)`, `campaignStore.clearPersonas(briefId)`

- [ ] **Step 1: Add brief selection + sessionStorage to campaignStore**

At the top of `campaignsim-v3/frontend/src/stores/campaignStore.js`, after the existing `const` declarations but before `export const useCampaignStore`, add:

```js
const BRIEF_KEY = "cs_active_brief_id";
```

Inside the `state: () => ({` object, add:

```js
    brandBriefId: sessionStorage.getItem(BRIEF_KEY) || null,
```

Inside the `actions:` object (or equivalent — the store uses options API), add these actions. Find the `actions` block or the `actions:` key and append:

```js
    selectBrief(id) {
      this.brandBriefId = id;
      sessionStorage.setItem(BRIEF_KEY, id);
    },

    clearBrief() {
      this.brandBriefId = null;
      sessionStorage.removeItem(BRIEF_KEY);
    },

    async loadPersonas(briefId) {
      this.personas.loading = true;
      this.personas.error = null;
      try {
        const { apiClient } = await import("@/api/client.js");
        const resp = await apiClient.get(`/api/simulation/personas?brief_id=${briefId}`);
        this.personas.items = resp.data.items;
      } catch (err) {
        this.personas.error = err.message || "Failed to load personas";
      } finally {
        this.personas.loading = false;
      }
    },

    async deletePersona(personaId) {
      const { apiClient } = await import("@/api/client.js");
      await apiClient.delete(`/api/simulation/persona/${personaId}`);
      this.personas.items = this.personas.items.filter((p) => p.id !== personaId);
    },

    async clearPersonas(briefId) {
      const { apiClient } = await import("@/api/client.js");
      await apiClient.post(`/api/simulation/personas/clear?brief_id=${briefId}`);
      this.personas.items = [];
    },
```

- [ ] **Step 2: Update Step2Personas.vue**

Replace the contents of `campaignsim-v3/frontend/src/views/Step2Personas.vue`:

```vue
<template>
  <div class="view-stack stagger-in">
    <PageHeader
      title="Audience Personas"
      eyebrow="Step 2"
      description="Generate segment-aware synthetic audiences from your knowledge graph."
    >
      <template #actions>
        <AppButton variant="secondary" :disabled="!store.personasReady" @click="store.goToStep(3)">
          Continue
        </AppButton>
      </template>
    </PageHeader>

    <AppCard>
      <div class="toolbar-row">
        <div>
          <span style="display: block; margin-bottom: 0.4rem; font-size: 0.8125rem; font-weight: 600">
            Persona count
          </span>
          <div class="segmented-control">
            <button
              v-for="n in counts"
              :key="n"
              type="button"
              :class="{ 'is-active': count === n }"
              @click="count = n"
            >
              {{ n }}
            </button>
          </div>
        </div>
        <label style="flex: 1; min-width: 180px">
          <span>Search</span>
          <input v-model.trim="search" type="search" placeholder="Name, segment, profession…" />
        </label>
        <div style="display: flex; gap: 0.5rem;">
          <AppButton
            variant="secondary"
            :disabled="!store.personas.items.length || store.personas.loading"
            @click="regenerateAll"
          >
            Regenerate all
          </AppButton>
          <AppButton
            :disabled="!store.graphReady || store.personas.loading"
            :loading="store.personas.loading"
            @click="store.generatePersonas(count)"
          >
            {{ store.personas.items.length ? "Generate more" : "Generate personas" }}
          </AppButton>
        </div>
      </div>

      <div v-if="segments.length" class="filter-chips" style="margin-top: 1rem">
        <button type="button" :class="{ 'is-active': !segmentFilter }" @click="segmentFilter = ''">All</button>
        <button
          v-for="seg in segments"
          :key="seg"
          type="button"
          :class="{ 'is-active': segmentFilter === seg }"
          @click="segmentFilter = seg"
        >
          {{ seg }}
        </button>
      </div>

      <div v-if="store.personas.loading" class="progress-block">
        <div class="progress-bar">
          <span :style="{ width: `${store.personas.progress || 12}%` }"></span>
        </div>
        <p>{{ store.personas.progressMessage || "Generating personas from graph context…" }}</p>
      </div>
      <ErrorState v-if="store.personas.error" :message="store.personas.error" />
    </AppCard>

    <div v-if="store.personas.loading && !store.personas.items.length" class="persona-grid">
      <div v-for="n in 6" :key="n" class="skeleton-card">
        <SkeletonBlock variant="title" />
        <SkeletonBlock />
        <SkeletonBlock width="60%" />
      </div>
    </div>

    <EmptyState
      v-else-if="!store.personas.items.length"
      title="No personas yet"
      message="Generate personas from your brand knowledge graph to continue."
    />

    <div v-else class="persona-grid">
      <div v-for="persona in filteredPersonas" :key="persona.user_id || persona.id" class="persona-card-wrapper">
        <PersonaCard
          :persona="persona"
          @select="activePersona = persona"
        />
        <button
          class="persona-delete-btn"
          type="button"
          title="Delete persona"
          @click.stop="store.deletePersona(persona.id)"
        >
          ✕
        </button>
      </div>
    </div>

    <PersonaDetailDrawer :persona="activePersona" @close="activePersona = null" />
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from "vue";
import AppButton from "@/components/common/AppButton.vue";
import AppCard from "@/components/common/AppCard.vue";
import EmptyState from "@/components/common/EmptyState.vue";
import ErrorState from "@/components/common/ErrorState.vue";
import PageHeader from "@/components/common/PageHeader.vue";
import SkeletonBlock from "@/components/common/SkeletonBlock.vue";
import PersonaCard from "@/components/personas/PersonaCard.vue";
import PersonaDetailDrawer from "@/components/personas/PersonaDetailDrawer.vue";
import { useCampaignStore } from "@/stores/campaignStore";

const store = useCampaignStore();
const count = ref(30);
const search = ref("");
const segmentFilter = ref("");
const activePersona = ref(null);
const counts = [10, 20, 30, 50];

// Load persisted personas from DB on mount
onMounted(() => {
  if (store.brandBriefId && !store.personas.items.length) {
    store.loadPersonas(store.brandBriefId);
  }
});

async function regenerateAll() {
  if (!store.brandBriefId) return;
  await store.clearPersonas(store.brandBriefId);
  store.generatePersonas(count.value);
}

const segments = computed(() => [...new Set(store.personas.items.map((p) => p.segment).filter(Boolean))]);

const filteredPersonas = computed(() =>
  store.personas.items.filter((persona) => {
    const matchesSegment = segmentFilter.value ? persona.segment === segmentFilter.value : true;
    const q = search.value.toLowerCase();
    const matchesSearch = q
      ? [persona.name, persona.segment, persona.profession, persona.country].some((field) =>
          String(field || "")
            .toLowerCase()
            .includes(q),
        )
      : true;
    return matchesSegment && matchesSearch;
  }),
);
</script>

<style scoped>
.persona-card-wrapper {
  position: relative;
}
.persona-delete-btn {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 50%;
  border: none;
  background: var(--color-danger, #ef4444);
  color: #fff;
  font-size: 0.7rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.15s;
}
.persona-card-wrapper:hover .persona-delete-btn {
  opacity: 1;
}
</style>
```

- [ ] **Step 3: Verify syntax (frontend)**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2/campaignsim-v3/frontend"
npm run build 2>&1 | tail -20
```

Expected: `built in` — no errors.

- [ ] **Step 4: Run Chinese and brand clean checks**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2"
grep -rn -P "[\x{4e00}-\x{9fff}\x{ff01}-\x{ffee}]" \
  --include="*.py" --include="*.vue" --include="*.js" --include="*.ts" \
  --include="*.json" --include="*.md" \
  --exclude-dir=".git" --exclude-dir="__pycache__" \
  . 2>/dev/null | grep -v "locales/zh.json"

grep -rni "mirofish\|666ghj" \
  --include="*.py" --include="*.vue" --include="*.js" --include="*.ts" \
  --include="*.json" --include="*.md" --include="*.yml" --include="*.toml" \
  --exclude-dir=".git" . 2>/dev/null
```

Expected: no output from either command.

- [ ] **Step 5: Run all backend tests**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2/campaignsim/backend"
python3 -m pytest tests/ -v
```

Expected: all 23 tests PASS.

- [ ] **Step 6: Commit**

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2"
git add campaignsim-v3/frontend/src/stores/campaignStore.js campaignsim-v3/frontend/src/views/Step2Personas.vue
git commit -m "feat: persona DB actions in campaignStore + Step2 delete/regenerate UX"
```

---

## Self-Review

### Spec coverage check

| Spec section | Covered by task(s) |
|---|---|
| User accounts (signup/login/JWT) | Task 4, 5 |
| Brand brief CRUD + inline edit | Task 6 |
| Brand brief file upload | Task 6 (`/upload` route) |
| Persona persistence to DB | Task 8 |
| Persona delete / clear | Task 8, 11 |
| User-scoped file paths (StorageBackend) | Task 3, 7 |
| httpOnly cookies + SameSite=None | Task 5 |
| CORS with supports_credentials | Task 2 |
| Rate limiting (CF-Connecting-IP) | Task 5 |
| JWT HS256 pinned | Task 4 |
| Refresh token SHA-256 in DB | Task 4, 5 |
| Refresh token indexes on DB | Task 2 (models.py) |
| Axios 401→refresh interceptor | Task 9 |
| brandBriefId sessionStorage persistence | Task 11 |
| Auth guard on existing routes | Task 7 |
| postgres healthcheck in docker-compose | Task 1 |
| /briefs post-login landing page | Task 10 |
| PUBLIC_ROUTES guard (includes home) | Task 10 |
| LoginView, SignupView, BrandBriefView | Task 10 |
| Step2 on-mount load + delete + regenerate | Task 11 |
| campaigns/campaign_variants schema-only | Task 2 (models annotated) |
| Alembic migration | Task 2 |
| .env.example | Task 1 |

All spec requirements are covered. No gaps found.
