"""Simulation API routes
Step2: Zep entity read/filter, OASIS simulation prep and run (fully automated)"""

import json
import os
import traceback
from flask import request, jsonify, send_file

from . import simulation_bp
from ..config import Config
from ..services.zep_entity_reader import ZepEntityReader
from ..services.oasis_profile_generator import OasisProfileGenerator
from ..services.simulation_manager import SimulationManager, SimulationStatus
from ..services.simulation_runner import SimulationRunner, RunnerStatus
from ..utils.logger import get_logger
from ..utils.locale import t, get_locale, set_locale
from ..models.project import ProjectManager

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

# ==============  ==============

@simulation_bp.route('/entities/<graph_id>', methods=['GET'])
def get_graph_entities(graph_id: str):
    """    LabelsEntity
    
    Query
        entity_types: 
        enrich: true"""
    try:
        if Config.KG_BACKEND == 'zep' and not Config.ZEP_API_KEY:
            return jsonify({
                "success": False,
                "error": t('api.zepApiKeyMissing')
            }), 500

        entity_types_str = request.args.get('entity_types', '')
        entity_types = [t.strip() for t in entity_types_str.split(',') if t.strip()] if entity_types_str else None
        enrich = request.args.get('enrich', 'true').lower() == 'true'
        
        logger.info(f"Getting graph entities: graph_id={graph_id}, entity_types={entity_types}, enrich={enrich}")
        
        reader = ZepEntityReader()
        result = reader.filter_defined_entities(
            graph_id=graph_id,
            defined_entity_types=entity_types,
            enrich_with_edges=enrich
        )
        
        return jsonify({
            "success": True,
            "data": result.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Failed to get graph entities: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@simulation_bp.route('/entities/<graph_id>/<entity_uuid>', methods=['GET'])
def get_entity_detail(graph_id: str, entity_uuid: str):
    """..."""
    try:
        if Config.KG_BACKEND == 'zep' and not Config.ZEP_API_KEY:
            return jsonify({
                "success": False,
                "error": t('api.zepApiKeyMissing')
            }), 500

        reader = ZepEntityReader()
        entity = reader.get_entity_with_context(graph_id, entity_uuid)
        
        if not entity:
            return jsonify({
                "success": False,
                "error": t('api.entityNotFound', id=entity_uuid)
            }), 404
        
        return jsonify({
            "success": True,
            "data": entity.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Failed to get entity details: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@simulation_bp.route('/entities/<graph_id>/by-type/<entity_type>', methods=['GET'])
def get_entities_by_type(graph_id: str, entity_type: str):
    """..."""
    try:
        if Config.KG_BACKEND == 'zep' and not Config.ZEP_API_KEY:
            return jsonify({
                "success": False,
                "error": t('api.zepApiKeyMissing')
            }), 500

        enrich = request.args.get('enrich', 'true').lower() == 'true'
        
        reader = ZepEntityReader()
        entities = reader.get_entities_by_type(
            graph_id=graph_id,
            entity_type=entity_type,
            enrich_with_edges=enrich
        )
        
        return jsonify({
            "success": True,
            "data": {
                "entity_type": entity_type,
                "count": len(entities),
                "entities": [e.to_dict() for e in entities]
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get entities: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

# ==============  ==============

@simulation_bp.route('/create', methods=['POST'])
def create_simulation():
    """    max_roundsLLM
    
    JSON
        {
            "project_id": "proj_xxxx",      // 
            "graph_id": "campaignsim_xxxx",    // project
            "enable_twitter": true,          // true
            "enable_reddit": true            // true
        }
    
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "project_id": "proj_xxxx",
                "graph_id": "campaignsim_xxxx",
                "status": "created",
                "enable_twitter": true,
                "enable_reddit": true,
                "created_at": "2025-12-01T10:00:00"
            }
        }"""
    try:
        data = request.get_json() or {}
        
        project_id = data.get('project_id')
        if not project_id:
            return jsonify({
                "success": False,
                "error": t('api.requireProjectId')
            }), 400
        
        project = ProjectManager.get_project(project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": t('api.projectNotFound', id=project_id)
            }), 404
        
        graph_id = data.get('graph_id') or project.graph_id
        if not graph_id:
            return jsonify({
                "success": False,
                "error": t('api.graphNotBuilt')
            }), 400
        
        manager = SimulationManager()
        state = manager.create_simulation(
            project_id=project_id,
            graph_id=graph_id,
            enable_twitter=data.get('enable_twitter', True),
            enable_reddit=data.get('enable_reddit', True),
        )
        
        return jsonify({
            "success": True,
            "data": state.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Failed to create simulation: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

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

@simulation_bp.route('/prepare', methods=['POST'])
def prepare_simulation():
    """    LLM
    
    task_id
     GET /api/simulation/prepare/status 
    
    - 
    - 
    - force_regenerate=true
    
    1. 
    2. Zep
    3. OASIS Agent Profile
    4. LLM
    5. 
    
    JSON
        {
            "simulation_id": "sim_xxxx",                   // ID
            "entity_types": ["Student", "PublicFigure"],  // 
            "use_llm_for_profiles": true,                 // LLM
            "parallel_profile_count": 5,                  // 5
            "force_regenerate": false                     // false
        }
    
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "task_id": "task_xxxx",           // 
                "status": "preparing|ready",
                "message": "|",
                "already_prepared": true|false    // 
            }
        }"""
    import threading
    import os
    from ..models.task import TaskManager, TaskStatus
    from ..config import Config
    
    try:
        data = request.get_json() or {}
        
        simulation_id = data.get('simulation_id')
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": t('api.requireSimulationId')
            }), 400
        
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)
        
        if not state:
            return jsonify({
                "success": False,
                "error": t('api.simulationNotFound', id=simulation_id)
            }), 404
        
        force_regenerate = data.get('force_regenerate', False)
        logger.info(f" /prepare Request: simulation_id={simulation_id}, force_regenerate={force_regenerate}")
        
        if not force_regenerate:
            logger.debug(f" {simulation_id} ...")
            is_prepared, prepare_info = _check_simulation_prepared(simulation_id)
            logger.debug(f": is_prepared={is_prepared}, prepare_info={prepare_info}")
            if is_prepared:
                logger.info(f" {simulation_id} ")
                return jsonify({
                    "success": True,
                    "data": {
                        "simulation_id": simulation_id,
                        "status": "ready",
                        "message": t('api.alreadyPrepared'),
                        "already_prepared": True,
                        "prepare_info": prepare_info
                    }
                })
            else:
                logger.info(f" {simulation_id} ")
        
        project = ProjectManager.get_project(state.project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": t('api.projectNotFound', id=state.project_id)
            }), 404
        
        simulation_requirement = project.simulation_requirement or ""
        if not simulation_requirement:
            return jsonify({
                "success": False,
                "error": t('api.projectMissingRequirement')
            }), 400
        
        document_text = ProjectManager.get_extracted_text(state.project_id) or ""
        
        entity_types_list = data.get('entity_types')
        use_llm_for_profiles = data.get('use_llm_for_profiles', True)
        parallel_profile_count = data.get('parallel_profile_count', 5)
        
        # ==========  ==========
        # prepareAgent
        try:
            logger.info(f": graph_id={state.graph_id}")
            reader = ZepEntityReader()
            filtered_preview = reader.filter_defined_entities(
                graph_id=state.graph_id,
                defined_entity_types=entity_types_list,
                enrich_with_edges=False
            )
            state.entities_count = filtered_preview.filtered_count
            state.entity_types = list(filtered_preview.entity_types)
            logger.info(f": {filtered_preview.filtered_count}, type: {filtered_preview.entity_types}")
        except Exception as e:
            logger.warning(f" after : {e}")
        task_manager = TaskManager()
        task_id = task_manager.create_task(
            task_type="simulation_prepare",
            metadata={
                "simulation_id": simulation_id,
                "project_id": state.project_id
            }
        )
        
        state.status = SimulationStatus.PREPARING
        manager._save_simulation_state(state)
        
        # Capture locale before spawning background thread
        current_locale = get_locale()

        def run_prepare():
            set_locale(current_locale)
            try:
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.PROCESSING,
                    progress=0,
                    message=t('progress.startPreparingEnv')
                )
                
                stage_details = {}
                
                def progress_callback(stage, progress, message, **kwargs):
                    stage_weights = {
                        "reading": (0, 20),           # 0-20%
                        "generating_profiles": (20, 70),  # 20-70%
                        "generating_config": (70, 90),    # 70-90%
                        "copying_scripts": (90, 100)       # 90-100%
                    }
                    
                    start, end = stage_weights.get(stage, (0, 100))
                    current_progress = int(start + (end - start) * progress / 100)
                    
                    stage_names = {
                        "reading": t('progress.readingGraphEntities'),
                        "generating_profiles": t('progress.generatingProfiles'),
                        "generating_config": t('progress.generatingSimConfig'),
                        "copying_scripts": t('progress.preparingScripts')
                    }
                    
                    stage_index = list(stage_weights.keys()).index(stage) + 1 if stage in stage_weights else 1
                    total_stages = len(stage_weights)
                    
                    stage_details[stage] = {
                        "stage_name": stage_names.get(stage, stage),
                        "stage_progress": progress,
                        "current": kwargs.get("current", 0),
                        "total": kwargs.get("total", 0),
                        "item_name": kwargs.get("item_name", "")
                    }
                    
                    detail = stage_details[stage]
                    progress_detail_data = {
                        "current_stage": stage,
                        "current_stage_name": stage_names.get(stage, stage),
                        "stage_index": stage_index,
                        "total_stages": total_stages,
                        "stage_progress": progress,
                        "current_item": detail["current"],
                        "total_items": detail["total"],
                        "item_description": message
                    }
                    
                    if detail["total"] > 0:
                        detailed_message = (
                            f"[{stage_index}/{total_stages}] {stage_names.get(stage, stage)}: "
                            f"{detail['current']}/{detail['total']} - {message}"
                        )
                    else:
                        detailed_message = f"[{stage_index}/{total_stages}] {stage_names.get(stage, stage)}: {message}"
                    
                    task_manager.update_task(
                        task_id,
                        progress=current_progress,
                        message=detailed_message,
                        progress_detail=progress_detail_data
                    )
                
                result_state = manager.prepare_simulation(
                    simulation_id=simulation_id,
                    simulation_requirement=simulation_requirement,
                    document_text=document_text,
                    defined_entity_types=entity_types_list,
                    use_llm_for_profiles=use_llm_for_profiles,
                    progress_callback=progress_callback,
                    parallel_profile_count=parallel_profile_count
                )
                
                task_manager.complete_task(
                    task_id,
                    result=result_state.to_simple_dict()
                )
                
            except Exception as e:
                logger.error(f": {str(e)}")
                task_manager.fail_task(task_id, str(e))
                
                state = manager.get_simulation(simulation_id)
                if state:
                    state.status = SimulationStatus.FAILED
                    state.error = str(e)
                    manager._save_simulation_state(state)
        
        thread = threading.Thread(target=run_prepare, daemon=True)
        thread.start()
        
        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "task_id": task_id,
                "status": "preparing",
                "message": t('api.prepareStarted'),
                "already_prepared": False,
                "expected_entities_count": state.entities_count,  # Agent
                "entity_types": state.entity_types
            }
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 404
        
    except Exception as e:
        logger.error(f"Failed to start preparation task: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@simulation_bp.route('/prepare/status', methods=['POST'])
def get_prepare_status():
    """    1. task_id
    2. simulation_id
    
    JSON
        {
            "task_id": "task_xxxx",          // preparetask_id
            "simulation_id": "sim_xxxx"      // ID
        }
    
        {
            "success": true,
            "data": {
                "task_id": "task_xxxx",
                "status": "processing|completed|ready",
                "progress": 45,
                "message": "...",
                "already_prepared": true|false,  // 
                "prepare_info": {...}            // 
            }
        }"""
    from ..models.task import TaskManager
    
    try:
        data = request.get_json() or {}
        
        task_id = data.get('task_id')
        simulation_id = data.get('simulation_id')
        
        # simulation_id
        if simulation_id:
            is_prepared, prepare_info = _check_simulation_prepared(simulation_id)
            if is_prepared:
                return jsonify({
                    "success": True,
                    "data": {
                        "simulation_id": simulation_id,
                        "status": "ready",
                        "progress": 100,
                        "message": t('api.alreadyPrepared'),
                        "already_prepared": True,
                        "prepare_info": prepare_info
                    }
                })
        
        # task_id
        if not task_id:
            if simulation_id:
                # simulation_id
                return jsonify({
                    "success": True,
                    "data": {
                        "simulation_id": simulation_id,
                        "status": "not_started",
                        "progress": 0,
                        "message": t('api.notStartedPrepare'),
                        "already_prepared": False
                    }
                })
            return jsonify({
                "success": False,
                "error": t('api.requireTaskOrSimId')
            }), 400
        
        task_manager = TaskManager()
        task = task_manager.get_task(task_id)
        
        if not task:
            # simulation_id
            if simulation_id:
                is_prepared, prepare_info = _check_simulation_prepared(simulation_id)
                if is_prepared:
                    return jsonify({
                        "success": True,
                        "data": {
                            "simulation_id": simulation_id,
                            "task_id": task_id,
                            "status": "ready",
                            "progress": 100,
                            "message": t('api.taskCompletedPrepared'),
                            "already_prepared": True,
                            "prepare_info": prepare_info
                        }
                    })
            
            return jsonify({
                "success": False,
                "error": t('api.taskNotFound', id=task_id)
            }), 404
        
        task_dict = task.to_dict()
        task_dict["already_prepared"] = False
        
        return jsonify({
            "success": True,
            "data": task_dict
        })
        
    except Exception as e:
        logger.error(f"Failed to query task status: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@simulation_bp.route('/<simulation_id>', methods=['GET'])
def get_simulation(simulation_id: str):
    """..."""
    try:
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)
        
        if not state:
            return jsonify({
                "success": False,
                "error": t('api.simulationNotFound', id=simulation_id)
            }), 404
        
        result = state.to_dict()
        
        if state.status == SimulationStatus.READY:
            result["run_instructions"] = manager.get_run_instructions(simulation_id)
        
        return jsonify({
            "success": True,
            "data": result
        })
        
    except Exception as e:
        logger.error(f"Failed to get simulation status: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@simulation_bp.route('/list', methods=['GET'])
def list_simulations():
    """    Query
        project_id: ID"""
    try:
        project_id = request.args.get('project_id')
        
        manager = SimulationManager()
        simulations = manager.list_simulations(project_id=project_id)
        
        return jsonify({
            "success": True,
            "data": [s.to_dict() for s in simulations],
            "count": len(simulations)
        })
        
    except Exception as e:
        logger.error(f"Failed to list simulations: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

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

@simulation_bp.route('/history', methods=['GET'])
def get_simulation_history():
    """    Query
        limit: 20
    
        {
            "success": true,
            "data": [
                {
                    "simulation_id": "sim_xxxx",
                    "project_id": "proj_xxxx",
                    "project_name": "",
                    "simulation_requirement": "...",
                    "status": "completed",
                    "entities_count": 68,
                    "profiles_count": 68,
                    "entity_types": ["Student", "Professor", ...],
                    "created_at": "2024-12-10",
                    "updated_at": "2024-12-10",
                    "total_rounds": 120,
                    "current_round": 120,
                    "report_id": "report_xxxx",
                    "version": "v1.0.2"
                },
                ...
            ],
            "count": 7
        }"""
    try:
        limit = request.args.get('limit', 20, type=int)
        
        manager = SimulationManager()
        simulations = manager.list_simulations()[:limit]
        
        #  Simulation
        enriched_simulations = []
        for sim in simulations:
            sim_dict = sim.to_dict()
            
            #  simulation_config.json  simulation_requirement
            config = manager.get_simulation_config(sim.simulation_id)
            if config:
                sim_dict["simulation_requirement"] = config.get("simulation_requirement", "")
                time_config = config.get("time_config", {})
                sim_dict["total_simulation_hours"] = time_config.get("total_simulation_hours", 0)
                recommended_rounds = int(
                    time_config.get("total_simulation_hours", 0) * 60 / 
                    max(time_config.get("minutes_per_round", 60), 1)
                )
            else:
                sim_dict["simulation_requirement"] = ""
                sim_dict["total_simulation_hours"] = 0
                recommended_rounds = 0
            
            #  run_state.json
            run_state = SimulationRunner.get_run_state(sim.simulation_id)
            if run_state:
                sim_dict["current_round"] = run_state.current_round
                sim_dict["runner_status"] = run_state.runner_status.value
                #  total_rounds
                sim_dict["total_rounds"] = run_state.total_rounds if run_state.total_rounds > 0 else recommended_rounds
            else:
                sim_dict["current_round"] = 0
                sim_dict["runner_status"] = "idle"
                sim_dict["total_rounds"] = recommended_rounds
            
            # 3
            project = ProjectManager.get_project(sim.project_id)
            if project and hasattr(project, 'files') and project.files:
                sim_dict["files"] = [
                    {"filename": f.get("filename", "")} 
                    for f in project.files[:3]
                ]
            else:
                sim_dict["files"] = []
            
            #  report_id simulation  report
            sim_dict["report_id"] = _get_report_id_for_simulation(sim.simulation_id)
            
            sim_dict["version"] = "v1.0.2"
            
            try:
                created_date = sim_dict.get("created_at", "")[:10]
                sim_dict["created_date"] = created_date
            except:
                sim_dict["created_date"] = ""
            
            enriched_simulations.append(sim_dict)
        
        return jsonify({
            "success": True,
            "data": enriched_simulations,
            "count": len(enriched_simulations)
        })
        
    except Exception as e:
        logger.error(f": {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@simulation_bp.route('/<simulation_id>/profiles', methods=['GET'])
def get_simulation_profiles(simulation_id: str):
    """    Agent Profile
    
    Query
        platform: reddit/twitterreddit"""
    try:
        platform = request.args.get('platform', 'reddit')
        
        manager = SimulationManager()
        profiles = manager.get_profiles(simulation_id, platform=platform)
        
        return jsonify({
            "success": True,
            "data": {
                "platform": platform,
                "count": len(profiles),
                "profiles": profiles
            }
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 404
        
    except Exception as e:
        logger.error(f"Profile: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@simulation_bp.route('/<simulation_id>/profiles/realtime', methods=['GET'])
def get_simulation_profiles_realtime(simulation_id: str):
    """    Agent Profile
    
     /profiles 
    -  SimulationManager
    - 
    - 
    
    Query
        platform: reddit/twitterreddit
    
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "platform": "reddit",
                "count": 15,
                "total_expected": 93,  // 
                "is_generating": true,  // 
                "file_exists": true,
                "file_modified_at": "2025-12-04T18:20:00",
                "profiles": [...]
            }
        }"""
    import json
    import csv
    from datetime import datetime
    
    try:
        platform = request.args.get('platform', 'reddit')
        
        sim_dir = os.path.join(Config.OASIS_SIMULATION_DATA_DIR, simulation_id)
        
        if not os.path.exists(sim_dir):
            return jsonify({
                "success": False,
                "error": t('api.simulationNotFound', id=simulation_id)
            }), 404
        
        if platform == "reddit":
            profiles_file = os.path.join(sim_dir, "reddit_profiles.json")
        else:
            profiles_file = os.path.join(sim_dir, "twitter_profiles.csv")
        
        file_exists = os.path.exists(profiles_file)
        profiles = []
        file_modified_at = None
        
        if file_exists:
            file_stat = os.stat(profiles_file)
            file_modified_at = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            
            try:
                if platform == "reddit":
                    with open(profiles_file, 'r', encoding='utf-8') as f:
                        profiles = json.load(f)
                else:
                    with open(profiles_file, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        profiles = list(reader)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f" profiles after : {e}")
                profiles = []
        
        #  state.json
        is_generating = False
        total_expected = None
        
        state_file = os.path.join(sim_dir, "state.json")
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                    status = state_data.get("status", "")
                    is_generating = status == "preparing"
                    total_expected = state_data.get("entities_count")
            except Exception:
                pass
        
        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "platform": platform,
                "count": len(profiles),
                "total_expected": total_expected,
                "is_generating": is_generating,
                "file_exists": file_exists,
                "file_modified_at": file_modified_at,
                "profiles": profiles
            }
        })
        
    except Exception as e:
        logger.error(f"Profile: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@simulation_bp.route('/<simulation_id>/config/realtime', methods=['GET'])
def get_simulation_config_realtime(simulation_id: str):
    """     /config 
    -  SimulationManager
    - 
    - 
    - 
    
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "file_exists": true,
                "file_modified_at": "2025-12-04T18:20:00",
                "is_generating": true,  // 
                "generation_stage": "generating_config",  // 
                "config": {...}  // 
            }
        }"""
    import json
    from datetime import datetime
    
    try:
        sim_dir = os.path.join(Config.OASIS_SIMULATION_DATA_DIR, simulation_id)
        
        if not os.path.exists(sim_dir):
            return jsonify({
                "success": False,
                "error": t('api.simulationNotFound', id=simulation_id)
            }), 404
        
        config_file = os.path.join(sim_dir, "simulation_config.json")
        
        file_exists = os.path.exists(config_file)
        config = None
        file_modified_at = None
        
        if file_exists:
            file_stat = os.stat(config_file)
            file_modified_at = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f" config after : {e}")
                config = None
        
        #  state.json
        is_generating = False
        generation_stage = None
        config_generated = False
        
        state_file = os.path.join(sim_dir, "state.json")
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                    status = state_data.get("status", "")
                    is_generating = status == "preparing"
                    config_generated = state_data.get("config_generated", False)
                    
                    if is_generating:
                        if state_data.get("profiles_generated", False):
                            generation_stage = "generating_config"
                        else:
                            generation_stage = "generating_profiles"
                    elif status == "ready":
                        generation_stage = "completed"
            except Exception:
                pass
        
        response_data = {
            "simulation_id": simulation_id,
            "file_exists": file_exists,
            "file_modified_at": file_modified_at,
            "is_generating": is_generating,
            "generation_stage": generation_stage,
            "config_generated": config_generated,
            "config": config
        }
        
        if config:
            response_data["summary"] = {
                "total_agents": len(config.get("agent_configs", [])),
                "simulation_hours": config.get("time_config", {}).get("total_simulation_hours"),
                "initial_posts_count": len(config.get("event_config", {}).get("initial_posts", [])),
                "hot_topics_count": len(config.get("event_config", {}).get("hot_topics", [])),
                "has_twitter_config": "twitter_config" in config,
                "has_reddit_config": "reddit_config" in config,
                "generated_at": config.get("generated_at"),
                "llm_model": config.get("llm_model")
            }
        
        return jsonify({
            "success": True,
            "data": response_data
        })
        
    except Exception as e:
        logger.error(f"Config: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@simulation_bp.route('/<simulation_id>/config', methods=['GET'])
def get_simulation_config(simulation_id: str):
    """    LLM
    
        - time_config: /
        - agent_configs: Agent
        - event_config: 
        - platform_configs: 
        - generation_reasoning: LLM"""
    try:
        manager = SimulationManager()
        config = manager.get_simulation_config(simulation_id)
        
        if not config:
            return jsonify({
                "success": False,
                "error": t('api.configNotFound')
            }), 404
        
        return jsonify({
            "success": True,
            "data": config
        })
        
    except Exception as e:
        logger.error(f": {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@simulation_bp.route('/<simulation_id>/config/download', methods=['GET'])
def download_simulation_config(simulation_id: str):
    """..."""
    try:
        manager = SimulationManager()
        sim_dir = manager._get_simulation_dir(simulation_id)
        config_path = os.path.join(sim_dir, "simulation_config.json")
        
        if not os.path.exists(config_path):
            return jsonify({
                "success": False,
                "error": t('api.configFileNotFound')
            }), 404
        
        return send_file(
            config_path,
            as_attachment=True,
            download_name="simulation_config.json"
        )
        
    except Exception as e:
        logger.error(f": {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@simulation_bp.route('/script/<script_name>/download', methods=['GET'])
def download_simulation_script(script_name: str):
    """     backend/scripts/
    
    script_name
        - run_twitter_simulation.py
        - run_reddit_simulation.py
        - run_parallel_simulation.py
        - action_logger.py"""
    try:
        #  backend/scripts/
        scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../scripts'))
        
        allowed_scripts = [
            "run_twitter_simulation.py",
            "run_reddit_simulation.py", 
            "run_parallel_simulation.py",
            "action_logger.py"
        ]
        
        if script_name not in allowed_scripts:
            return jsonify({
                "success": False,
                "error": t('api.unknownScript', name=script_name, allowed=allowed_scripts)
            }), 400
        
        script_path = os.path.join(scripts_dir, script_name)
        
        if not os.path.exists(script_path):
            return jsonify({
                "success": False,
                "error": t('api.scriptFileNotFound', name=script_name)
            }), 404
        
        return send_file(
            script_path,
            as_attachment=True,
            download_name=script_name
        )
        
    except Exception as e:
        logger.error(f": {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

# ============== Profile ==============

@simulation_bp.route('/generate-profiles', methods=['POST'])
def generate_profiles():
    """Kick off async OASIS profile generation.

    Returns a task_id immediately. The caller should poll
    GET /api/simulation/generate-profiles/status?task_id=<task_id>
    until status == "completed" or "failed".

    JSON body:
        {
            "graph_id": "campaignsim_xxxx",
            "entity_types": ["Student"],   // optional filter
            "use_llm": true,
            "platform": "reddit"
        }
    """
    import threading
    from ..models.task import TaskManager, TaskStatus

    try:
        data = request.get_json() or {}

        graph_id = data.get('graph_id')
        if not graph_id:
            return jsonify({
                "success": False,
                "error": t('api.requireGraphId')
            }), 400

        simulation_id = data.get('simulation_id')

        # Default to only individual persona entity types so brands/channels are excluded
        entity_types = data.get('entity_types') or [
            "CustomerPersona", "Person", "Influencer", "Consumer",
            "Buyer", "User", "Shopper", "Subscriber", "Prospect"
        ]
        use_llm = data.get('use_llm', True)
        platform = data.get('platform', 'reddit')
        requested_count = data.get('count')  # None means "one per entity"
        if requested_count is not None:
            try:
                requested_count = int(requested_count)
            except (TypeError, ValueError):
                requested_count = None

        # Quick entity count check before spawning the thread
        reader = ZepEntityReader()
        filtered = reader.filter_defined_entities(
            graph_id=graph_id,
            defined_entity_types=entity_types,
            enrich_with_edges=True
        )

        if filtered.filtered_count == 0:
            return jsonify({
                "success": False,
                "error": t('api.noMatchingEntities')
            }), 400

        # Expand or sample the entity list to match the requested count.
        # If count > num_entities, cycle through entities to fill the target
        # (the LLM temperature variation will produce distinct outputs).
        # If count < num_entities, sample randomly.
        entities_to_use = list(filtered.entities)
        if requested_count and requested_count > 0:
            if requested_count > len(entities_to_use):
                expanded = []
                while len(expanded) < requested_count:
                    expanded.extend(entities_to_use)
                entities_to_use = expanded[:requested_count]
            elif requested_count < len(entities_to_use):
                import random as _random
                entities_to_use = _random.sample(entities_to_use, requested_count)

        target_count = len(entities_to_use)

        task_manager = TaskManager()
        task_id = task_manager.create_task(
            task_type="profile_generation",
            metadata={"graph_id": graph_id, "platform": platform, "target_count": target_count}
        )

        current_locale = get_locale()

        def run_generation():
            set_locale(current_locale)
            try:
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.PROCESSING,
                    progress=5,
                    message=f"Starting generation of {target_count} personas…"
                )

                total = target_count

                # Generator calls: progress_callback(current, total, message)
                def on_progress(current, total_arg, message=""):
                    pct = int(5 + (current / max(total, 1)) * 90)
                    task_manager.update_task(
                        task_id,
                        progress=pct,
                        message=f"Generated {current}/{total} personas"
                    )

                generator = OasisProfileGenerator()
                profiles = generator.generate_profiles_from_entities(
                    entities=entities_to_use,
                    use_llm=use_llm,
                    progress_callback=on_progress
                )

                if platform == "reddit":
                    profiles_data = [p.to_reddit_format() for p in profiles]
                elif platform == "twitter":
                    profiles_data = [p.to_twitter_format() for p in profiles]
                else:
                    profiles_data = [p.to_dict() for p in profiles]

                # Save profiles to disk so /profiles endpoint can serve them
                if simulation_id:
                    try:
                        from ..services.simulation_manager import SimulationManager
                        mgr = SimulationManager()
                        generator.save_profiles(
                            profiles=profiles,
                            file_path=os.path.join(
                                mgr._get_simulation_dir(simulation_id),
                                f"{platform}_profiles.json"
                            ),
                            platform=platform
                        )
                        logger.info(f"Saved {len(profiles)} profiles to disk for simulation {simulation_id}")
                    except Exception as save_err:
                        logger.warning(f"Could not save profiles to disk: {save_err}")

                task_manager.complete_task(task_id, result={
                    "platform": platform,
                    "entity_types": list(filtered.entity_types),
                    "count": len(profiles_data),
                    "profiles": profiles_data
                })

            except Exception as e:
                logger.error(f"Profile generation failed: {str(e)}")
                task_manager.fail_task(task_id, str(e))

        thread = threading.Thread(target=run_generation, daemon=True)
        thread.start()

        return jsonify({
            "success": True,
            "data": {
                "task_id": task_id,
                "status": "processing",
                "entity_count": filtered.filtered_count,
                "message": "Profile generation started"
            }
        })

    except Exception as e:
        logger.error(f"Failed to start profile generation: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/generate-profiles/status', methods=['GET'])
def get_generate_profiles_status():
    """Poll profile generation task status.

    Query params:
        task_id: the task_id returned by POST /generate-profiles
    """
    from ..models.task import TaskManager

    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({"success": False, "error": "task_id is required"}), 400

    task = TaskManager().get_task(task_id)
    if not task:
        return jsonify({"success": False, "error": t('api.taskNotFound', id=task_id)}), 404

    return jsonify({"success": True, "data": task.to_dict()})

# ==============  ==============

@simulation_bp.route('/start', methods=['POST'])
def start_simulation():
    """    JSON
        {
            "simulation_id": "sim_xxxx",          // ID
            "platform": "parallel",                // : twitter / reddit / parallel ()
            "max_rounds": 100,                     // : 
            "enable_graph_memory_update": false,   // : AgentZep
            "force": false                         // : 
        }

     force 
        - 
        - run_state.json, actions.jsonl, simulation.log 
        - simulation_config.json profile 
        - 

     enable_graph_memory_update
        - AgentZep
        - ""AI
        -  graph_id
        - API

        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "runner_status": "running",
                "process_pid": 12345,
                "twitter_running": true,
                "reddit_running": true,
                "started_at": "2025-12-01T10:00:00",
                "graph_memory_update_enabled": true,  // 
                "force_restarted": true               // 
            }
        }"""
    try:
        data = request.get_json() or {}

        simulation_id = data.get('simulation_id')
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": t('api.requireSimulationId')
            }), 400

        platform = data.get('platform', 'parallel')
        max_rounds = data.get('max_rounds')
        enable_graph_memory_update = data.get('enable_graph_memory_update', False)
        force = data.get('force', False)

        #  max_rounds
        if max_rounds is not None:
            try:
                max_rounds = int(max_rounds)
                if max_rounds <= 0:
                    return jsonify({
                        "success": False,
                        "error": t('api.maxRoundsPositive')
                    }), 400
            except (ValueError, TypeError):
                return jsonify({
                    "success": False,
                    "error": t('api.maxRoundsInvalid')
                }), 400

        if platform not in ['twitter', 'reddit', 'parallel']:
            return jsonify({
                "success": False,
                "error": t('api.invalidPlatform', platform=platform)
            }), 400

        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)

        if not state:
            return jsonify({
                "success": False,
                "error": t('api.simulationNotFound', id=simulation_id)
            }), 404

        force_restarted = False
        
        if state.status != SimulationStatus.READY:
            is_prepared, prepare_info = _check_simulation_prepared(simulation_id)

            if is_prepared:
                if state.status == SimulationStatus.RUNNING:
                    run_state = SimulationRunner.get_run_state(simulation_id)
                    if run_state and run_state.runner_status.value == "running":
                        if force:
                            logger.info(f" {simulation_id}")
                            try:
                                SimulationRunner.stop_simulation(simulation_id)
                            except Exception as e:
                                logger.warning(f": {str(e)}")
                        else:
                            return jsonify({
                                "success": False,
                                "error": t('api.simRunningForceHint')
                            }), 400

                if force:
                    logger.info(f" {simulation_id}")
                    cleanup_result = SimulationRunner.cleanup_simulation_logs(simulation_id)
                    if not cleanup_result.get("success"):
                        logger.warning(f": {cleanup_result.get('errors')}")
                    force_restarted = True

                #  ready
                logger.info(f" {simulation_id} ready: {state.status.value}")
                state.status = SimulationStatus.READY
                manager._save_simulation_state(state)
            else:
                return jsonify({
                    "success": False,
                    "error": t('api.simNotReady', status=state.status.value)
                }), 400
        
        # ID
        graph_id = None
        if enable_graph_memory_update:
            #  graph_id
            graph_id = state.graph_id
            if not graph_id:
                project = ProjectManager.get_project(state.project_id)
                if project:
                    graph_id = project.graph_id
            
            if not graph_id:
                return jsonify({
                    "success": False,
                    "error": t('api.graphIdRequiredForMemory')
                }), 400
            
            logger.info(f": simulation_id={simulation_id}, graph_id={graph_id}")
        
        run_state = SimulationRunner.start_simulation(
            simulation_id=simulation_id,
            platform=platform,
            max_rounds=max_rounds,
            enable_graph_memory_update=enable_graph_memory_update,
            graph_id=graph_id
        )
        
        state.status = SimulationStatus.RUNNING
        manager._save_simulation_state(state)
        
        response_data = run_state.to_dict()
        if max_rounds:
            response_data['max_rounds_applied'] = max_rounds
        response_data['graph_memory_update_enabled'] = enable_graph_memory_update
        response_data['force_restarted'] = force_restarted
        if enable_graph_memory_update:
            response_data['graph_id'] = graph_id
        
        return jsonify({
            "success": True,
            "data": response_data
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
        
    except Exception as e:
        logger.error(f": {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@simulation_bp.route('/stop', methods=['POST'])
def stop_simulation():
    """    JSON
        {
            "simulation_id": "sim_xxxx"  // ID
        }
    
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "runner_status": "stopped",
                "completed_at": "2025-12-01T12:00:00"
            }
        }"""
    try:
        data = request.get_json() or {}
        
        simulation_id = data.get('simulation_id')
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": t('api.requireSimulationId')
            }), 400
        
        run_state = SimulationRunner.stop_simulation(simulation_id)
        
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)
        if state:
            state.status = SimulationStatus.PAUSED
            manager._save_simulation_state(state)
        
        return jsonify({
            "success": True,
            "data": run_state.to_dict()
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
        
    except Exception as e:
        logger.error(f": {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

# ==============  ==============

@simulation_bp.route('/<simulation_id>/run-status', methods=['GET'])
def get_run_status(simulation_id: str):
    """        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "runner_status": "running",
                "current_round": 5,
                "total_rounds": 144,
                "progress_percent": 3.5,
                "simulated_hours": 2,
                "total_simulation_hours": 72,
                "twitter_running": true,
                "reddit_running": true,
                "twitter_actions_count": 150,
                "reddit_actions_count": 200,
                "total_actions_count": 350,
                "started_at": "2025-12-01T10:00:00",
                "updated_at": "2025-12-01T10:30:00"
            }
        }"""
    try:
        run_state = SimulationRunner.get_run_state(simulation_id)
        
        if not run_state:
            return jsonify({
                "success": True,
                "data": {
                    "simulation_id": simulation_id,
                    "runner_status": "idle",
                    "current_round": 0,
                    "total_rounds": 0,
                    "progress_percent": 0,
                    "twitter_actions_count": 0,
                    "reddit_actions_count": 0,
                    "total_actions_count": 0,
                }
            })
        
        return jsonify({
            "success": True,
            "data": run_state.to_dict()
        })
        
    except Exception as e:
        logger.error(f": {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@simulation_bp.route('/<simulation_id>/run-status/detail', methods=['GET'])
def get_run_status_detail(simulation_id: str):
    """    Query
        platform: twitter/reddit
    
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "runner_status": "running",
                "current_round": 5,
                ...
                "all_actions": [
                    {
                        "round_num": 5,
                        "timestamp": "2025-12-01T10:30:00",
                        "platform": "twitter",
                        "agent_id": 3,
                        "agent_name": "Agent Name",
                        "action_type": "CREATE_POST",
                        "action_args": {"content": "..."},
                        "result": null,
                        "success": true
                    },
                    ...
                ],
                "twitter_actions": [...],  # Twitter 
                "reddit_actions": [...]    # Reddit 
            }
        }"""
    try:
        run_state = SimulationRunner.get_run_state(simulation_id)
        platform_filter = request.args.get('platform')
        
        if not run_state:
            return jsonify({
                "success": True,
                "data": {
                    "simulation_id": simulation_id,
                    "runner_status": "idle",
                    "all_actions": [],
                    "twitter_actions": [],
                    "reddit_actions": []
                }
            })
        
        all_actions = SimulationRunner.get_all_actions(
            simulation_id=simulation_id,
            platform=platform_filter
        )
        
        twitter_actions = SimulationRunner.get_all_actions(
            simulation_id=simulation_id,
            platform="twitter"
        ) if not platform_filter or platform_filter == "twitter" else []
        
        reddit_actions = SimulationRunner.get_all_actions(
            simulation_id=simulation_id,
            platform="reddit"
        ) if not platform_filter or platform_filter == "reddit" else []
        
        # recent_actions
        current_round = run_state.current_round
        recent_actions = SimulationRunner.get_all_actions(
            simulation_id=simulation_id,
            platform=platform_filter,
            round_num=current_round
        ) if current_round > 0 else []
        
        result = run_state.to_dict()
        result["all_actions"] = [a.to_dict() for a in all_actions]
        result["twitter_actions"] = [a.to_dict() for a in twitter_actions]
        result["reddit_actions"] = [a.to_dict() for a in reddit_actions]
        result["rounds_count"] = len(run_state.rounds)
        # recent_actions
        result["recent_actions"] = [a.to_dict() for a in recent_actions]
        
        return jsonify({
            "success": True,
            "data": result
        })
        
    except Exception as e:
        logger.error(f": {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@simulation_bp.route('/<simulation_id>/actions', methods=['GET'])
def get_simulation_actions(simulation_id: str):
    """    Agent
    
    Query
        limit: 100
        offset: 0
        platform: twitter/reddit
        agent_id: Agent ID
        round_num: 
    
        {
            "success": true,
            "data": {
                "count": 100,
                "actions": [...]
            }
        }"""
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        platform = request.args.get('platform')
        agent_id = request.args.get('agent_id', type=int)
        round_num = request.args.get('round_num', type=int)
        
        actions = SimulationRunner.get_actions(
            simulation_id=simulation_id,
            limit=limit,
            offset=offset,
            platform=platform,
            agent_id=agent_id,
            round_num=round_num
        )
        
        return jsonify({
            "success": True,
            "data": {
                "count": len(actions),
                "actions": [a.to_dict() for a in actions]
            }
        })
        
    except Exception as e:
        logger.error(f": {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@simulation_bp.route('/<simulation_id>/timeline', methods=['GET'])
def get_simulation_timeline(simulation_id: str):
    """    Query
        start_round: 0
        end_round: """
    try:
        start_round = request.args.get('start_round', 0, type=int)
        end_round = request.args.get('end_round', type=int)
        
        timeline = SimulationRunner.get_timeline(
            simulation_id=simulation_id,
            start_round=start_round,
            end_round=end_round
        )
        
        return jsonify({
            "success": True,
            "data": {
                "rounds_count": len(timeline),
                "timeline": timeline
            }
        })
        
    except Exception as e:
        logger.error(f": {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@simulation_bp.route('/<simulation_id>/agent-stats', methods=['GET'])
def get_agent_stats(simulation_id: str):
    """    Agent
    
    Agent"""
    try:
        stats = SimulationRunner.get_agent_stats(simulation_id)
        
        return jsonify({
            "success": True,
            "data": {
                "agents_count": len(stats),
                "stats": stats
            }
        })
        
    except Exception as e:
        logger.error(f"Agent: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

# ==============  ==============

@simulation_bp.route('/<simulation_id>/posts', methods=['GET'])
def get_simulation_posts(simulation_id: str):
    """    Query
        platform: twitter/reddit
        limit: 50
        offset: 
    
    SQLite"""
    try:
        platform = request.args.get('platform', 'reddit')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        sim_dir = os.path.join(
            os.path.dirname(__file__),
            f'../../uploads/simulations/{simulation_id}'
        )
        
        db_file = f"{platform}_simulation.db"
        db_path = os.path.join(sim_dir, db_file)
        
        if not os.path.exists(db_path):
            return jsonify({
                "success": True,
                "data": {
                    "platform": platform,
                    "count": 0,
                    "posts": [],
                    "message": t('api.dbNotExist')
                }
            })
        
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM post 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            posts = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("SELECT COUNT(*) FROM post")
            total = cursor.fetchone()[0]
            
        except sqlite3.OperationalError:
            posts = []
            total = 0
        
        conn.close()
        
        return jsonify({
            "success": True,
            "data": {
                "platform": platform,
                "total": total,
                "count": len(posts),
                "posts": posts
            }
        })
        
    except Exception as e:
        logger.error(f": {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@simulation_bp.route('/<simulation_id>/comments', methods=['GET'])
def get_simulation_comments(simulation_id: str):
    """    Reddit
    
    Query
        post_id: ID
        limit: 
        offset: """
    try:
        post_id = request.args.get('post_id')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        sim_dir = os.path.join(
            os.path.dirname(__file__),
            f'../../uploads/simulations/{simulation_id}'
        )
        
        db_path = os.path.join(sim_dir, "reddit_simulation.db")
        
        if not os.path.exists(db_path):
            return jsonify({
                "success": True,
                "data": {
                    "count": 0,
                    "comments": []
                }
            })
        
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if post_id:
                cursor.execute("""
                    SELECT * FROM comment 
                    WHERE post_id = ?
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                """, (post_id, limit, offset))
            else:
                cursor.execute("""
                    SELECT * FROM comment 
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                """, (limit, offset))
            
            comments = [dict(row) for row in cursor.fetchall()]
            
        except sqlite3.OperationalError:
            comments = []
        
        conn.close()
        
        return jsonify({
            "success": True,
            "data": {
                "count": len(comments),
                "comments": comments
            }
        })
        
    except Exception as e:
        logger.error(f": {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

# ============== Interview  ==============

@simulation_bp.route('/interview', methods=['POST'])
def interview_agent():
    """    Agent

    JSON
        {
            "simulation_id": "sim_xxxx",       // ID
            "agent_id": 0,                     // Agent ID
            "prompt": "",  // 
            "platform": "twitter",             // twitter/reddit
                                               // 
            "timeout": 60                      // 60
        }

    platform
        {
            "success": true,
            "data": {
                "agent_id": 0,
                "prompt": "",
                "result": {
                    "agent_id": 0,
                    "prompt": "...",
                    "platforms": {
                        "twitter": {"agent_id": 0, "response": "...", "platform": "twitter"},
                        "reddit": {"agent_id": 0, "response": "...", "platform": "reddit"}
                    }
                },
                "timestamp": "2025-12-08T10:00:01"
            }
        }

    platform
        {
            "success": true,
            "data": {
                "agent_id": 0,
                "prompt": "",
                "result": {
                    "agent_id": 0,
                    "response": "...",
                    "platform": "twitter",
                    "timestamp": "2025-12-08T10:00:00"
                },
                "timestamp": "2025-12-08T10:00:01"
            }
        }"""
    try:
        data = request.get_json() or {}
        
        simulation_id = data.get('simulation_id')
        agent_id = data.get('agent_id')
        prompt = data.get('prompt')
        platform = data.get('platform')  # twitter/reddit/None
        timeout = data.get('timeout', 60)
        
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": t('api.requireSimulationId')
            }), 400
        
        if agent_id is None:
            return jsonify({
                "success": False,
                "error": t('api.requireAgentId')
            }), 400
        
        if not prompt:
            return jsonify({
                "success": False,
                "error": t('api.requirePrompt')
            }), 400
        
        # platform
        if platform and platform not in ("twitter", "reddit"):
            return jsonify({
                "success": False,
                "error": t('api.invalidInterviewPlatform')
            }), 400
        
        if not SimulationRunner.check_env_alive(simulation_id):
            return jsonify({
                "success": False,
                "error": t('api.envNotRunning')
            }), 400
        
        # promptAgent
        optimized_prompt = optimize_interview_prompt(prompt)
        
        result = SimulationRunner.interview_agent(
            simulation_id=simulation_id,
            agent_id=agent_id,
            prompt=optimized_prompt,
            platform=platform,
            timeout=timeout
        )

        return jsonify({
            "success": result.get("success", False),
            "data": result
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
        
    except TimeoutError as e:
        return jsonify({
            "success": False,
            "error": t('api.interviewTimeout', error=str(e))
        }), 504
        
    except Exception as e:
        logger.error(f"Interview failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@simulation_bp.route('/interview/batch', methods=['POST'])
def interview_agents_batch():
    """    Agent

    JSON
        {
            "simulation_id": "sim_xxxx",       // ID
            "interviews": [                    // 
                {
                    "agent_id": 0,
                    "prompt": "A",
                    "platform": "twitter"      // Agent
                },
                {
                    "agent_id": 1,
                    "prompt": "B"  // platform
                }
            ],
            "platform": "reddit",              // platform
                                               // Agent
            "timeout": 120                     // 120
        }

        {
            "success": true,
            "data": {
                "interviews_count": 2,
                "result": {
                    "interviews_count": 4,
                    "results": {
                        "twitter_0": {"agent_id": 0, "response": "...", "platform": "twitter"},
                        "reddit_0": {"agent_id": 0, "response": "...", "platform": "reddit"},
                        "twitter_1": {"agent_id": 1, "response": "...", "platform": "twitter"},
                        "reddit_1": {"agent_id": 1, "response": "...", "platform": "reddit"}
                    }
                },
                "timestamp": "2025-12-08T10:00:01"
            }
        }"""
    try:
        data = request.get_json() or {}

        simulation_id = data.get('simulation_id')
        interviews = data.get('interviews')
        platform = data.get('platform')  # twitter/reddit/None
        timeout = data.get('timeout', 120)

        if not simulation_id:
            return jsonify({
                "success": False,
                "error": t('api.requireSimulationId')
            }), 400

        if not interviews or not isinstance(interviews, list):
            return jsonify({
                "success": False,
                "error": t('api.requireInterviews')
            }), 400

        # platform
        if platform and platform not in ("twitter", "reddit"):
            return jsonify({
                "success": False,
                "error": t('api.invalidInterviewPlatform')
            }), 400

        for i, interview in enumerate(interviews):
            if 'agent_id' not in interview:
                return jsonify({
                    "success": False,
                    "error": t('api.interviewListMissingAgentId', index=i+1)
                }), 400
            if 'prompt' not in interview:
                return jsonify({
                    "success": False,
                    "error": t('api.interviewListMissingPrompt', index=i+1)
                }), 400
            # platform
            item_platform = interview.get('platform')
            if item_platform and item_platform not in ("twitter", "reddit"):
                return jsonify({
                    "success": False,
                    "error": t('api.interviewListInvalidPlatform', index=i+1)
                }), 400

        if not SimulationRunner.check_env_alive(simulation_id):
            return jsonify({
                "success": False,
                "error": t('api.envNotRunning')
            }), 400

        # promptAgent
        optimized_interviews = []
        for interview in interviews:
            optimized_interview = interview.copy()
            optimized_interview['prompt'] = optimize_interview_prompt(interview.get('prompt', ''))
            optimized_interviews.append(optimized_interview)

        result = SimulationRunner.interview_agents_batch(
            simulation_id=simulation_id,
            interviews=optimized_interviews,
            platform=platform,
            timeout=timeout
        )

        return jsonify({
            "success": result.get("success", False),
            "data": result
        })

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

    except TimeoutError as e:
        return jsonify({
            "success": False,
            "error": t('api.batchInterviewTimeout', error=str(e))
        }), 504

    except Exception as e:
        logger.error(f"Interview failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@simulation_bp.route('/interview/all', methods=['POST'])
def interview_all_agents():
    """     - Agent

    JSON
        {
            "simulation_id": "sim_xxxx",            // ID
            "prompt": "",  // Agent
            "platform": "reddit",                   // twitter/reddit
                                                    // Agent
            "timeout": 180                          // 180
        }

        {
            "success": true,
            "data": {
                "interviews_count": 50,
                "result": {
                    "interviews_count": 100,
                    "results": {
                        "twitter_0": {"agent_id": 0, "response": "...", "platform": "twitter"},
                        "reddit_0": {"agent_id": 0, "response": "...", "platform": "reddit"},
                        ...
                    }
                },
                "timestamp": "2025-12-08T10:00:01"
            }
        }"""
    try:
        data = request.get_json() or {}

        simulation_id = data.get('simulation_id')
        prompt = data.get('prompt')
        platform = data.get('platform')  # twitter/reddit/None
        timeout = data.get('timeout', 180)

        if not simulation_id:
            return jsonify({
                "success": False,
                "error": t('api.requireSimulationId')
            }), 400

        if not prompt:
            return jsonify({
                "success": False,
                "error": t('api.requirePrompt')
            }), 400

        # platform
        if platform and platform not in ("twitter", "reddit"):
            return jsonify({
                "success": False,
                "error": t('api.invalidInterviewPlatform')
            }), 400

        if not SimulationRunner.check_env_alive(simulation_id):
            return jsonify({
                "success": False,
                "error": t('api.envNotRunning')
            }), 400

        # promptAgent
        optimized_prompt = optimize_interview_prompt(prompt)

        result = SimulationRunner.interview_all_agents(
            simulation_id=simulation_id,
            prompt=optimized_prompt,
            platform=platform,
            timeout=timeout
        )

        return jsonify({
            "success": result.get("success", False),
            "data": result
        })

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

    except TimeoutError as e:
        return jsonify({
            "success": False,
            "error": t('api.globalInterviewTimeout', error=str(e))
        }), 504

    except Exception as e:
        logger.error(f"Interview failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@simulation_bp.route('/interview/history', methods=['POST'])
def get_interview_history():
    """    Interview

    Interview

    JSON
        {
            "simulation_id": "sim_xxxx",  // ID
            "platform": "reddit",          // reddit/twitter
                                           // 
            "agent_id": 0,                 // Agent
            "limit": 100                   // 100
        }

        {
            "success": true,
            "data": {
                "count": 10,
                "history": [
                    {
                        "agent_id": 0,
                        "response": "...",
                        "prompt": "",
                        "timestamp": "2025-12-08T10:00:00",
                        "platform": "reddit"
                    },
                    ...
                ]
            }
        }"""
    try:
        data = request.get_json() or {}
        
        simulation_id = data.get('simulation_id')
        platform = data.get('platform')
        agent_id = data.get('agent_id')
        limit = data.get('limit', 100)
        
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": t('api.requireSimulationId')
            }), 400

        history = SimulationRunner.get_interview_history(
            simulation_id=simulation_id,
            platform=platform,
            agent_id=agent_id,
            limit=limit
        )

        return jsonify({
            "success": True,
            "data": {
                "count": len(history),
                "history": history
            }
        })

    except Exception as e:
        logger.error(f"Interview: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@simulation_bp.route('/env-status', methods=['POST'])
def get_env_status():
    """    Interview

    JSON
        {
            "simulation_id": "sim_xxxx"  // ID
        }

        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "env_alive": true,
                "twitter_available": true,
                "reddit_available": true,
                "message": "Interview"
            }
        }"""
    try:
        data = request.get_json() or {}
        
        simulation_id = data.get('simulation_id')
        
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": t('api.requireSimulationId')
            }), 400

        env_alive = SimulationRunner.check_env_alive(simulation_id)
        
        env_status = SimulationRunner.get_env_status_detail(simulation_id)

        if env_alive:
            message = t('api.envRunning')
        else:
            message = t('api.envNotRunningShort')

        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "env_alive": env_alive,
                "twitter_available": env_status.get("twitter_available", False),
                "reddit_available": env_status.get("reddit_available", False),
                "message": message
            }
        })

    except Exception as e:
        logger.error(f": {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@simulation_bp.route('/close-env', methods=['POST'])
def close_simulation_env():
    """     /stop /stop 
    
    JSON
        {
            "simulation_id": "sim_xxxx",  // ID
            "timeout": 30                  // 30
        }
    
        {
            "success": true,
            "data": {
                "message": "",
                "result": {...},
                "timestamp": "2025-12-08T10:00:01"
            }
        }"""
    try:
        data = request.get_json() or {}
        
        simulation_id = data.get('simulation_id')
        timeout = data.get('timeout', 30)
        
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": t('api.requireSimulationId')
            }), 400
        
        result = SimulationRunner.close_simulation_env(
            simulation_id=simulation_id,
            timeout=timeout
        )
        
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)
        if state:
            state.status = SimulationStatus.COMPLETED
            manager._save_simulation_state(state)
        
        return jsonify({
            "success": result.get("success", False),
            "data": result
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
        
    except Exception as e:
        logger.error(f": {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Phase 2 — Channel Variant Simulation ==============

@simulation_bp.route('/launch_variant', methods=['POST'])
def launch_variant():
    """Launch a single channel variant simulation.

    Creates a variant-specific simulation directory, writes the config,
    copies the persona profiles CSV, and starts the channel simulation
    subprocess via SimulationRunner.

    Request body:
    {
        "simulation_id": "...",       // parent simulation ID (used to locate profiles)
        "variant_id": "variant_0",    // unique ID for this variant run
        "channel": "instagram",       // instagram | email | tiktok | linkedin
        "campaign_content": "...",    // full campaign text with channel framing
        "num_rounds": 10              // simulation rounds (default 10)
    }

    Response:
    {
        "success": true,
        "data": {
            "variant_sim_id": "...",
            "simulation_dir": "..."
        }
    }
    """
    import shutil

    try:
        data = request.get_json() or {}

        simulation_id = data.get("simulation_id")
        if not simulation_id:
            return jsonify({"success": False, "error": t("api.requireSimulationId")}), 400

        variant_id = data.get("variant_id", "variant_0")
        channel = data.get("channel", "instagram")
        campaign_content = data.get("campaign_content", "")
        num_rounds = int(data.get("num_rounds", 10))

        if not campaign_content:
            return jsonify({"success": False, "error": "campaign_content is required"}), 400

        # Locate parent simulation dir (contains twitter_profiles.csv)
        parent_sim_dir = os.path.join(SimulationRunner.RUN_STATE_DIR, simulation_id)
        profiles_src = os.path.join(parent_sim_dir, "twitter_profiles.csv")
        if not os.path.exists(profiles_src):
            return jsonify({
                "success": False,
                "error": (
                    f"twitter_profiles.csv not found in simulation {simulation_id}. "
                    "Run /prepare first to generate persona profiles."
                )
            }), 400

        # Create variant simulation directory
        variant_sim_id = f"{simulation_id}__{variant_id}"
        variant_sim_dir = os.path.join(SimulationRunner.RUN_STATE_DIR, variant_sim_id)
        os.makedirs(variant_sim_dir, exist_ok=True)

        # Copy persona profiles to variant dir
        profiles_dst = os.path.join(variant_sim_dir, "twitter_profiles.csv")
        shutil.copy2(profiles_src, profiles_dst)

        # Read parent config for agent list
        parent_config_path = os.path.join(parent_sim_dir, "simulation_config.json")
        agent_configs = []
        if os.path.exists(parent_config_path):
            with open(parent_config_path, "r", encoding="utf-8") as f:
                parent_config = json.load(f)
            raw_agents = parent_config.get("agent_configs", [])
            agent_configs = [
                {
                    "agent_id": a.get("agent_id", a.get("user_id")),
                    "activity_level": a.get("activity_level", 0.7),
                }
                for a in raw_agents
                if a.get("agent_id", a.get("user_id")) is not None
            ]

        # Write variant simulation_config.json
        variant_config = {
            "simulation_id": variant_sim_id,
            "variant_id": variant_id,
            "channel": channel,
            "num_rounds": num_rounds,
            "brand_agent_id": 0,
            "campaign_content": campaign_content,
            "agent_configs": agent_configs,
        }
        variant_config_path = os.path.join(variant_sim_dir, "simulation_config.json")
        with open(variant_config_path, "w", encoding="utf-8") as f:
            json.dump(variant_config, f, indent=2, ensure_ascii=False)

        # Launch via SimulationRunner (platform="channel" -> run_channel_simulation.py).
        # Pass max_rounds so the runner's total_rounds tracks correctly (the variant
        # config has no time_config key, so without this it defaults to 144 rounds).
        state = SimulationRunner.start_simulation(
            simulation_id=variant_sim_id,
            platform="channel",
            max_rounds=num_rounds,
        )

        logger.info(
            f"Variant simulation launched: variant_sim_id={variant_sim_id}, "
            f"channel={channel}, pid={state.process_pid}"
        )

        return jsonify({
            "success": True,
            "data": {
                "variant_sim_id": variant_sim_id,
                "simulation_dir": variant_sim_dir,
                "runner_status": state.runner_status,
                "process_pid": state.process_pid,
            }
        })

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

    except Exception as e:
        logger.error(f"launch_variant failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/variant_status/<variant_sim_id>', methods=['GET'])
def variant_status(variant_sim_id: str):
    """Poll status of a running variant simulation.

    Returns env_status.json contents plus the runner state.

    Response:
    {
        "success": true,
        "data": {
            "runner_status": "running|completed|failed",
            "env_status": {...},
            "actions_count": 42
        }
    }
    """
    try:
        sim_dir = os.path.join(SimulationRunner.RUN_STATE_DIR, variant_sim_id)
        if not os.path.isdir(sim_dir):
            return jsonify({
                "success": False,
                "error": f"Variant simulation not found: {variant_sim_id}"
            }), 404

        # Runner state
        state = SimulationRunner.get_run_state(variant_sim_id)
        runner_status = state.runner_status if state else "unknown"

        # Script-written status file
        env_status = {}
        env_status_path = os.path.join(sim_dir, "env_status.json")
        if os.path.exists(env_status_path):
            with open(env_status_path, "r", encoding="utf-8") as f:
                env_status = json.load(f)

        # Count exported agent actions (exclude sentinel lines)
        actions_count = 0
        actions_path = os.path.join(sim_dir, "actions.jsonl")
        if os.path.exists(actions_path):
            with open(actions_path, "r", encoding="utf-8") as f:
                actions_count = sum(
                    1 for line in f
                    if line.strip() and '"event_type"' not in line
                )

        return jsonify({
            "success": True,
            "data": {
                "variant_sim_id": variant_sim_id,
                "runner_status": runner_status,
                "env_status": env_status,
                "actions_count": actions_count,
            }
        })

    except Exception as e:
        logger.error(f"variant_status failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Phase 3 — A/B Testing & Campaign Variables ==============

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


@simulation_bp.route('/ab_test', methods=['POST'])
def start_ab_test():
    """Start a multi-variant A/B simulation.

    Builds a Campaign object from the request, launches all variants via
    VariantRunner (each gets its own subprocess), and persists the campaign
    so ab_status can poll it.

    Request body:
    {
        "simulation_id": "sim_xxxx",   // parent sim that ran /prepare
        "brand_name": "FreshBrew Coffee",
        "campaign_goal": "Drive trial purchase",
        "variants": [
            {
                "variant_name": "Video on Instagram",
                "channel": "instagram",
                "target_segment": "",
                "max_rounds": 10,
                "content": {
                    "format": "VideoAd",
                    "headline": "Zero Sugar. Zero Wait.",
                    "body": "Ready in 30 seconds.",
                    "cta": "Try it — 20% off",
                    "visual_desc": "Fast-paced montage",
                    "tone": "playful"
                }
            }
        ]
    }

    Response:
    {
        "success": true,
        "data": {
            "campaign_id": "...",
            "variants": [{"variant_id": "...", "variant_sim_id": "...", "status": "running"}]
        }
    }
    """
    from ..models.campaign import Campaign, CampaignVariant, CampaignContent
    from ..services.variant_runner import VariantRunner

    try:
        data = request.get_json() or {}

        simulation_id = data.get("simulation_id")
        if not simulation_id:
            return jsonify({"success": False, "error": t("api.requireSimulationId")}), 400

        variants_data = data.get("variants", [])
        if not variants_data:
            return jsonify({"success": False, "error": "At least one variant is required"}), 400

        # Build Campaign object
        campaign = Campaign(
            simulation_id=simulation_id,
            brand_name=data.get("brand_name", ""),
            campaign_goal=data.get("campaign_goal", ""),
        )

        for v_data in variants_data:
            c = v_data.get("content", {})
            content = CampaignContent(
                format=c.get("format", "CarouselPost"),
                headline=c.get("headline", ""),
                body=c.get("body", ""),
                cta=c.get("cta", ""),
                visual_desc=c.get("visual_desc", ""),
                email_subject=c.get("email_subject", ""),
                tone=c.get("tone", "neutral"),
            )
            variant = CampaignVariant(
                variant_name=v_data.get("variant_name", "Variant"),
                channel=v_data.get("channel", "instagram"),
                target_segment=v_data.get("target_segment", ""),
                max_rounds=int(v_data.get("max_rounds", 10)),
                content=content,
            )
            campaign.variants.append(variant)

        # Launch all variants
        runner = VariantRunner()
        campaign = runner.launch_all(campaign)

        # Persist campaign for polling
        _save_campaign(campaign)

        logger.info(
            f"A/B test launched: campaign_id={campaign.campaign_id}, "
            f"{len(campaign.variants)} variants"
        )

        return jsonify({
            "success": True,
            "data": {
                "campaign_id": campaign.campaign_id,
                "variants": [
                    {
                        "variant_id": v.variant_id,
                        "variant_name": v.variant_name,
                        "channel": v.channel,
                        "variant_sim_id": v.variant_sim_id,
                        "status": v.status,
                        "error": v.error,
                    }
                    for v in campaign.variants
                ],
            }
        })

    except FileNotFoundError as e:
        return jsonify({"success": False, "error": str(e)}), 400

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

    except Exception as e:
        logger.error(f"start_ab_test failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/ab_status/<campaign_id>', methods=['GET'])
def ab_status(campaign_id: str):
    """Poll the status of all variants in a campaign.

    Response:
    {
        "success": true,
        "data": {
            "campaign_id": "...",
            "total_variants": 3,
            "completed": 2,
            "failed": 0,
            "all_done": false,
            "variants": [
                {
                    "variant_id": "...",
                    "variant_name": "...",
                    "channel": "instagram",
                    "variant_sim_id": "...",
                    "runner_status": "running",
                    "env_status": {"status": "running", "timestamp": "..."},
                    "actions_count": 47
                }
            ]
        }
    }
    """
    from ..services.variant_runner import VariantRunner

    try:
        campaign = _load_campaign(campaign_id)
        if campaign is None:
            return jsonify({"success": False, "error": f"Campaign not found: {campaign_id}"}), 404

        runner = VariantRunner()
        status = runner.get_campaign_status(campaign)

        return jsonify({"success": True, "data": status})

    except Exception as e:
        logger.error(f"ab_status failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


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

@simulation_bp.route('/campaign_recommendations', methods=['POST'])
def generate_campaign_recommendations():
    """
    Score all simulation variants and generate a recommendation report.

    Request:
        { "campaign_id": "...", "graph_id": "..." }
        graph_id is optional — used to enrich recommendations with brand context.

    Returns:
        { "success": true, "data": { "task_id": "..." } }
    """
    import threading
    from ..models.task import TaskManager, TaskStatus
    from ..services.variant_scorer import VariantScorer
    from ..services.campaign_report_agent import CampaignReportAgent

    try:
        data = request.get_json() or {}
        campaign_id = data.get("campaign_id")
        graph_id = data.get("graph_id")

        if not campaign_id:
            return jsonify({"success": False, "error": "campaign_id is required"}), 400

        # Load as raw dict — _save_campaign wraps a Campaign object and can't store
        # extra keys like campaign_report; use the JSON file directly instead.
        campaign_path = os.path.join(_campaigns_dir(), f"{campaign_id}.json")
        if not os.path.exists(campaign_path):
            return jsonify({"success": False, "error": f"Campaign {campaign_id} not found"}), 404
        with open(campaign_path, "r", encoding="utf-8") as f:
            campaign_dict = json.load(f)

        task_manager = TaskManager()
        task_id = task_manager.create_task(
            task_type="campaign_report",
            metadata={"campaign_id": campaign_id},
        )

        def _run():
            try:
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.PROCESSING,
                    progress=10,
                    message="Scoring simulation variants...",
                )
                scorer = VariantScorer()
                scored = scorer.score_campaign(campaign_dict)

                if not scored:
                    task_manager.fail_task(task_id, "No completed variants with action logs found.")
                    return

                task_manager.update_task(
                    task_id,
                    progress=50,
                    message=f"Scored {len(scored)} variants. Generating recommendations...",
                )

                from ..services.kg import KGClient as _KGClient
                zep_client = _KGClient(data_dir=Config.KG_DATA_DIR) if graph_id else None

                agent = CampaignReportAgent(
                    scored_variants=scored,
                    zep_client=zep_client,
                    graph_id=graph_id,
                )
                result = agent.generate({
                    "brand_name":    campaign_dict.get("brand_name", ""),
                    "campaign_goal": campaign_dict.get("campaign_goal", ""),
                })

                # Persist report back into campaign JSON directly (bypasses Campaign.to_dict()
                # which only serialises declared dataclass fields and would drop campaign_report)
                campaign_dict["campaign_report"] = result
                with open(campaign_path, "w", encoding="utf-8") as f:
                    json.dump(campaign_dict, f, indent=2, ensure_ascii=False)

                task_manager.complete_task(
                    task_id,
                    result={"campaign_id": campaign_id, "report_saved": True},
                )

            except Exception as e:
                logger.error(f"Campaign recommendation generation failed: {e}")
                task_manager.fail_task(task_id, str(e))

        threading.Thread(target=_run, daemon=True).start()

        return jsonify({"success": True, "data": {"task_id": task_id}})

    except Exception as e:
        logger.error(f"campaign_recommendations endpoint failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


@simulation_bp.route('/campaign_report/<campaign_id>', methods=['GET'])
def get_campaign_report(campaign_id: str):
    """
    Retrieve the generated campaign recommendation report.

    Returns the full report dict saved inside the campaign JSON, plus
    pre-computed scored_variants for the UI ranking table.

    Query params:
        format=markdown  — return only the report_text as plain text
    """
    try:
        campaign_path = os.path.join(_campaigns_dir(), f"{campaign_id}.json")
        if not os.path.exists(campaign_path):
            return jsonify({"success": False, "error": f"Campaign {campaign_id} not found"}), 404
        with open(campaign_path, "r", encoding="utf-8") as f:
            campaign_dict = json.load(f)

        report = campaign_dict.get("campaign_report")
        if not report:
            return jsonify({
                "success": False,
                "error": "No report generated yet. Call POST /campaign_recommendations first.",
            }), 404

        fmt = request.args.get("format", "json")
        if fmt == "markdown":
            from flask import Response
            return Response(
                report.get("report_text", "No report text."),
                mimetype="text/markdown",
                headers={
                    "Content-Disposition": f"attachment; filename=campaign_report_{campaign_id}.md"
                },
            )

        return jsonify({"success": True, "data": report})

    except Exception as e:
        logger.error(f"get_campaign_report failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


@simulation_bp.route('/campaigns', methods=['GET'])
def list_campaigns():
    """List all past and active A/B campaigns for the history dashboard.

    Returns campaigns sorted newest-first, each enriched with a derived
    `overall_status` (pending / running / completed / failed) computed from
    variant statuses.

    Query params:
        limit (int, default 50) — max campaigns to return
    """
    try:
        limit = int(request.args.get("limit", 50))
        campaigns_dir = _campaigns_dir()

        items = []
        for fname in os.listdir(campaigns_dir):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(campaigns_dir, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue

            variants = data.get("variants", [])
            statuses = [v.get("status", "pending") for v in variants]

            if all(s == "completed" for s in statuses):
                overall_status = "completed"
            elif any(s == "failed" for s in statuses):
                overall_status = "failed"
            elif any(s == "running" for s in statuses):
                overall_status = "running"
            else:
                overall_status = "pending"

            has_report = bool(data.get("campaign_report"))

            items.append({
                "campaign_id":   data.get("campaign_id"),
                "simulation_id": data.get("simulation_id"),
                "brand_name":    data.get("brand_name", ""),
                "campaign_goal": data.get("campaign_goal", ""),
                "created_at":    data.get("created_at"),
                "variant_count": len(variants),
                "variants":      [
                    {
                        "variant_id":   v.get("variant_id"),
                        "variant_name": v.get("variant_name"),
                        "channel":      v.get("channel"),
                        "status":       v.get("status", "pending"),
                    }
                    for v in variants
                ],
                "overall_status": overall_status,
                "has_report":    has_report,
            })

        items.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        items = items[:limit]

        return jsonify({"success": True, "data": items, "total": len(items)})

    except Exception as e:
        logger.error(f"list_campaigns failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

