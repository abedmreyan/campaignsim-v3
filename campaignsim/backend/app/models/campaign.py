"""
CampaignSim — Campaign and Variant data models.

A Campaign holds multiple CampaignVariants. Each variant is a single
combination of content format, message, channel, and target segment.
Results (action logs) are produced per variant and scored in Phase 4.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


# Used only when no channel registry definition is available (e.g. a channel
# key that was deleted after the campaign ran, or plain-dataclass unit tests
# with no Flask/DB context). Real formatting comes from Channel.framing_template.
_DEFAULT_FRAMING_TEMPLATE = "[{channel} {format}] {headline}"


@dataclass
class CampaignContent:
    """The creative content for a single variant."""
    format: str                  # "VideoAd", "CarouselPost", "EmailNewsletter", "SearchAd"
    headline: str
    body: str
    cta: str
    visual_desc: str = ""        # describes the visual for LLM context
    email_subject: str = ""      # only for email variants
    tone: str = "neutral"        # "professional", "playful", "urgent", "inspirational"

    def format_for_channel(self, channel: str, framing_template: Optional[str] = None) -> str:
        """
        Build the framed campaign_content string that the simulation script
        posts as the brand agent's initial post.

        `framing_template` comes from the channel registry (Channel.framing_template,
        e.g. "[Instagram {format}] {headline}" or, for email,
        "[Email {format}] Subject: {email_subject} — {headline}"). Falls back to a
        generic template when the caller has no registry lookup available.

        Example output:
            [Instagram VideoAd] Zero Sugar. Zero Wait. | Our cold brew is ready
            in 30 seconds. | CTA: Try it — 20% off | Tone: playful | Visual: fast-
            paced barista montage, upbeat music
        """
        template = framing_template or _DEFAULT_FRAMING_TEMPLATE
        try:
            opening = template.format(
                channel=channel.replace("_", " ").title(),
                format=self.format,
                headline=self.headline,
                email_subject=self.email_subject,
                tone=self.tone,
                cta=self.cta,
                body=self.body,
            )
        except (KeyError, IndexError):
            opening = _DEFAULT_FRAMING_TEMPLATE.format(
                channel=channel.replace("_", " ").title(), format=self.format, headline=self.headline
            )

        parts = [opening]
        if self.body:
            parts.append(self.body)
        if self.cta:
            parts.append(f"CTA: {self.cta}")
        if self.tone and self.tone != "neutral":
            parts.append(f"Tone: {self.tone}")
        if self.visual_desc:
            parts.append(f"Visual: {self.visual_desc}")
        if self.email_subject and "{email_subject}" not in template:
            parts.append(f"Subject: {self.email_subject}")

        return " | ".join(parts)


@dataclass
class CampaignVariant:
    """A single testable combination of content + channel + segment."""
    variant_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    variant_name: str = ""           # e.g. "Video on Instagram – Millennials"
    channel: str = "instagram"       # "instagram", "email", "tiktok", "linkedin"
    content: Optional[CampaignContent] = None
    target_segment: str = ""         # name of persona group (empty = all personas)
    max_rounds: int = 0              # 0 = unset -> VariantRunner falls back to the channel's own default

    # Phase 2 — Designer agent provenance (see CampaignVariantRecord.provenance)
    provenance: str = "user"         # "user" | "ai"
    rationale: Optional[str] = None  # why the agent chose this variant, if AI-proposed
    hypothesis: Optional[str] = None # the specific claim this variant tests, if AI-proposed

    # Filled in after simulation is launched
    variant_sim_id: Optional[str] = None   # composite ID used in SimulationRunner
    status: str = "pending"                # "pending", "running", "completed", "failed"
    output_dir: Optional[str] = None
    error: Optional[str] = None

    def formatted_content(self, framing_template: Optional[str] = None) -> str:
        """Return the channel-framed content string for the simulation script.

        `framing_template` should come from the channel registry (looked up by
        the caller, e.g. VariantRunner, which has DB access); falls back to a
        generic template if not provided.
        """
        if self.content is None:
            return ""
        return self.content.format_for_channel(self.channel, framing_template)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


@dataclass
class Campaign:
    """Top-level campaign. Contains multiple variants."""
    campaign_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    simulation_id: str = ""          # parent simulation ID (has the profiles CSV)
    brand_name: str = ""
    campaign_goal: str = ""
    # One of app.services.business_context.OBJECTIVES, or "" if unset. Shapes
    # which funnel tier's actions VariantScorer emphasises (see business_context.py).
    objective: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    variants: List[CampaignVariant] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Campaign":
        variants = []
        for v in data.get("variants", []):
            content_data = v.get("content") or {}
            if content_data:
                content = CampaignContent(**{
                    k: content_data.get(k, "")
                    for k in CampaignContent.__dataclass_fields__
                })
            else:
                content = None
            variants.append(CampaignVariant(
                **{k: v[k] for k in CampaignVariant.__dataclass_fields__ if k != "content" and k in v},
                content=content,
            ))
        return cls(
            campaign_id=data.get("campaign_id", str(uuid.uuid4())),
            simulation_id=data.get("simulation_id", ""),
            brand_name=data.get("brand_name", ""),
            campaign_goal=data.get("campaign_goal", ""),
            objective=data.get("objective", ""),
            created_at=data.get("created_at", datetime.now().isoformat()),
            variants=variants,
        )
