"""Channel registry — marketing channels as data, not code.

Builtin channels are seeded from app/data/builtin_channels.json (user_id=NULL,
is_builtin=True). Custom channels are user-scoped rows, either hand-authored
or LLM-drafted from a free-text description and then user-edited/approved.

Action vocabulary note: `available_actions`/`action_weights`/`funnel_map` keys
MUST be real OASIS ActionType.value strings (lowercase snake_case, e.g.
"create_post", "like_post") — these are what actually appear in the
simulation's actions.jsonl. See CAMEL-AI OASIS's ActionType enum.
"""

import json
import os
from typing import Any, Dict, List, Optional

from ..extensions import db
from ..models.orm import Channel
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger

logger = get_logger("campaignsim.services.channel_registry")

_SEED_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "builtin_channels.json")

# The only actions a channel definition is allowed to reference — kept in
# sync with CAMEL-AI OASIS's ActionType enum (social_platform/typing.py).
VALID_ACTIONS = {
    "do_nothing", "refresh", "search_user", "search_posts", "create_post",
    "like_post", "unlike_post", "dislike_post", "undo_dislike_post",
    "report_post", "follow", "unfollow", "mute", "unmute", "trend", "repost",
    "quote_post", "create_comment", "like_comment", "unlike_comment",
    "dislike_comment", "undo_dislike_comment", "purchase_product", "interview",
}

VALID_KINDS = {"feed", "direct"}


def seed_builtin_channels() -> int:
    """Idempotently insert/update builtin channel rows from the JSON seed file.

    Safe to call on every app startup or migration — upserts by (user_id=NULL, key).
    Returns the number of rows created or updated.
    """
    with open(_SEED_PATH, "r", encoding="utf-8") as f:
        definitions = json.load(f)

    changed = 0
    for d in definitions:
        errors = validate_definition(d)
        if errors:
            raise ValueError(f"Invalid builtin channel '{d.get('key')}': {errors}")

        existing = Channel.query.filter_by(user_id=None, key=d["key"]).first()
        if existing is None:
            db.session.add(Channel(
                user_id=None,
                key=d["key"],
                name=d["name"],
                kind=d["kind"],
                available_actions=d["available_actions"],
                action_weights=d["action_weights"],
                funnel_map=d.get("funnel_map", {}),
                formats=d.get("formats", []),
                framing_template=d["framing_template"],
                mechanics=d.get("mechanics", {}),
                description=d.get("description", ""),
                weights_rationale=d.get("weights_rationale", ""),
                is_builtin=True,
            ))
            changed += 1
        else:
            existing.name = d["name"]
            existing.kind = d["kind"]
            existing.available_actions = d["available_actions"]
            existing.action_weights = d["action_weights"]
            existing.funnel_map = d.get("funnel_map", {})
            existing.formats = d.get("formats", [])
            existing.framing_template = d["framing_template"]
            existing.mechanics = d.get("mechanics", {})
            existing.description = d.get("description", "")
            existing.weights_rationale = d.get("weights_rationale", "")
            existing.is_builtin = True
            changed += 1

    db.session.commit()
    logger.info(f"Seeded/updated {changed} builtin channels")
    return changed


def validate_definition(d: Dict[str, Any]) -> List[str]:
    """Return a list of validation error strings (empty = valid)."""
    errors = []
    for field in ("key", "name", "kind", "available_actions", "action_weights", "framing_template"):
        if not d.get(field) and d.get(field) != []:
            errors.append(f"missing required field: {field}")

    if d.get("kind") not in VALID_KINDS:
        errors.append(f"kind must be one of {sorted(VALID_KINDS)}, got {d.get('kind')!r}")

    actions = d.get("available_actions") or []
    if not isinstance(actions, list) or not actions:
        errors.append("available_actions must be a non-empty list")
    else:
        invalid = [a for a in actions if a not in VALID_ACTIONS]
        if invalid:
            errors.append(f"unknown action(s) not in OASIS ActionType: {invalid}")

    weights = d.get("action_weights") or {}
    if not isinstance(weights, dict):
        errors.append("action_weights must be an object")
    else:
        stray = [k for k in weights if k not in actions]
        if stray:
            errors.append(f"action_weights key(s) not in available_actions: {stray}")
        non_numeric = [k for k, v in weights.items() if not isinstance(v, (int, float))]
        if non_numeric:
            errors.append(f"action_weights value(s) not numeric: {non_numeric}")

    funnel_map = d.get("funnel_map") or {}
    if funnel_map:
        if not isinstance(funnel_map, dict) or set(funnel_map.keys()) - {
            "attention", "engagement", "amplification", "intent"
        }:
            errors.append("funnel_map keys must be a subset of attention/engagement/amplification/intent")
        else:
            for tier, tier_actions in funnel_map.items():
                stray = [a for a in tier_actions if a not in actions]
                if stray:
                    errors.append(f"funnel_map[{tier}] references action(s) not in available_actions: {stray}")

    return errors


def list_channels(user_id) -> List[Channel]:
    """All builtin channels plus this user's custom channels."""
    return (
        Channel.query.filter(
            db.or_(Channel.user_id == None, Channel.user_id == user_id)  # noqa: E711
        )
        .order_by(Channel.is_builtin.desc(), Channel.name.asc())
        .all()
    )


def get_channel(user_id, key: str) -> Optional[Channel]:
    """A single channel by key, builtin or owned by this user."""
    return Channel.query.filter(
        Channel.key == key,
        db.or_(Channel.user_id == None, Channel.user_id == user_id),  # noqa: E711
    ).first()


CUSTOM_CHANNEL_SYSTEM_PROMPT = f"""You are a marketing platform engineer designing a new
marketing channel definition for a multi-agent campaign simulator.

The simulator's agents can only take actions from this fixed vocabulary
(these are the ONLY valid strings — do not invent new ones):
{sorted(VALID_ACTIONS)}

Given a short description of a marketing channel, output a JSON object with
these exact fields:
- key: short lowercase snake_case identifier (e.g. "podcast_ad")
- name: human-readable display name
- kind: "feed" (agents see and react to each other's posts/shares — social
  propagation) or "direct" (each agent reacts privately to delivered content,
  no visibility into other agents' reactions — e.g. email, SMS, a push
  notification, a direct mail piece)
- available_actions: 4-7 actions from the vocabulary above that make sense
  for this channel (always include "do_nothing")
- action_weights: a number for each action in available_actions, expressing
  engagement strength. 0.0 for do_nothing. Unwanted/negative outcomes (like
  an unsubscribe/opt-out action) should get a NEGATIVE weight. Otherwise use
  roughly the 0.2-0.9 range, ordered by how much marketing value the action
  signals.
- funnel_map: an object with keys "attention", "engagement", "amplification",
  "intent" (amplification and intent may be empty lists for private/direct
  channels with no sharing mechanic), each mapping to a list of actions from
  available_actions classifying what stage of the funnel that action represents
- formats: 2-4 content format names appropriate to this channel (PascalCase)
- framing_template: a template string for how campaign content is framed to
  agents, using {{format}} and {{headline}} placeholders at minimum, e.g.
  "[Podcast {{format}}] {{headline}}"
- mechanics: {{"visibility": "public"|"private", "activation": "continuous"|"scheduled", "max_rounds_default": int 3-15}}
- description: one sentence describing the channel
- weights_rationale: one or two sentences justifying the weight ordering

Return ONLY the JSON object, no other text."""


def draft_channel_from_description(description: str) -> Dict[str, Any]:
    """Ask the LLM to draft a channel definition from a free-text description.

    Returns the raw drafted dict for the caller to validate/persist — never
    writes to the DB itself (the user must review/approve first).
    """
    client = LLMClient()
    draft = client.chat_json(
        messages=[
            {"role": "system", "content": CUSTOM_CHANNEL_SYSTEM_PROMPT},
            {"role": "user", "content": f"Channel description: {description}"},
        ],
        temperature=0.4,
    )

    errors = validate_definition(draft)
    if errors:
        # One repair attempt: hand the model its own output plus the errors.
        logger.warning(f"Drafted channel failed validation, retrying: {errors}")
        draft = client.chat_json(
            messages=[
                {"role": "system", "content": CUSTOM_CHANNEL_SYSTEM_PROMPT},
                {"role": "user", "content": f"Channel description: {description}"},
                {"role": "assistant", "content": json.dumps(draft)},
                {"role": "user", "content": (
                    "That definition is invalid: " + "; ".join(errors) +
                    ". Return a corrected JSON object only."
                )},
            ],
            temperature=0.2,
        )
        errors = validate_definition(draft)
        if errors:
            raise ValueError(f"LLM could not produce a valid channel definition: {errors}")

    return draft
