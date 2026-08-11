"""SQLAlchemy ORM models for the platform database (Postgres).

File-based artifacts (KG SQLite files, simulation run directories, action
logs) stay on disk; these tables hold identity, ownership, and metadata
pointers into that file layout.

Spec: docs/superpowers/specs/2026-06-19-user-auth-brand-brief-personas-design.md
Deviations (per redesign plan): campaigns/variants/simulations rows are
populated immediately, and lineage/segment columns are added up front.
"""

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from ..extensions import db


def _utcnow():
    return datetime.now(timezone.utc)


# JSON that becomes JSONB on Postgres but stays portable elsewhere (tests).
JSONB = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime(timezone=True), default=_utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    refresh_tokens = db.relationship("RefreshToken", cascade="all, delete-orphan", backref="user")

    def to_dict(self):
        return {
            "id": str(self.id),
            "email": self.email,
            "display_name": self.display_name,
        }


class RefreshToken(db.Model):
    __tablename__ = "refresh_tokens"

    id = db.Column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(sa.Uuid(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = db.Column(db.String(255), nullable=False, index=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    revoked = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=_utcnow)


class BrandBrief(db.Model):
    __tablename__ = "brand_briefs"

    id = db.Column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(sa.Uuid(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    # content is the canonical source of truth for the brief text; uploaded
    # files are extracted into it.
    content = db.Column(db.Text)
    file_path = db.Column(db.String(500))
    # Pointer to the legacy file-based project JSON driving the KG build flow.
    project_id = db.Column(db.String(100))
    graph_id = db.Column(db.String(255))
    graph_status = db.Column(db.String(20), default="pending")  # pending|building|ready|failed
    # One of app.services.business_context.BUSINESS_TYPES, or NULL if unset.
    # Shapes ontology + persona generation guidance (see business_context.py).
    business_type = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=_utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    personas = db.relationship("Persona", cascade="all, delete-orphan", backref="brand_brief")

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "content": self.content,
            "file_path": self.file_path,
            "project_id": self.project_id,
            "business_type": self.business_type,
            "graph_id": self.graph_id,
            "graph_status": self.graph_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Persona(db.Model):
    __tablename__ = "personas"

    id = db.Column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(sa.Uuid(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    brand_brief_id = db.Column(sa.Uuid(as_uuid=True), db.ForeignKey("brand_briefs.id", ondelete="CASCADE"), nullable=False, index=True)
    external_id = db.Column(db.String(100))  # OASIS user_id, e.g. "42"
    segment = db.Column(db.String(255))
    # Phase 4: real-data segment this persona was synthesised from.
    segment_id = db.Column(sa.Uuid(as_uuid=True), nullable=True)
    source = db.Column(db.String(20), default="kg")  # kg | segment | hybrid
    data = db.Column(JSONB, nullable=False)  # full OasisAgentProfile dict
    created_at = db.Column(db.DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        db.Index("idx_personas_user_brief", "user_id", "brand_brief_id"),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "brand_brief_id": str(self.brand_brief_id),
            "external_id": self.external_id,
            "segment": self.segment,
            "segment_id": str(self.segment_id) if self.segment_id else None,
            "source": self.source,
            "data": self.data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CampaignRecord(db.Model):
    """DB row for a campaign; the run artifacts stay in uploads/campaigns/."""
    __tablename__ = "campaigns"

    id = db.Column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(sa.Uuid(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    brand_brief_id = db.Column(sa.Uuid(as_uuid=True), db.ForeignKey("brand_briefs.id"), nullable=True)
    # ID of the file-based campaign JSON (camp_* / uuid) used by the runtime.
    campaign_ref = db.Column(db.String(100), index=True)
    brand_name = db.Column(db.String(255))
    campaign_goal = db.Column(db.Text)
    # Iteration lineage (Phase 3): v2 campaigns point at their v1 parent.
    parent_campaign_id = db.Column(sa.Uuid(as_uuid=True), db.ForeignKey("campaigns.id"), nullable=True)
    iteration = db.Column(db.Integer, default=1, nullable=False)
    designer_session_id = db.Column(sa.Uuid(as_uuid=True), nullable=True)
    # One of app.services.business_context.OBJECTIVES, or NULL if unset.
    # Shapes which funnel tier's actions are emphasised when scoring (see
    # business_context.funnel_emphasis / VariantScorer).
    objective = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=_utcnow)

    variants = db.relationship("CampaignVariantRecord", cascade="all, delete-orphan", backref="campaign")

    def to_dict(self):
        return {
            "id": str(self.id),
            "campaign_ref": self.campaign_ref,
            "brand_brief_id": str(self.brand_brief_id) if self.brand_brief_id else None,
            "brand_name": self.brand_name,
            "campaign_goal": self.campaign_goal,
            "parent_campaign_id": str(self.parent_campaign_id) if self.parent_campaign_id else None,
            "iteration": self.iteration,
            "objective": self.objective,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CampaignVariantRecord(db.Model):
    __tablename__ = "campaign_variants"

    id = db.Column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = db.Column(sa.Uuid(as_uuid=True), db.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_ref = db.Column(db.String(100))  # variant_id in the campaign JSON
    variant_name = db.Column(db.String(255))
    channel = db.Column(db.String(50))
    content = db.Column(JSONB)  # serialized CampaignContent
    target_segment = db.Column(db.String(255))
    status = db.Column(db.String(20), default="pending")
    # Phase 2 provenance: user-authored vs AI-proposed.
    provenance = db.Column(db.String(10), default="user")  # user | ai
    # Designer agent's stated reasoning for this variant, and the specific,
    # falsifiable hypothesis it's testing (e.g. "test whether Gen Z prefers
    # short-form video over carousel") — checked against outcomes by the
    # Phase 3 insight agent's hypothesis_check tool. NULL for user-authored variants.
    rationale = db.Column(db.Text, nullable=True)
    hypothesis = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=_utcnow)

    def to_dict(self):
        return {
            "id": str(self.id),
            "variant_ref": self.variant_ref,
            "variant_name": self.variant_name,
            "channel": self.channel,
            "content": self.content,
            "target_segment": self.target_segment,
            "status": self.status,
            "provenance": self.provenance,
            "rationale": self.rationale,
            "hypothesis": self.hypothesis,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SimulationRecord(db.Model):
    __tablename__ = "simulations"

    id = db.Column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(sa.Uuid(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id = db.Column(sa.Uuid(as_uuid=True), db.ForeignKey("campaigns.id"), nullable=True)
    brand_brief_id = db.Column(sa.Uuid(as_uuid=True), db.ForeignKey("brand_briefs.id"), nullable=True)
    # The string sim id used throughout the file-based runtime ("sim_abc...").
    sim_key = db.Column(db.String(100), index=True)
    status = db.Column(db.String(20), default="pending")  # pending|running|completed|failed
    result_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime(timezone=True), default=_utcnow)


class Channel(db.Model):
    """A marketing channel definition: action vocabulary, weights, mechanics.

    Builtin channels have user_id=NULL and are seeded from
    app/data/builtin_channels.json. Custom channels are user-scoped, usually
    LLM-drafted from a free-text description then user-edited/approved.
    """
    __tablename__ = "channels"

    id = db.Column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(sa.Uuid(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    key = db.Column(db.String(50), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    kind = db.Column(db.String(20), nullable=False, default="feed")  # feed | direct
    available_actions = db.Column(JSONB, nullable=False)   # ["like_post", "create_post", ...] (real ActionType values)
    action_weights = db.Column(JSONB, nullable=False)      # {"like_post": 0.3, ...}
    funnel_map = db.Column(JSONB, nullable=False, default=dict)  # {"attention": [...], "engagement": [...], ...}
    formats = db.Column(JSONB, nullable=False, default=list)     # ["VideoAd", "CarouselPost", ...]
    framing_template = db.Column(db.Text, nullable=False)  # e.g. "[{channel} {format}] {headline} ..."
    mechanics = db.Column(JSONB, nullable=False, default=dict)   # {visibility, activation, max_rounds_default}
    description = db.Column(db.Text)
    weights_rationale = db.Column(db.Text)
    is_builtin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=_utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "key", name="uq_channel_user_key"),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "key": self.key,
            "name": self.name,
            "kind": self.kind,
            "available_actions": self.available_actions,
            "action_weights": self.action_weights,
            "funnel_map": self.funnel_map,
            "formats": self.formats,
            "framing_template": self.framing_template,
            "mechanics": self.mechanics,
            "description": self.description,
            "weights_rationale": self.weights_rationale,
            "is_builtin": self.is_builtin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AgentSession(db.Model):
    """A conversational session with the Designer (Phase 2) or Insight (Phase 3) agent.

    `messages` is the full chat transcript (list of {role, content, ...} dicts,
    OpenAI chat-completions message shape) so a session can resume exactly
    where it left off. `draft` is the agent's current proposed campaign
    (brand_name, campaign_goal, objective, variants[]) — nothing is launched
    until the user commits it via POST .../commit.
    """
    __tablename__ = "agent_sessions"

    id = db.Column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(sa.Uuid(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    kind = db.Column(db.String(10), nullable=False)  # designer | insight
    brand_brief_id = db.Column(sa.Uuid(as_uuid=True), db.ForeignKey("brand_briefs.id"), nullable=True)
    campaign_id = db.Column(sa.Uuid(as_uuid=True), db.ForeignKey("campaigns.id"), nullable=True)
    simulation_id = db.Column(sa.Uuid(as_uuid=True), db.ForeignKey("simulations.id"), nullable=True)
    messages = db.Column(JSONB, nullable=False, default=list)
    draft = db.Column(JSONB, nullable=True)
    status = db.Column(db.String(20), default="active", nullable=False)  # active | committed | abandoned
    created_at = db.Column(db.DateTime(timezone=True), default=_utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    def to_dict(self):
        return {
            "id": str(self.id),
            "kind": self.kind,
            "brand_brief_id": str(self.brand_brief_id) if self.brand_brief_id else None,
            "campaign_id": str(self.campaign_id) if self.campaign_id else None,
            "simulation_id": str(self.simulation_id) if self.simulation_id else None,
            "messages": self.messages or [],
            "draft": self.draft,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Dataset(db.Model):
    """A user-uploaded customer export (CRM dump, orders, newsletter list).

    `schema_map` records the confirmed source-column -> canonical-field
    mapping (see app/models/customer_schema.py) used at import time.
    `status` tracks the intake pipeline: uploaded -> mapped -> imported ->
    segmented (or failed at any step).
    """
    __tablename__ = "datasets"

    id = db.Column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(sa.Uuid(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    source_type = db.Column(db.String(20), nullable=False)  # csv | xlsx
    file_path = db.Column(db.String(500))  # storage-relative path (see services/storage.py)
    row_count = db.Column(db.Integer, default=0)
    columns = db.Column(JSONB, nullable=True)  # source column names, as uploaded
    schema_map = db.Column(JSONB, nullable=True)  # {source_col: canonical_field | null}
    status = db.Column(db.String(20), default="uploaded", nullable=False)
    error = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=_utcnow)

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "source_type": self.source_type,
            "row_count": self.row_count,
            "columns": self.columns or [],
            "schema_map": self.schema_map,
            "status": self.status,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Customer(db.Model):
    """One imported row from a Dataset, mapped to the canonical schema.

    `attributes` holds canonical fields plus any unmapped source columns
    passed through as-is (see CanonicalCustomer.extras). Any column mapped to
    an identity-like canonical field (external_id) is one-way hashed before
    it ever reaches this table — see services/dataset_mapper.py — so raw PII
    is never persisted or available to prompt an LLM with.
    """
    __tablename__ = "customers"

    id = db.Column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(sa.Uuid(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id = db.Column(sa.Uuid(as_uuid=True), db.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    # Cluster membership from the most recent segment_dataset() run — set by
    # services/segmentation_engine.py, needed for per-segment CSV export and
    # merge/split without re-clustering.
    segment_id = db.Column(sa.Uuid(as_uuid=True), db.ForeignKey("segments.id", ondelete="SET NULL"), nullable=True, index=True)
    external_id = db.Column(db.String(255), nullable=True)  # hashed
    attributes = db.Column(JSONB, nullable=False, default=dict)

    def to_dict(self):
        return {
            "id": str(self.id),
            "dataset_id": str(self.dataset_id),
            "segment_id": str(self.segment_id) if self.segment_id else None,
            "external_id": self.external_id,
            "attributes": self.attributes,
        }


class Segment(db.Model):
    """A named cluster of a Dataset's customers, with aggregate stats used to
    ground persona synthesis (never raw customer rows — see
    services/segmentation_engine.py and oasis_profile_generator.py).
    """
    __tablename__ = "segments"

    id = db.Column(sa.Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(sa.Uuid(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id = db.Column(sa.Uuid(as_uuid=True), db.ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    method = db.Column(db.String(20), default="kmeans")  # kmeans | manual
    definition = db.Column(JSONB, nullable=True)  # {features: [...], centroid: [...]}
    size = db.Column(db.Integer, default=0)
    stats = db.Column(JSONB, nullable=True)  # aggregate distributions for prompting
    status = db.Column(db.String(20), default="draft", nullable=False)  # draft | approved
    created_at = db.Column(db.DateTime(timezone=True), default=_utcnow)

    def to_dict(self):
        return {
            "id": str(self.id),
            "dataset_id": str(self.dataset_id),
            "name": self.name,
            "description": self.description,
            "method": self.method,
            "definition": self.definition,
            "size": self.size,
            "stats": self.stats,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
