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
    """Schema-only -- no rows written in this phase."""
    __tablename__ = "campaigns"

    id             = Column(String(36), primary_key=True, default=_uuid)
    user_id        = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    brand_brief_id = Column(String(36), ForeignKey("brand_briefs.id"))
    brand_name     = Column(String(255))
    campaign_goal  = Column(Text)
    created_at     = Column(DateTime(timezone=True), default=_now, nullable=False)

    variants = db.relationship("CampaignVariant", back_populates="campaign", cascade="all, delete-orphan")


class CampaignVariant(db.Model):
    """Schema-only -- no rows written in this phase."""
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
