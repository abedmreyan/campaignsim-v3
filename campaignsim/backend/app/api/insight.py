"""Insight Agent API (Phase 3) — post-simulation analysis + redesign chat.

Session lifecycle: create (bound to a scored campaign; seeded with the
existing structured report as the first assistant turn) -> exchange messages
(tools drill into scored results, the action log, offline persona
interviews, hypotheses, and iteration lineage) -> optionally propose a
redesign -> apply it, which opens a *new* Designer session pre-loaded with
that redesign as its draft and linked back via parent_campaign_id/iteration.
Committing that Designer session (existing Phase 2 flow) is what actually
launches iteration N+1 — nothing here launches a simulation directly.
"""

import uuid as uuidlib

from flask import g, jsonify, request

from . import insight_bp
from ..extensions import db
from ..models.orm import AgentSession, CampaignRecord, SimulationRecord
from ..services.insight_agent import INSIGHT_SYSTEM_PROMPT, InsightAgent
from ..utils.logger import get_logger

logger = get_logger('campaignsim.api.insight')


def _get_owned_session(session_id):
    try:
        sid = uuidlib.UUID(str(session_id))
    except ValueError:
        return None
    return AgentSession.query.filter_by(id=sid, user_id=g.current_user.id, kind='insight').first()


def _get_owned_campaign_by_ref(campaign_ref):
    return CampaignRecord.query.filter_by(campaign_ref=str(campaign_ref), user_id=g.current_user.id).first()


@insight_bp.route('/sessions', methods=['POST'])
def create_session():
    data = request.get_json(silent=True) or {}

    campaign_ref = data.get('campaign_id')
    if not campaign_ref:
        return jsonify({"success": False, "error": "campaign_id is required"}), 400

    campaign_record = _get_owned_campaign_by_ref(campaign_ref)
    if not campaign_record:
        return jsonify({"success": False, "error": "Campaign not found"}), 404

    try:
        agent = InsightAgent(user_id=g.current_user.id, campaign_id=campaign_record.id)
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404

    if not agent.scored_variants:
        return jsonify({
            "success": False,
            "error": "No scored report for this campaign yet. Generate the recommendation report first.",
        }), 400

    # Seed exactly like send_message() would on an empty history, so later
    # turns (which reuse send_message) don't re-seed and duplicate the report.
    session = AgentSession(
        user_id=g.current_user.id,
        kind='insight',
        brand_brief_id=campaign_record.brand_brief_id,
        campaign_id=campaign_record.id,
        messages=[
            {"role": "system", "content": INSIGHT_SYSTEM_PROMPT},
            {"role": "assistant", "content": agent.initial_report_message()},
        ],
        draft=None,
        status='active',
    )
    db.session.add(session)
    db.session.commit()
    return jsonify({"success": True, "data": session.to_dict()}), 201


@insight_bp.route('/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    session = _get_owned_session(session_id)
    if not session:
        return jsonify({"success": False, "error": "Session not found"}), 404
    return jsonify({"success": True, "data": session.to_dict()})


@insight_bp.route('/sessions/<session_id>/messages', methods=['POST'])
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

    try:
        agent = InsightAgent(user_id=g.current_user.id, campaign_id=session.campaign_id)
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404

    try:
        result = agent.send_message(session.messages or [], user_message)
    except Exception as e:
        logger.error(f"insight send_message failed for session {session_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 502

    session.messages = result["messages"]
    if result.get("draft") is not None:
        session.draft = result["draft"]
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


@insight_bp.route('/sessions/<session_id>/proposals/apply', methods=['POST'])
def apply_proposal(session_id):
    session = _get_owned_session(session_id)
    if not session:
        return jsonify({"success": False, "error": "Session not found"}), 404
    if not session.draft or not session.draft.get("variants"):
        return jsonify({"success": False, "error": "Session has no redesign proposal to apply"}), 400

    campaign_record = CampaignRecord.query.filter_by(id=session.campaign_id, user_id=g.current_user.id).first()
    if not campaign_record:
        return jsonify({"success": False, "error": "Campaign not found"}), 404

    try:
        agent = InsightAgent(user_id=g.current_user.id, campaign_id=campaign_record.id)
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404

    sim_record = None
    if agent.parent_sim_key:
        sim_record = SimulationRecord.query.filter_by(sim_key=agent.parent_sim_key, user_id=g.current_user.id).first()

    draft = dict(session.draft)
    variants = [dict(v) for v in draft.get("variants", [])]
    for variant in variants:
        variant.setdefault("provenance", "ai")
    draft["variants"] = variants
    draft["parent_campaign_id"] = str(campaign_record.id)
    draft["iteration"] = campaign_record.iteration + 1

    designer_session = AgentSession(
        user_id=g.current_user.id,
        kind='designer',
        brand_brief_id=campaign_record.brand_brief_id,
        simulation_id=sim_record.id if sim_record else None,
        messages=[],
        draft=draft,
        status='active',
    )
    db.session.add(designer_session)
    db.session.commit()

    return jsonify({"success": True, "data": {"designer_session": designer_session.to_dict()}}), 201
