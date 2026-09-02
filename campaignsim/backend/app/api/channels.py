"""Channel registry API — list/create/edit/delete marketing channel definitions."""

import traceback
import uuid as uuidlib

from flask import g, jsonify, request

from . import channels_bp
from ..extensions import db
from ..models.orm import Channel
from ..services.channel_registry import (
    draft_channel_from_description,
    get_channel,
    list_channels,
    validate_definition,
)
from ..utils.logger import get_logger

logger = get_logger("campaignsim.api.channels")


def _get_owned_custom_channel(channel_id):
    try:
        cid = uuidlib.UUID(str(channel_id))
    except ValueError:
        return None
    return Channel.query.filter_by(id=cid, user_id=g.current_user.id).first()


@channels_bp.route("", methods=["GET"])
@channels_bp.route("/", methods=["GET"])
def list_all():
    channels = list_channels(g.current_user.id)
    return jsonify({"success": True, "data": [c.to_dict() for c in channels]})


@channels_bp.route("/<key>", methods=["GET"])
def get_one(key):
    channel = get_channel(g.current_user.id, key)
    if not channel:
        return jsonify({"success": False, "error": "Channel not found"}), 404
    return jsonify({"success": True, "data": channel.to_dict()})


@channels_bp.route("/draft", methods=["POST"])
def draft():
    """LLM-draft a channel definition from a free-text description.

    Does not persist anything — the caller reviews/edits, then POSTs the
    (possibly edited) result to /api/channels to save it.
    """
    data = request.get_json(silent=True) or {}
    description = (data.get("description") or "").strip()
    if not description:
        return jsonify({"success": False, "error": "description is required"}), 400

    try:
        draft_def = draft_channel_from_description(description)
        return jsonify({"success": True, "data": draft_def})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 422
    except Exception as e:
        logger.error(f"Channel draft failed: {e}")
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500


@channels_bp.route("", methods=["POST"])
@channels_bp.route("/", methods=["POST"])
def create():
    data = request.get_json(silent=True) or {}
    errors = validate_definition(data)
    if errors:
        return jsonify({"success": False, "error": "Invalid channel definition", "details": errors}), 400

    if Channel.query.filter_by(user_id=g.current_user.id, key=data["key"]).first():
        return jsonify({"success": False, "error": f"You already have a channel with key '{data['key']}'"}), 409

    channel = Channel(
        user_id=g.current_user.id,
        key=data["key"],
        name=data["name"],
        kind=data["kind"],
        available_actions=data["available_actions"],
        action_weights=data["action_weights"],
        funnel_map=data.get("funnel_map", {}),
        formats=data.get("formats", []),
        framing_template=data["framing_template"],
        mechanics=data.get("mechanics", {}),
        description=data.get("description", ""),
        weights_rationale=data.get("weights_rationale", ""),
        is_builtin=False,
    )
    db.session.add(channel)
    db.session.commit()
    return jsonify({"success": True, "data": channel.to_dict()}), 201


@channels_bp.route("/<channel_id>", methods=["PUT"])
def update(channel_id):
    channel = _get_owned_custom_channel(channel_id)
    if not channel:
        return jsonify({"success": False, "error": "Channel not found"}), 404

    data = request.get_json(silent=True) or {}
    merged = {**channel.to_dict(), **data}
    errors = validate_definition(merged)
    if errors:
        return jsonify({"success": False, "error": "Invalid channel definition", "details": errors}), 400

    for field in (
        "name", "kind", "available_actions", "action_weights", "funnel_map",
        "formats", "framing_template", "mechanics", "description", "weights_rationale",
    ):
        if field in data:
            setattr(channel, field, data[field])
    db.session.commit()
    return jsonify({"success": True, "data": channel.to_dict()})


@channels_bp.route("/<channel_id>", methods=["DELETE"])
def delete(channel_id):
    channel = _get_owned_custom_channel(channel_id)
    if not channel:
        return jsonify({"success": False, "error": "Channel not found"}), 404
    db.session.delete(channel)
    db.session.commit()
    return jsonify({"success": True})
