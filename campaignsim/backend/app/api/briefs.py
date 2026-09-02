"""Brand brief API (spec §6) — briefs are the user's reusable campaign inputs.

A brief's `content` column is the canonical text. Uploading a file extracts
its text into `content`; rebuild-graph regenerates the ontology + KG from the
current content through the same project pipeline the graph API uses.
"""

import os
import traceback
import uuid as uuidlib

from flask import current_app, g, jsonify, request

from . import briefs_bp
from ..config import Config
from ..extensions import db
from ..models.orm import BrandBrief, Persona
from ..models.project import ProjectManager, ProjectStatus
from ..services.business_context import BUSINESS_TYPES
from ..services.graph_build_job import start_graph_build
from ..services.ontology_generator import OntologyGenerator
from ..services.storage import storage
from ..services.text_processor import TextProcessor
from ..utils.file_parser import FileParser
from ..utils.logger import get_logger

logger = get_logger('campaignsim.api.briefs')

ALLOWED_EXTS = Config.ALLOWED_EXTENSIONS


def _get_owned_brief(brief_id):
    try:
        bid = uuidlib.UUID(str(brief_id))
    except ValueError:
        return None
    return BrandBrief.query.filter_by(id=bid, user_id=g.current_user.id).first()


@briefs_bp.route('', methods=['GET'])
@briefs_bp.route('/', methods=['GET'])
def list_briefs():
    briefs = (
        BrandBrief.query.filter_by(user_id=g.current_user.id)
        .order_by(BrandBrief.created_at.desc())
        .all()
    )
    return jsonify({"success": True, "data": [b.to_dict() for b in briefs]})


@briefs_bp.route('', methods=['POST'])
@briefs_bp.route('/', methods=['POST'])
def create_brief():
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({"success": False, "error": "name is required"}), 400

    business_type = data.get('business_type')
    if business_type and business_type not in BUSINESS_TYPES:
        return jsonify({
            "success": False,
            "error": f"business_type must be one of {BUSINESS_TYPES}",
        }), 400

    brief = BrandBrief(
        user_id=g.current_user.id,
        name=name,
        content=data.get('content') or '',
        business_type=business_type,
    )
    db.session.add(brief)
    db.session.commit()
    return jsonify({"success": True, "data": brief.to_dict()}), 201


@briefs_bp.route('/<brief_id>', methods=['GET'])
def get_brief(brief_id):
    brief = _get_owned_brief(brief_id)
    if not brief:
        return jsonify({"success": False, "error": "Brief not found"}), 404
    return jsonify({"success": True, "data": brief.to_dict()})


@briefs_bp.route('/<brief_id>', methods=['PUT'])
def update_brief(brief_id):
    brief = _get_owned_brief(brief_id)
    if not brief:
        return jsonify({"success": False, "error": "Brief not found"}), 404

    data = request.get_json(silent=True) or {}
    if 'name' in data and (data['name'] or '').strip():
        brief.name = data['name'].strip()
    if 'content' in data:
        brief.content = data['content'] or ''
    if 'business_type' in data:
        business_type = data['business_type']
        if business_type and business_type not in BUSINESS_TYPES:
            return jsonify({
                "success": False,
                "error": f"business_type must be one of {BUSINESS_TYPES}",
            }), 400
        brief.business_type = business_type or None
    db.session.commit()
    return jsonify({"success": True, "data": brief.to_dict()})


@briefs_bp.route('/<brief_id>', methods=['DELETE'])
def delete_brief(brief_id):
    brief = _get_owned_brief(brief_id)
    if not brief:
        return jsonify({"success": False, "error": "Brief not found"}), 404

    # Remove the associated legacy project directory (KG build inputs).
    if brief.project_id:
        ProjectManager.delete_project(brief.project_id)
    if brief.file_path:
        try:
            storage.delete_file(str(g.current_user.id), brief.file_path)
        except Exception:
            pass

    db.session.delete(brief)  # personas cascade via FK
    db.session.commit()
    return jsonify({"success": True})


@briefs_bp.route('/<brief_id>/upload', methods=['POST'])
def upload_brief_file(brief_id):
    """Attach/replace the uploaded source file; its text becomes content."""
    brief = _get_owned_brief(brief_id)
    if not brief:
        return jsonify({"success": False, "error": "Brief not found"}), 404

    file = request.files.get('file')
    if not file or not file.filename:
        return jsonify({"success": False, "error": "file is required"}), 400
    ext = os.path.splitext(file.filename)[1].lower().lstrip('.')
    if ext not in ALLOWED_EXTS:
        return jsonify({
            "success": False,
            "error": f"Unsupported file type .{ext} (allowed: {', '.join(sorted(ALLOWED_EXTS))})"
        }), 400

    key = os.path.join('briefs', str(brief.id), f"source.{ext}")
    path = storage.save_file(str(g.current_user.id), key, file.read())

    try:
        text = FileParser.extract_text(path)
        text = TextProcessor.preprocess_text(text)
    except Exception as e:
        return jsonify({"success": False, "error": f"Could not extract text: {e}"}), 400

    brief.file_path = key
    brief.content = text
    db.session.commit()
    return jsonify({"success": True, "data": brief.to_dict()})


@briefs_bp.route('/<brief_id>/rebuild-graph', methods=['POST'])
def rebuild_graph(brief_id):
    """Regenerate ontology + knowledge graph from the brief's current content.

    Creates (or replaces) the brief's backing project, then launches the same
    background build used by /api/graph/build.
    """
    brief = _get_owned_brief(brief_id)
    if not brief:
        return jsonify({"success": False, "error": "Brief not found"}), 404
    if not (brief.content or '').strip():
        return jsonify({"success": False, "error": "Brief has no content"}), 400

    data = request.get_json(silent=True) or {}
    simulation_requirement = (
        data.get('simulation_requirement')
        or f"Analyse the market landscape for {brief.name} campaigns"
    )

    try:
        # Fresh project per rebuild keeps the legacy pipeline unchanged.
        if brief.project_id:
            ProjectManager.delete_project(brief.project_id)

        project = ProjectManager.create_project(name=brief.name)
        project.simulation_requirement = simulation_requirement
        ProjectManager.save_extracted_text(project.project_id, brief.content)
        project.total_text_length = len(brief.content)

        generator = OntologyGenerator()
        ontology = generator.generate(
            document_texts=[brief.content],
            simulation_requirement=simulation_requirement,
            business_type=brief.business_type,
        )
        project.ontology = {
            "entity_types": ontology.get("entity_types", []),
            "edge_types": ontology.get("edge_types", []),
        }
        project.analysis_summary = ontology.get("analysis_summary", "")
        project.status = ProjectStatus.ONTOLOGY_GENERATED
        ProjectManager.save_project(project)

        brief.project_id = project.project_id
        brief.graph_id = None
        brief.graph_status = 'building'
        db.session.commit()

        app_obj = current_app._get_current_object()
        bid = brief.id

        def _sync(graph_id=None, status='ready'):
            with app_obj.app_context():
                b = db.session.get(BrandBrief, bid)
                if b:
                    if graph_id:
                        b.graph_id = graph_id
                    b.graph_status = status
                    db.session.commit()

        task_id = start_graph_build(
            project=project,
            text=brief.content,
            graph_name=brief.name,
            chunk_size=Config.DEFAULT_CHUNK_SIZE,
            chunk_overlap=Config.DEFAULT_CHUNK_OVERLAP,
            on_success=lambda gid: _sync(graph_id=gid, status='ready'),
            on_failure=lambda err: _sync(status='failed'),
            user_id=g.current_user.id,
        )

        return jsonify({
            "success": True,
            "data": {
                "brief": brief.to_dict(),
                "project_id": project.project_id,
                "task_id": task_id,
                "ontology": project.ontology,
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"rebuild-graph failed for brief {brief_id}: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


# ---------------- Personas (DB-backed, spec §6) ----------------

@briefs_bp.route('/<brief_id>/personas', methods=['GET'])
def list_personas(brief_id):
    brief = _get_owned_brief(brief_id)
    if not brief:
        return jsonify({"success": False, "error": "Brief not found"}), 404
    personas = (
        Persona.query.filter_by(user_id=g.current_user.id, brand_brief_id=brief.id)
        .order_by(Persona.created_at.asc())
        .all()
    )
    return jsonify({"success": True, "data": [p.to_dict() for p in personas]})


@briefs_bp.route('/<brief_id>/personas/clear', methods=['POST'])
def clear_personas(brief_id):
    brief = _get_owned_brief(brief_id)
    if not brief:
        return jsonify({"success": False, "error": "Brief not found"}), 404
    deleted = Persona.query.filter_by(
        user_id=g.current_user.id, brand_brief_id=brief.id
    ).delete()
    db.session.commit()
    return jsonify({"success": True, "deleted": deleted})


@briefs_bp.route('/personas/<persona_id>', methods=['DELETE'])
def delete_persona(persona_id):
    try:
        pid = uuidlib.UUID(str(persona_id))
    except ValueError:
        return jsonify({"success": False, "error": "Persona not found"}), 404
    persona = Persona.query.filter_by(id=pid, user_id=g.current_user.id).first()
    if not persona:
        return jsonify({"success": False, "error": "Persona not found"}), 404
    db.session.delete(persona)
    db.session.commit()
    return jsonify({"success": True})
