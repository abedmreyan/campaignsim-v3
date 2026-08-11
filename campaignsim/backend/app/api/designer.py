"""Designer Agent API (Phase 2) — pre-simulation campaign co-design chat.

Session lifecycle: create (bound to a brand brief, optionally a simulation
for audience_overview) -> exchange messages (each call resumes the
persisted transcript) -> edit the draft directly -> commit, which turns the
session's draft into the exact payload POST /api/simulation/ab_test already
accepts. Nothing is launched from here — commit only hands back a payload
for the frontend to POST itself, keeping the existing ab_test route as the
single place that creates campaign/variant rows and launches subprocesses.
"""

import uuid as uuidlib

from flask import g, jsonify, request

from . import designer_bp
from ..extensions import db
from ..models.orm import AgentSession, BrandBrief, SimulationRecord
from ..services.designer_agent import DesignerAgent
from ..utils.logger import get_logger

logger = get_logger('campaignsim.api.designer')

_CONTENT_FIELDS = ("format", "headline", "body", "cta", "visual_desc", "email_subject", "tone")


def _variant_to_ab_test_shape(v):
    """Draft variants are flat (as produced by DesignerAgent.propose_variants /
    validated by validate_proposal); ab_test expects content fields nested
    under a `content` object. Reshape without mutating the stored draft."""
    return {
        "variant_name": v.get("variant_name", "Variant"),
        "channel": v.get("channel", ""),
        "target_segment": v.get("target_segment", ""),
        "max_rounds": v.get("max_rounds") or 0,
        "provenance": v.get("provenance") or "user",
        "rationale": v.get("rationale"),
        "hypothesis": v.get("hypothesis"),
        "content": {field: v.get(field, "") for field in _CONTENT_FIELDS},
    }


def _get_owned_session(session_id):
    try:
        sid = uuidlib.UUID(str(session_id))
    except ValueError:
        return None
    return AgentSession.query.filter_by(id=sid, user_id=g.current_user.id, kind='designer').first()


@designer_bp.route('/sessions', methods=['POST'])
def create_session():
    data = request.get_json(silent=True) or {}

    # simulation_id here is the file-based sim_key (e.g. "sim_xxxx"), the only
    # simulation handle the frontend ever holds — same convention as ab_test,
    # launch_variant, etc. The SimulationRecord.id UUID is an internal FK only.
    simulation_id = data.get('simulation_id')
    sim_record = None
    if simulation_id:
        sim_record = SimulationRecord.query.filter_by(
            sim_key=str(simulation_id), user_id=g.current_user.id
        ).first()
        if not sim_record:
            return jsonify({"success": False, "error": "Simulation not found"}), 404

    # brand_brief_id is optional from the caller — the parent simulation already
    # knows which brief it belongs to (set at /api/simulation/create time), so
    # default to that instead of making the frontend track it separately.
    brand_brief_id = data.get('brand_brief_id')
    brief = None
    if brand_brief_id:
        try:
            brief = BrandBrief.query.filter_by(
                id=uuidlib.UUID(str(brand_brief_id)), user_id=g.current_user.id
            ).first()
        except ValueError:
            brief = None
        if not brief:
            return jsonify({"success": False, "error": "Brief not found"}), 404
    elif sim_record and sim_record.brand_brief_id:
        brief = BrandBrief.query.filter_by(id=sim_record.brand_brief_id, user_id=g.current_user.id).first()

    session = AgentSession(
        user_id=g.current_user.id,
        kind='designer',
        brand_brief_id=brief.id if brief else None,
        simulation_id=sim_record.id if sim_record else None,
        messages=[],
        draft=None,
        status='active',
    )
    db.session.add(session)
    db.session.commit()
    return jsonify({"success": True, "data": session.to_dict()}), 201


@designer_bp.route('/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    session = _get_owned_session(session_id)
    if not session:
        return jsonify({"success": False, "error": "Session not found"}), 404
    return jsonify({"success": True, "data": session.to_dict()})


@designer_bp.route('/sessions/<session_id>/messages', methods=['POST'])
def post_message(session_id):
    session = _get_owned_session(session_id)
    if not session:
        return jsonify({"success": False, "error": "Session not found"}), 404
    if session.status != 'active':
        return jsonify({"success": False, "error": f"Session is {session.status}, not active"}), 400

    data = request.get_json(silent=True) or {}
    user_message = (data.get('message') or '').strip()
    if not user_message:
        return jsonify({"success": False, "error": "message is required"}), 400

    agent = DesignerAgent(
        user_id=g.current_user.id,
        brand_brief_id=session.brand_brief_id,
        simulation_id=session.simulation_id,
    )
    try:
        result = agent.send_message(session.messages or [], user_message)
    except Exception as e:
        logger.error(f"designer send_message failed for session {session_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 502

    session.messages = result["messages"]
    if result.get("draft") is not None:
        draft = result["draft"]
        for variant in draft.get("variants", []):
            variant.setdefault("provenance", "ai")
        session.draft = draft
    db.session.commit()

    return jsonify({
        "success": True,
        "data": {
            "reply": result["reply"],
            "tool_calls_log": result["tool_calls_log"],
            "draft": session.draft,
            "session": session.to_dict(),
        },
    })


@designer_bp.route('/sessions/<session_id>/draft', methods=['PUT'])
def update_draft(session_id):
    session = _get_owned_session(session_id)
    if not session:
        return jsonify({"success": False, "error": "Session not found"}), 404
    if session.status != 'active':
        return jsonify({"success": False, "error": f"Session is {session.status}, not active"}), 400

    draft = request.get_json(silent=True) or {}
    agent = DesignerAgent(user_id=g.current_user.id)
    errors = agent.validate_proposal(draft)
    if errors:
        return jsonify({"success": False, "error": "Invalid draft", "details": errors}), 400

    for variant in draft.get("variants", []):
        variant.setdefault("provenance", "user")
    # Reserved, internal-only lineage keys (Phase 3 — set when this session was
    # opened from an applied Insight redesign) survive edits even though the
    # frontend's edit form never sends them itself.
    existing = session.draft or {}
    for key in ("parent_campaign_id", "iteration"):
        if key in existing and key not in draft:
            draft[key] = existing[key]
    session.draft = draft
    db.session.commit()
    return jsonify({"success": True, "data": session.to_dict()})


@designer_bp.route('/sessions/<session_id>/commit', methods=['POST'])
def commit_session(session_id):
    session = _get_owned_session(session_id)
    if not session:
        return jsonify({"success": False, "error": "Session not found"}), 404
    if session.status != 'active':
        return jsonify({"success": False, "error": f"Session is {session.status}, not active"}), 400
    if not session.draft or not session.draft.get("variants"):
        return jsonify({"success": False, "error": "Session has no draft to commit"}), 400
    if not session.simulation_id:
        return jsonify({"success": False, "error": "Session has no linked simulation to launch against"}), 400

    sim_record = SimulationRecord.query.filter_by(id=session.simulation_id, user_id=g.current_user.id).first()
    if not sim_record:
        return jsonify({"success": False, "error": "Linked simulation not found"}), 404

    agent = DesignerAgent(user_id=g.current_user.id)
    errors = agent.validate_proposal(session.draft)
    if errors:
        return jsonify({"success": False, "error": "Draft is no longer valid", "details": errors}), 400

    draft = session.draft
    payload = {
        "simulation_id": sim_record.sim_key,
        "brand_name": draft.get("brand_name", ""),
        "campaign_goal": draft.get("campaign_goal", ""),
        "objective": draft.get("objective", ""),
        "variants": [_variant_to_ab_test_shape(v) for v in draft.get("variants", [])],
    }
    if draft.get("parent_campaign_id"):
        payload["parent_campaign_id"] = draft["parent_campaign_id"]
        payload["iteration"] = draft.get("iteration", 1)

    session.status = 'committed'
    db.session.commit()

    return jsonify({"success": True, "data": {"payload": payload}})
