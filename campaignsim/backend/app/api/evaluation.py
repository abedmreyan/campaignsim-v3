"""Evaluation API — records expert predictions and compares against simulation rankings."""

import json
import os
from datetime import datetime

from flask import jsonify, request

from ..config import Config
from ..utils.logger import get_logger
from . import evaluation_bp

logger = get_logger('campaignsim.api.evaluation')


def _studies_dir() -> str:
    d = os.path.join(Config.UPLOAD_FOLDER, "evaluation_studies")
    os.makedirs(d, exist_ok=True)
    return d


def _study_path(study_id: str) -> str:
    return os.path.join(_studies_dir(), f"{study_id}.json")


def _load_study(study_id: str) -> dict:
    path = _study_path(study_id)
    if not os.path.exists(path):
        return {"study_id": study_id, "predictions": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_study(study: dict) -> None:
    with open(_study_path(study["study_id"]), "w", encoding="utf-8") as f:
        json.dump(study, f, indent=2, ensure_ascii=False)


@evaluation_bp.route('/record_prediction', methods=['POST'])
def record_expert_prediction():
    """
    Record a human expert's variant ranking prediction.

    Body:
    {
        "study_id": "pilot_study_1",
        "participant_id": "expert_A",
        "campaign_id": "<campaign_id>",
        "predicted_ranking": ["variant_id_1", "variant_id_2", "variant_id_3"]
    }
    """
    try:
        data = request.get_json(force=True) or {}
        study_id = data.get("study_id")
        participant_id = data.get("participant_id")
        campaign_id = data.get("campaign_id")
        predicted_ranking = data.get("predicted_ranking", [])

        if not study_id:
            return jsonify({"success": False, "error": "study_id is required"}), 400
        if not participant_id:
            return jsonify({"success": False, "error": "participant_id is required"}), 400
        if not campaign_id:
            return jsonify({"success": False, "error": "campaign_id is required"}), 400
        if not predicted_ranking:
            return jsonify({"success": False, "error": "predicted_ranking must be a non-empty list"}), 400

        study = _load_study(study_id)

        # Remove duplicate submission from same participant + campaign if exists
        study["predictions"] = [
            p for p in study["predictions"]
            if not (p["participant_id"] == participant_id and p["campaign_id"] == campaign_id)
        ]

        study["predictions"].append({
            "participant_id": participant_id,
            "campaign_id": campaign_id,
            "predicted_ranking": predicted_ranking,
            "recorded_at": datetime.utcnow().isoformat()
        })

        _save_study(study)
        logger.info(f"Recorded prediction: study={study_id} participant={participant_id} campaign={campaign_id}")

        return jsonify({"success": True, "data": {"study_id": study_id, "recorded": True}})

    except Exception as e:
        logger.error(f"record_expert_prediction failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@evaluation_bp.route('/compare_results/<study_id>', methods=['GET'])
def compare_study_results(study_id: str):
    """
    Compare human expert predictions against simulation rankings.

    For each prediction, look up the campaign's simulation ranking (from campaign_report)
    and compute top-1 and top-2 agreement rates.
    """
    try:
        study = _load_study(study_id)
        predictions = study.get("predictions", [])

        if not predictions:
            return jsonify({"success": True, "data": {
                "study_id": study_id,
                "total_predictions": 0,
                "message": "No predictions recorded yet."
            }})

        campaigns_dir = os.path.join(Config.UPLOAD_FOLDER, "campaigns")

        results = []
        top1_agreements = 0
        top2_agreements = 0
        total_with_report = 0

        for pred in predictions:
            campaign_id = pred["campaign_id"]
            predicted_ranking = pred["predicted_ranking"]
            campaign_path = os.path.join(campaigns_dir, f"{campaign_id}.json")

            if not os.path.exists(campaign_path):
                results.append({
                    "participant_id": pred["participant_id"],
                    "campaign_id": campaign_id,
                    "predicted_ranking": predicted_ranking,
                    "simulation_ranking": None,
                    "top1_match": None,
                    "top2_match": None,
                    "note": "Campaign report not found"
                })
                continue

            with open(campaign_path, "r", encoding="utf-8") as f:
                campaign_dict = json.load(f)

            report = campaign_dict.get("campaign_report")
            if not report:
                results.append({
                    "participant_id": pred["participant_id"],
                    "campaign_id": campaign_id,
                    "predicted_ranking": predicted_ranking,
                    "simulation_ranking": None,
                    "top1_match": None,
                    "top2_match": None,
                    "note": "Simulation report not generated yet"
                })
                continue

            scored = report.get("scored_variants", [])
            sim_ranking = [v.get("variant_id") for v in scored]
            sim_top = sim_ranking[0] if sim_ranking else None

            top1_match = bool(sim_top and predicted_ranking and predicted_ranking[0] == sim_top)
            top2_match = bool(sim_top and predicted_ranking and sim_top in predicted_ranking[:2])

            if top1_match:
                top1_agreements += 1
            if top2_match:
                top2_agreements += 1
            total_with_report += 1

            results.append({
                "participant_id": pred["participant_id"],
                "campaign_id": campaign_id,
                "predicted_ranking": predicted_ranking,
                "simulation_ranking": sim_ranking,
                "top1_match": top1_match,
                "top2_match": top2_match
            })

        top1_rate = round(top1_agreements / total_with_report, 3) if total_with_report else None
        top2_rate = round(top2_agreements / total_with_report, 3) if total_with_report else None

        return jsonify({"success": True, "data": {
            "study_id": study_id,
            "total_predictions": len(predictions),
            "predictions_with_report": total_with_report,
            "top1_agreement_rate": top1_rate,
            "top2_agreement_rate": top2_rate,
            "results": results
        }})

    except Exception as e:
        logger.error(f"compare_study_results failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
