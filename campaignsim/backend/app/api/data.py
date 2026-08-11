"""Dataset intake, segmentation, and segment-grounded persona synthesis API
(Phase 4 — CRM/data integration).

Pipeline: upload a CSV/XLSX -> review/confirm the LLM-proposed column mapping
-> import into the canonical Customer schema -> cluster into segments ->
review/rename/approve segments -> generate personas grounded in approved
segments' aggregate stats for a specific simulation.

Import and segmentation run as background tasks (see models/task.py, the
same TaskManager used by graph build / campaign report generation) and are
polled via the existing generic GET /api/graph/task/<task_id>.
"""

import csv
import io
import os
import threading
import uuid as uuidlib

import pandas as pd
from flask import current_app, g, jsonify, request, send_file

from . import data_bp
from ..config import Config
from ..extensions import db
from ..models.customer_schema import CANONICAL_FIELDS
from ..models.orm import Customer, Dataset, Segment
from ..services.dataset_mapper import import_dataset, propose_mapping, read_dataset_file
from ..services.segmentation_engine import segment_dataset
from ..services.storage import storage
from ..utils.logger import get_logger

logger = get_logger('campaignsim.api.data')


def _get_owned_dataset(dataset_id):
    try:
        did = uuidlib.UUID(str(dataset_id))
    except ValueError:
        return None
    return Dataset.query.filter_by(id=did, user_id=g.current_user.id).first()


def _get_owned_segment(segment_id):
    try:
        sid = uuidlib.UUID(str(segment_id))
    except ValueError:
        return None
    return Segment.query.filter_by(id=sid, user_id=g.current_user.id).first()


def _load_dataframe(dataset: Dataset) -> pd.DataFrame:
    return read_dataset_file(dataset.file_path, dataset.source_type)


# ---------------- Datasets ----------------

@data_bp.route('/datasets', methods=['GET'])
def list_datasets():
    datasets = Dataset.query.filter_by(user_id=g.current_user.id).order_by(Dataset.created_at.desc()).all()
    return jsonify({"success": True, "data": [d.to_dict() for d in datasets]})


@data_bp.route('/datasets', methods=['POST'])
def upload_dataset():
    file = request.files.get('file')
    if not file or not file.filename:
        return jsonify({"success": False, "error": "file is required"}), 400
    ext = os.path.splitext(file.filename)[1].lower().lstrip('.')
    if ext not in Config.DATASET_ALLOWED_EXTENSIONS:
        return jsonify({
            "success": False,
            "error": f"Unsupported file type .{ext} (allowed: {', '.join(sorted(Config.DATASET_ALLOWED_EXTENSIONS))})",
        }), 400

    name = (request.form.get('name') or os.path.splitext(file.filename)[0]).strip()
    dataset_id = uuidlib.uuid4()
    key = os.path.join('datasets', str(dataset_id), f"source.{ext}")
    path = storage.save_file(str(g.current_user.id), key, file.read())

    try:
        df = read_dataset_file(path, ext)
    except Exception as e:
        storage.delete_file(str(g.current_user.id), key)
        return jsonify({"success": False, "error": f"Could not parse file: {e}"}), 400

    dataset = Dataset(
        id=dataset_id,
        user_id=g.current_user.id,
        name=name or "Untitled dataset",
        source_type=ext,
        file_path=path,
        row_count=len(df),
        columns=list(df.columns),
        status="uploaded",
    )
    db.session.add(dataset)
    db.session.commit()
    return jsonify({"success": True, "data": dataset.to_dict()}), 201


@data_bp.route('/datasets/<dataset_id>', methods=['GET'])
def get_dataset(dataset_id):
    dataset = _get_owned_dataset(dataset_id)
    if not dataset:
        return jsonify({"success": False, "error": "Dataset not found"}), 404
    return jsonify({"success": True, "data": dataset.to_dict()})


@data_bp.route('/datasets/<dataset_id>', methods=['DELETE'])
def delete_dataset(dataset_id):
    dataset = _get_owned_dataset(dataset_id)
    if not dataset:
        return jsonify({"success": False, "error": "Dataset not found"}), 404
    if dataset.file_path:
        try:
            storage.delete_file(str(g.current_user.id), os.path.join('datasets', str(dataset.id)))
        except Exception:
            pass
    db.session.delete(dataset)  # customers/segments cascade via FK
    db.session.commit()
    return jsonify({"success": True})


@data_bp.route('/datasets/<dataset_id>/mapping', methods=['GET'])
def get_mapping(dataset_id):
    dataset = _get_owned_dataset(dataset_id)
    if not dataset:
        return jsonify({"success": False, "error": "Dataset not found"}), 404

    if dataset.schema_map is None:
        try:
            df = _load_dataframe(dataset)
        except Exception as e:
            return jsonify({"success": False, "error": f"Could not read dataset file: {e}"}), 400
        dataset.schema_map = propose_mapping(df)
        db.session.commit()

    return jsonify({
        "success": True,
        "data": {
            "columns": dataset.columns or [],
            "mapping": dataset.schema_map,
            "canonical_fields": CANONICAL_FIELDS,
        },
    })


@data_bp.route('/datasets/<dataset_id>/mapping', methods=['PUT'])
def update_mapping(dataset_id):
    dataset = _get_owned_dataset(dataset_id)
    if not dataset:
        return jsonify({"success": False, "error": "Dataset not found"}), 404

    data = request.get_json(silent=True) or {}
    mapping = data.get('mapping')
    if not isinstance(mapping, dict):
        return jsonify({"success": False, "error": "mapping (object) is required"}), 400

    valid_columns = set(dataset.columns or [])
    errors = []
    for col, field in mapping.items():
        if col not in valid_columns:
            errors.append(f"'{col}' is not a column in this dataset")
        if field is not None and field not in CANONICAL_FIELDS:
            errors.append(f"'{field}' is not a valid canonical field")
    if errors:
        return jsonify({"success": False, "error": "Invalid mapping", "details": errors}), 400

    dataset.schema_map = mapping
    dataset.status = "mapped"
    db.session.commit()
    return jsonify({"success": True, "data": dataset.to_dict()})


@data_bp.route('/datasets/<dataset_id>/import', methods=['POST'])
def import_dataset_route(dataset_id):
    dataset = _get_owned_dataset(dataset_id)
    if not dataset:
        return jsonify({"success": False, "error": "Dataset not found"}), 404
    if not dataset.schema_map:
        return jsonify({"success": False, "error": "Confirm a column mapping before importing"}), 400

    from ..models.task import TaskManager, TaskStatus

    task_manager = TaskManager()
    task_id = task_manager.create_task(task_type="dataset_import", metadata={"dataset_id": str(dataset.id)})
    app_obj = current_app._get_current_object()
    dataset_id_val, schema_map, file_path, source_type = dataset.id, dataset.schema_map, dataset.file_path, dataset.source_type

    def _run():
        with app_obj.app_context():
            try:
                task_manager.update_task(task_id, status=TaskStatus.PROCESSING, progress=10, message="Reading file…")
                ds = db.session.get(Dataset, dataset_id_val)
                df = read_dataset_file(file_path, source_type)
                task_manager.update_task(task_id, progress=40, message=f"Importing {len(df)} rows…")
                count = import_dataset(ds, df, schema_map)
                task_manager.complete_task(task_id, result={"dataset_id": str(dataset_id_val), "imported": count})
            except Exception as e:
                logger.error(f"Dataset import failed for {dataset_id_val}: {e}")
                task_manager.fail_task(task_id, str(e))

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"success": True, "data": {"task_id": task_id}})


@data_bp.route('/datasets/<dataset_id>/segment', methods=['POST'])
def segment_dataset_route(dataset_id):
    dataset = _get_owned_dataset(dataset_id)
    if not dataset:
        return jsonify({"success": False, "error": "Dataset not found"}), 404
    if dataset.status not in ("imported", "segmented"):
        return jsonify({"success": False, "error": "Import this dataset before segmenting it"}), 400

    from ..models.task import TaskManager, TaskStatus

    task_manager = TaskManager()
    task_id = task_manager.create_task(task_type="dataset_segment", metadata={"dataset_id": str(dataset.id)})
    app_obj = current_app._get_current_object()
    dataset_id_val, user_id = dataset.id, g.current_user.id

    def _run():
        with app_obj.app_context():
            try:
                task_manager.update_task(task_id, status=TaskStatus.PROCESSING, progress=20, message="Clustering customers…")
                segments = segment_dataset(dataset_id_val, user_id)
                task_manager.update_task(task_id, progress=80, message=f"Naming {len(segments)} segments…")
                task_manager.complete_task(task_id, result={
                    "dataset_id": str(dataset_id_val),
                    "segments": [s.to_dict() for s in segments],
                })
            except Exception as e:
                logger.error(f"Segmentation failed for dataset {dataset_id_val}: {e}")
                task_manager.fail_task(task_id, str(e))

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"success": True, "data": {"task_id": task_id}})


# ---------------- Segments ----------------

@data_bp.route('/segments', methods=['GET'])
def list_segments():
    query = Segment.query.filter_by(user_id=g.current_user.id)
    dataset_id = request.args.get('dataset_id')
    if dataset_id:
        try:
            query = query.filter_by(dataset_id=uuidlib.UUID(dataset_id))
        except ValueError:
            return jsonify({"success": False, "error": "Invalid dataset_id"}), 400
    segments = query.order_by(Segment.created_at.desc()).all()
    return jsonify({"success": True, "data": [s.to_dict() for s in segments]})


@data_bp.route('/segments/<segment_id>', methods=['GET'])
def get_segment(segment_id):
    segment = _get_owned_segment(segment_id)
    if not segment:
        return jsonify({"success": False, "error": "Segment not found"}), 404
    return jsonify({"success": True, "data": segment.to_dict()})


@data_bp.route('/segments/<segment_id>', methods=['PUT'])
def update_segment(segment_id):
    segment = _get_owned_segment(segment_id)
    if not segment:
        return jsonify({"success": False, "error": "Segment not found"}), 404

    data = request.get_json(silent=True) or {}
    if 'name' in data and (data['name'] or '').strip():
        segment.name = data['name'].strip()
    if 'description' in data:
        segment.description = data['description'] or ''
    if 'status' in data:
        if data['status'] not in ('draft', 'approved'):
            return jsonify({"success": False, "error": "status must be 'draft' or 'approved'"}), 400
        segment.status = data['status']
    db.session.commit()
    return jsonify({"success": True, "data": segment.to_dict()})


@data_bp.route('/segments/merge', methods=['POST'])
def merge_segments():
    data = request.get_json(silent=True) or {}
    segment_ids = data.get('segment_ids') or []
    if not isinstance(segment_ids, list) or len(segment_ids) < 2:
        return jsonify({"success": False, "error": "segment_ids must include at least 2 segments"}), 400

    segments = []
    for sid in segment_ids:
        segment = _get_owned_segment(sid)
        if not segment:
            return jsonify({"success": False, "error": f"Segment {sid} not found"}), 404
        segments.append(segment)
    if len({s.dataset_id for s in segments}) > 1:
        return jsonify({"success": False, "error": "Cannot merge segments from different datasets"}), 400

    from ..services.segmentation_engine import cluster_stats

    members = Customer.query.filter(Customer.segment_id.in_([s.id for s in segments])).all()
    merged = Segment(
        user_id=g.current_user.id,
        dataset_id=segments[0].dataset_id,
        name=(data.get('name') or " + ".join(s.name for s in segments))[:255],
        description=data.get('description') or "Merged segment.",
        method="manual",
        definition={"merged_from": [str(s.id) for s in segments]},
        size=len(members),
        stats=cluster_stats(members),
        status="draft",
    )
    db.session.add(merged)
    db.session.flush()
    for customer in members:
        customer.segment_id = merged.id
    for segment in segments:
        db.session.delete(segment)
    db.session.commit()
    return jsonify({"success": True, "data": merged.to_dict()}), 201


@data_bp.route('/segments/<segment_id>/export', methods=['GET'])
def export_segment(segment_id):
    segment = _get_owned_segment(segment_id)
    if not segment:
        return jsonify({"success": False, "error": "Segment not found"}), 404

    members = Customer.query.filter_by(segment_id=segment.id).all()
    fieldnames = ["external_id"] + sorted({k for c in members for k in (c.attributes or {}).keys()})
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for c in members:
        row = {"external_id": c.external_id, **(c.attributes or {})}
        writer.writerow({k: row.get(k, "") for k in fieldnames})

    mem = io.BytesIO(buffer.getvalue().encode("utf-8"))
    filename = f"segment_{segment.name.replace(' ', '_')}.csv"
    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name=filename)


# ---------------- Segment-grounded persona synthesis ----------------
# Registered on simulation_bp (not data_bp) to match the existing
# /api/simulation/* persona endpoints this complements.

from . import simulation_bp  # noqa: E402


def _profile_from_reddit_dict(d):
    from ..services.oasis_profile_generator import OasisAgentProfile
    return OasisAgentProfile(
        user_id=d.get("user_id", 0),
        user_name=d.get("username", f"user_{d.get('user_id', 0)}"),
        name=d.get("name", "Unknown"),
        bio=d.get("bio", ""),
        persona=d.get("persona", ""),
        karma=d.get("karma", 1000),
        age=d.get("age"),
        gender=d.get("gender"),
        mbti=d.get("mbti"),
        country=d.get("country"),
        profession=d.get("profession"),
        interested_topics=d.get("interested_topics", []),
    )


@simulation_bp.route('/personas/from-segments', methods=['POST'])
def generate_personas_from_segments():
    """Synthesise personas grounded in approved real-data segments and save
    them into an existing simulation's persona files (alongside or in place
    of its KG-derived audience — see `mode`).

    Request body:
    {
        "simulation_id": "sim_xxxx",     // parent simulation (has run /prepare)
        "brand_brief_id": "...",         // for KG grounding + Persona DB rows
        "segment_ids": ["...", "..."],   // must all be status='approved'
        "total_n": 40,                   // personas to generate, split proportionally by segment size
        "mode": "hybrid"                 // "hybrid" (append to existing) | "segments" (replace audience, keep brand agent)
    }
    """
    from ..models.orm import BrandBrief, Persona, SimulationRecord
    from ..services.oasis_profile_generator import OasisProfileGenerator
    from ..services.simulation_manager import SimulationManager

    data = request.get_json(silent=True) or {}
    simulation_id = data.get("simulation_id")
    brand_brief_id = data.get("brand_brief_id")
    segment_ids = data.get("segment_ids") or []
    total_n = int(data.get("total_n") or 0)
    mode = data.get("mode") or "hybrid"

    if not simulation_id:
        return jsonify({"success": False, "error": "simulation_id is required"}), 400
    if not segment_ids:
        return jsonify({"success": False, "error": "segment_ids is required"}), 400
    if total_n < 1:
        return jsonify({"success": False, "error": "total_n must be at least 1"}), 400
    if mode not in ("hybrid", "segments"):
        return jsonify({"success": False, "error": "mode must be 'hybrid' or 'segments'"}), 400

    sim_record = SimulationRecord.query.filter_by(sim_key=simulation_id, user_id=g.current_user.id).first()
    if not sim_record:
        return jsonify({"success": False, "error": "Simulation not found"}), 404

    brief = None
    if brand_brief_id:
        try:
            brief = BrandBrief.query.filter_by(id=uuidlib.UUID(str(brand_brief_id)), user_id=g.current_user.id).first()
        except ValueError:
            brief = None
    elif sim_record.brand_brief_id:
        brief = BrandBrief.query.filter_by(id=sim_record.brand_brief_id, user_id=g.current_user.id).first()

    segments = []
    for sid in segment_ids:
        segment = _get_owned_segment(sid)
        if not segment:
            return jsonify({"success": False, "error": f"Segment {sid} not found"}), 404
        if segment.status != "approved":
            return jsonify({"success": False, "error": f"Segment '{segment.name}' is not approved yet"}), 400
        segments.append(segment)

    total_size = sum(s.size for s in segments) or 1
    counts = {}
    for segment in segments:
        counts[str(segment.id)] = round(total_n * segment.size / total_size)
    # Rounding can drift the sum away from total_n — correct it on the largest segment.
    drift = total_n - sum(counts.values())
    if drift and segments:
        largest = max(segments, key=lambda s: s.size)
        counts[str(largest.id)] = max(0, counts[str(largest.id)] + drift)

    manager = SimulationManager()
    try:
        existing_profiles = manager.get_profiles(simulation_id, platform="reddit")
    except Exception:
        existing_profiles = []

    brand_profile = next((p for p in existing_profiles if str(p.get("user_id")) == "0"), None)
    kept_dicts = []
    if mode == "hybrid":
        kept_dicts = existing_profiles
        max_existing_id = max([p.get("user_id", 0) for p in existing_profiles], default=0)
        start_user_id = max_existing_id + 1
    else:  # "segments": keep only the brand agent, replace the rest
        kept_dicts = [brand_profile] if brand_profile else []
        start_user_id = max(1, (brand_profile.get("user_id", 0) if brand_profile else 0) + 1)

    generator = OasisProfileGenerator(business_type=brief.business_type if brief else None, graph_id=brief.graph_id if brief else None)
    new_profiles = generator.generate_profiles_from_segments(segments, counts, start_user_id=start_user_id)

    kept_profiles = [_profile_from_reddit_dict(d) for d in kept_dicts if d]
    all_profiles = kept_profiles + new_profiles

    sim_dir = manager._get_simulation_dir(simulation_id)
    generator.save_profiles(all_profiles, os.path.join(sim_dir, "reddit_profiles.json"), platform="reddit")
    generator.save_profiles(all_profiles, os.path.join(sim_dir, "twitter_profiles.csv"), platform="twitter")

    if brief:
        for segment in segments:
            seg_id = str(segment.id)
            for profile in new_profiles:
                if profile.source_entity_uuid != seg_id:
                    continue
                db.session.add(Persona(
                    user_id=g.current_user.id,
                    brand_brief_id=brief.id,
                    external_id=str(profile.user_id),
                    segment=segment.name,
                    segment_id=segment.id,
                    source="segment",
                    data=profile.to_reddit_format(),
                ))
        db.session.commit()

    return jsonify({
        "success": True,
        "data": {
            "simulation_id": simulation_id,
            "mode": mode,
            "generated": len(new_profiles),
            "total_profiles": len(all_profiles),
            "counts_by_segment": counts,
        },
    })
