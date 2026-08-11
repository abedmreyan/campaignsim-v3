"""Shared private helpers used across the simulation API blueprints.

Extracted from the former monolithic app/api/simulation.py during the
Phase 0 blueprint split — behavior is unchanged from the original file.
"""

import json
import os

from ..utils.logger import get_logger

logger = get_logger('campaignsim.api.simulation')

# Interview prompt
# Agent
INTERVIEW_PROMPT_PREFIX = ""

def optimize_interview_prompt(prompt: str) -> str:
    """    InterviewAgent
    
    Args:
        prompt: 
        
    Returns:"""
    if not prompt:
        return prompt
    if prompt.startswith(INTERVIEW_PROMPT_PREFIX):
        return prompt
    return f"{INTERVIEW_PROMPT_PREFIX}{prompt}"



def _check_simulation_prepared(simulation_id: str) -> tuple:
    """    1. state.json  status  "ready"
    2. reddit_profiles.json, twitter_profiles.csv, simulation_config.json
    
    (run_*.py) backend/scripts/ 
    
    Args:
        simulation_id: ID
        
    Returns:
        (is_prepared: bool, info: dict)"""
    import os
    from ..config import Config
    
    simulation_dir = os.path.join(Config.OASIS_SIMULATION_DATA_DIR, simulation_id)
    
    if not os.path.exists(simulation_dir):
        return False, {"reason": ""}
    
    #  backend/scripts/
    required_files = [
        "state.json",
        "simulation_config.json",
        "reddit_profiles.json",
        "twitter_profiles.csv"
    ]
    
    existing_files = []
    missing_files = []
    for f in required_files:
        file_path = os.path.join(simulation_dir, f)
        if os.path.exists(file_path):
            existing_files.append(f)
        else:
            missing_files.append(f)
    
    if missing_files:
        return False, {
            "reason": "",
            "missing_files": missing_files,
            "existing_files": existing_files
        }
    
    # state.json
    state_file = os.path.join(simulation_dir, "state.json")
    try:
        import json
        with open(state_file, 'r', encoding='utf-8') as f:
            state_data = json.load(f)
        
        status = state_data.get("status", "")
        config_generated = state_data.get("config_generated", False)
        
        logger.debug(f": {simulation_id}, status={status}, config_generated={config_generated}")
        
        #  config_generated=True
        # - ready:
        # - preparing:  config_generated=True
        # - running:
        # - completed:
        # - stopped:
        # - failed:
        prepared_statuses = ["ready", "preparing", "running", "completed", "stopped", "failed"]
        if status in prepared_statuses and config_generated:
            profiles_file = os.path.join(simulation_dir, "reddit_profiles.json")
            config_file = os.path.join(simulation_dir, "simulation_config.json")
            
            profiles_count = 0
            if os.path.exists(profiles_file):
                with open(profiles_file, 'r', encoding='utf-8') as f:
                    profiles_data = json.load(f)
                    profiles_count = len(profiles_data) if isinstance(profiles_data, list) else 0
            
            # preparingready
            if status == "preparing":
                try:
                    state_data["status"] = "ready"
                    from datetime import datetime
                    state_data["updated_at"] = datetime.now().isoformat()
                    with open(state_file, 'w', encoding='utf-8') as f:
                        json.dump(state_data, f, ensure_ascii=False, indent=2)
                    logger.info(f": {simulation_id} preparing -> ready")
                    status = "ready"
                except Exception as e:
                    logger.warning(f": {e}")
            
            logger.info(f" {simulation_id} : (status={status}, config_generated={config_generated})")
            return True, {
                "status": status,
                "entities_count": state_data.get("entities_count", 0),
                "profiles_count": profiles_count,
                "entity_types": state_data.get("entity_types", []),
                "config_generated": config_generated,
                "created_at": state_data.get("created_at"),
                "updated_at": state_data.get("updated_at"),
                "existing_files": existing_files
            }
        else:
            logger.warning(f" {simulation_id} : (status={status}, config_generated={config_generated})")
            return False, {
                "reason": f" after config_generatedfalse: status={status}, config_generated={config_generated}",
                "status": status,
                "config_generated": config_generated
            }
            
    except Exception as e:
        return False, {"reason": f": {str(e)}"}



def _get_report_id_for_simulation(simulation_id: str) -> str:
    """     simulation  report_id
    
     reports  simulation_id  report
     created_at 
    
    Args:
        simulation_id: ID
        
    Returns:
        report_id  None"""
    import json
    from datetime import datetime
    
    # reports backend/uploads/reports
    # __file__  app/api/simulation.py backend/
    reports_dir = os.path.join(os.path.dirname(__file__), '../../uploads/reports')
    if not os.path.exists(reports_dir):
        return None
    
    matching_reports = []
    
    try:
        for report_folder in os.listdir(reports_dir):
            report_path = os.path.join(reports_dir, report_folder)
            if not os.path.isdir(report_path):
                continue
            
            meta_file = os.path.join(report_path, "meta.json")
            if not os.path.exists(meta_file):
                continue
            
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                
                if meta.get("simulation_id") == simulation_id:
                    matching_reports.append({
                        "report_id": meta.get("report_id"),
                        "created_at": meta.get("created_at", ""),
                        "status": meta.get("status", "")
                    })
            except Exception:
                continue
        
        if not matching_reports:
            return None
        
        matching_reports.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return matching_reports[0].get("report_id")
        
    except Exception as e:
        logger.warning(f" simulation {simulation_id} report : {e}")
        return None



def _campaigns_dir() -> str:
    """Directory where campaign JSON files are persisted."""
    from ..config import Config
    d = os.path.join(Config.UPLOAD_FOLDER, "campaigns")
    os.makedirs(d, exist_ok=True)
    return d


def _save_campaign(campaign) -> None:
    path = os.path.join(_campaigns_dir(), f"{campaign.campaign_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(campaign.to_dict(), f, indent=2, ensure_ascii=False)


def _load_campaign(campaign_id: str):
    from ..models.campaign import Campaign
    path = os.path.join(_campaigns_dir(), f"{campaign_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return Campaign.from_dict(json.load(f))

