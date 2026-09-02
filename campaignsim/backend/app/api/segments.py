"""Audience segment assignment API routes.

Split from the former monolithic simulation.py (Phase 0 restructure). Behavior
is unchanged; routes still live under /api/simulation via the shared
simulation_bp blueprint."""

import traceback
from flask import request, jsonify

from . import simulation_bp
from ..services.simulation_runner import SimulationRunner
from ..utils.logger import get_logger
from ..utils.locale import t

logger = get_logger('campaignsim.api.segments')

@simulation_bp.route('/assign_segments', methods=['POST'])
def assign_segments():
    """Assign generated personas to named audience segments.

    Reads twitter_profiles.csv from the simulation directory, classifies
    each individual persona profile into the provided segments using LLM,
    and saves a filtered CSV per segment back to the simulation directory.

    Request body:
    {
        "simulation_id": "sim_xxxx",
        "segments": [
            {"name": "MillennialProfessionals", "description": "Age 28-38, urban, high income"},
            {"name": "GenZConsumers", "description": "Age 18-26, digital natives, price-conscious"}
        ]
    }

    Response:
    {
        "success": true,
        "data": {
            "segments": {
                "MillennialProfessionals": 12,
                "GenZConsumers": 8,
                "Unassigned": 3
            },
            "profile_paths": {
                "MillennialProfessionals": "/path/to/profiles_MillennialProfessionals.csv"
            }
        }
    }
    """
    import csv as csv_module
    from ..services.oasis_profile_generator import OasisProfileGenerator

    try:
        data = request.get_json() or {}
        simulation_id = data.get("simulation_id")
        segments_input = data.get("segments", [])

        if not simulation_id:
            return jsonify({"success": False, "error": t("api.requireSimulationId")}), 400
        if not segments_input:
            return jsonify({"success": False, "error": "segments list is required"}), 400

        sim_dir = os.path.join(SimulationRunner.RUN_STATE_DIR, simulation_id)
        profiles_csv = os.path.join(sim_dir, "twitter_profiles.csv")

        if not os.path.exists(profiles_csv):
            return jsonify({
                "success": False,
                "error": f"twitter_profiles.csv not found for simulation {simulation_id}"
            }), 400

        # Read profiles as lightweight dicts (avoid re-running LLM generation)
        with open(profiles_csv, "r", encoding="utf-8", newline="") as f:
            reader = csv_module.DictReader(f)
            rows = list(reader)
            fieldnames = reader.fieldnames or list(rows[0].keys()) if rows else []

        # Separate brand agent (user_id == 0) from personas
        brand_rows = [r for r in rows if str(r.get("user_id", "")) == "0"]
        persona_rows = [r for r in rows if str(r.get("user_id", "")) != "0"]

        if not persona_rows:
            return jsonify({"success": False, "error": "No persona profiles found (only brand agent)"}), 400

        # Use OasisProfileGenerator for LLM-based classification
        # We pass lightweight wrappers so assign_segments can access .name, .age, etc.
        class _ProfileProxy:
            def __init__(self, row):
                self.name = row.get("name", "")
                self.age = row.get("age", "")
                self.profession = row.get("profession", "")
                self.bio = row.get("bio", "")
                self.interested_topics = row.get("interested_topics", "")
                self._row = row

        proxies = [_ProfileProxy(r) for r in persona_rows]

        generator = OasisProfileGenerator()
        segment_map = generator.assign_segments(proxies, segments_input)

        # Save per-segment CSV files and collect counts
        counts = {}
        profile_paths = {}
        for seg_name, seg_profiles in segment_map.items():
            counts[seg_name] = len(seg_profiles)
            if not seg_profiles:
                continue
            seg_rows = brand_rows + [p._row for p in seg_profiles]
            seg_filename = f"profiles_{seg_name.replace(' ', '_')}.csv"
            seg_path = os.path.join(sim_dir, seg_filename)
            with open(seg_path, "w", encoding="utf-8", newline="") as f:
                writer = csv_module.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(seg_rows)
            profile_paths[seg_name] = seg_path
            logger.info(f"Saved segment '{seg_name}': {len(seg_profiles)} personas -> {seg_path}")

        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "segments": counts,
                "profile_paths": profile_paths,
            }
        })

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

    except Exception as e:
        logger.error(f"assign_segments failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Phase 4 — Recommendation Engine ==============

