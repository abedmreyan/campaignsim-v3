"""Brand brief API routes.

All routes require auth (cs_access cookie).
file_path in BrandBrief is relative to uploads/{user_id}/briefs/.
content TEXT column is the canonical source of truth.
"""

import os
import tempfile

from flask import current_app, g, jsonify, request
from werkzeug.utils import secure_filename

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
    safe_name = secure_filename(file.filename) or "upload"
    key = f"briefs/{brief.id}/{safe_name}"
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
