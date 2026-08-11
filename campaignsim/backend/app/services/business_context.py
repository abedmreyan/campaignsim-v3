"""Business-type and campaign-objective context.

Business type describes the BRAND (stable, set on the brand brief) and
shapes ontology + persona generation — a B2B brand's audience entities need
role/company/buying-committee framing that a B2C brand's don't.

Objective describes what a given CAMPAIGN is trying to achieve (set per
campaign) and shapes which funnel tier's actions get emphasised when scoring
— an awareness campaign cares about attention/reach, a conversion campaign
cares about intent/purchase signals.

These are template dicts, not per-vertical code branches — new business
types or objectives are added here, not by touching every prompt-building
function that consumes them.
"""

from typing import Dict, List, Optional

BUSINESS_TYPES = ["b2c_product", "b2b", "services", "local", "ecommerce", "app"]
OBJECTIVES = ["awareness", "conversion", "retention", "launch"]

# Appended to the ontology-generation prompt to steer which entity types the
# LLM should look for in the brief, beyond the generic marketing ontology.
ONTOLOGY_GUIDANCE: Dict[str, str] = {
    "b2c_product": (
        "This is a B2C product brand. Prioritise entity types for individual "
        "consumer segments, retail/e-commerce channels, and product variants."
    ),
    "b2b": (
        "This is a B2B brand. In addition to the standard entity types, look for "
        "and extract: job roles/titles involved in purchasing decisions, company "
        "types/sizes in the target market, and buying-committee stages (e.g. "
        "champion, economic buyer, technical evaluator). Persona entities should "
        "represent professional roles, not general consumers."
    ),
    "services": (
        "This is a services brand. Prioritise entity types for client segments, "
        "service tiers/packages, and the trust/referral signals that drive a "
        "services purchase decision."
    ),
    "local": (
        "This is a local/brick-and-mortar business. Prioritise entity types for "
        "the local geographic market, nearby competitor businesses, and "
        "location-based customer segments."
    ),
    "ecommerce": (
        "This is an e-commerce brand. Prioritise entity types for product "
        "categories, purchase-funnel stages, and price-sensitive vs. loyal "
        "customer segments."
    ),
    "app": (
        "This is an app/software product. Prioritise entity types for user "
        "personas by usage tier (free/paid, new/returning), in-app feature "
        "adoption, and app-store/platform distribution channels."
    ),
}

# Appended to the individual-persona-generation prompt for entities belonging
# to this business type. Field additions are described in prose (the
# generator's existing JSON schema stays fixed); the LLM is expected to work
# these details into the `persona` narrative field.
PERSONA_GUIDANCE: Dict[str, str] = {
    "b2c_product": (
        "Ground this persona in personal, individual consumer motivations — "
        "convenience, price, taste/preference, social influence."
    ),
    "b2b": (
        "This persona represents a PROFESSIONAL BUYER, not a general consumer. "
        "Within the `persona` field, explicitly cover: their job title and "
        "seniority, their company's size/industry, their role in the buying "
        "committee (champion / economic buyer / technical evaluator / end "
        "user / blocker), and what business outcome (ROI, risk reduction, "
        "time savings) they personally are judged on."
    ),
    "services": (
        "Ground this persona in trust and outcome expectations — prior "
        "referrals, reviews they'd check, and what a good vs. bad service "
        "experience means to them."
    ),
    "local": (
        "Ground this persona in local, in-person context — proximity, "
        "convenience of visiting, and community/word-of-mouth influence."
    ),
    "ecommerce": (
        "Ground this persona in online shopping behaviour — price comparison "
        "habits, cart-abandonment triggers, review-reading behaviour, and "
        "loyalty/repeat-purchase tendency."
    ),
    "app": (
        "Ground this persona in app usage behaviour — how they discovered "
        "the app, free-vs-paid tier sensitivity, feature usage depth, and "
        "what would make them churn vs. upgrade."
    ),
}

# Per-objective funnel-tier emphasis: engagement_score gets an extra
# multiplier on actions in the named funnel tier(s) (from the channel's
# funnel_map) — reflects that different campaign objectives care about
# different behaviours, not just raw engagement volume.
OBJECTIVE_FUNNEL_EMPHASIS: Dict[str, Dict[str, float]] = {
    "awareness":  {"attention": 1.3, "engagement": 1.0, "amplification": 1.15, "intent": 0.85},
    "conversion": {"attention": 0.85, "engagement": 1.0, "amplification": 0.9, "intent": 1.4},
    "retention":  {"attention": 0.9, "engagement": 1.2, "amplification": 1.0, "intent": 1.1},
    "launch":     {"attention": 1.2, "engagement": 1.1, "amplification": 1.2, "intent": 1.0},
}


def ontology_guidance(business_type: Optional[str]) -> str:
    return ONTOLOGY_GUIDANCE.get((business_type or "").lower(), "")


def persona_guidance(business_type: Optional[str]) -> str:
    return PERSONA_GUIDANCE.get((business_type or "").lower(), "")


def funnel_emphasis(objective: Optional[str]) -> Dict[str, float]:
    """Multiplier per funnel tier for the given objective; 1.0 for every tier
    (no-op) when objective is unset or unrecognised."""
    return OBJECTIVE_FUNNEL_EMPHASIS.get(
        (objective or "").lower(),
        {"attention": 1.0, "engagement": 1.0, "amplification": 1.0, "intent": 1.0},
    )
