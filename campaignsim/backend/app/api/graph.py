"""Graph API routes
Uses project context mechanism with server-side persistent state"""

import os
import traceback
import threading
from flask import request, jsonify, g

from . import graph_bp
from ..config import Config
from ..extensions import db
from ..models.orm import BrandBrief
from ..services.business_context import BUSINESS_TYPES
from ..services.ontology_generator import OntologyGenerator
from ..services.graph_builder import GraphBuilderService
from ..services.text_processor import TextProcessor
from ..utils.file_parser import FileParser
from ..utils.logger import get_logger
from ..utils.locale import t, get_locale, set_locale
from ..models.task import TaskManager, TaskStatus
from ..models.project import ProjectManager, ProjectStatus
from ..utils.ownership import user_owns_graph

logger = get_logger('campaignsim.api')

def allowed_file(filename: str) -> bool:
    """..."""
    if not filename or '.' not in filename:
        return False
    ext = os.path.splitext(filename)[1].lower().lstrip('.')
    return ext in Config.ALLOWED_EXTENSIONS


def _owned_brief_for_project(project_id: str):
    """Return the current user's BrandBrief row for this project, or None.

    Ownership of legacy file-based projects is tracked through the
    brand_briefs table (each project created via the API gets a brief row).
    """
    return BrandBrief.query.filter_by(
        user_id=g.current_user.id, project_id=project_id
    ).first()


# ==============  ==============

@graph_bp.route('/project/<project_id>', methods=['GET'])
def get_project(project_id: str):
    """..."""
    if not _owned_brief_for_project(project_id):
        return jsonify({
            "success": False,
            "error": t('api.projectNotFound', id=project_id)
        }), 404

    project = ProjectManager.get_project(project_id)

    if not project:
        return jsonify({
            "success": False,
            "error": t('api.projectNotFound', id=project_id)
        }), 404

    return jsonify({
        "success": True,
        "data": project.to_dict()
    })

@graph_bp.route('/project/list', methods=['GET'])
def list_projects():
    """List the current user's projects (ownership via brand_briefs rows)."""
    limit = request.args.get('limit', 50, type=int)
    owned_ids = {
        b.project_id
        for b in BrandBrief.query.filter_by(user_id=g.current_user.id).all()
        if b.project_id
    }
    projects = [p for p in ProjectManager.list_projects(limit=1000) if p.project_id in owned_ids]
    projects = projects[:limit]

    return jsonify({
        "success": True,
        "data": [p.to_dict() for p in projects],
        "count": len(projects)
    })

@graph_bp.route('/project/<project_id>', methods=['DELETE'])
def delete_project(project_id: str):
    """..."""
    brief = _owned_brief_for_project(project_id)
    if not brief:
        return jsonify({
            "success": False,
            "error": t('api.projectDeleteFailed', id=project_id)
        }), 404

    success = ProjectManager.delete_project(project_id)
    if success:
        # Unlink the brief from the deleted project/graph but keep its text.
        brief.project_id = None
        brief.graph_id = None
        brief.graph_status = 'pending'
        db.session.commit()

    if not success:
        return jsonify({
            "success": False,
            "error": t('api.projectDeleteFailed', id=project_id)
        }), 404

    return jsonify({
        "success": True,
        "message": t('api.projectDeleted', id=project_id)
    })

@graph_bp.route('/project/<project_id>/reset', methods=['POST'])
def reset_project(project_id: str):
    """..."""
    if not _owned_brief_for_project(project_id):
        return jsonify({
            "success": False,
            "error": t('api.projectNotFound', id=project_id)
        }), 404

    project = ProjectManager.get_project(project_id)

    if not project:
        return jsonify({
            "success": False,
            "error": t('api.projectNotFound', id=project_id)
        }), 404

    if project.ontology:
        project.status = ProjectStatus.ONTOLOGY_GENERATED
    else:
        project.status = ProjectStatus.CREATED
    
    project.graph_id = None
    project.graph_build_task_id = None
    project.error = None
    ProjectManager.save_project(project)
    
    return jsonify({
        "success": True,
        "message": t('api.projectReset', id=project_id),
        "data": project.to_dict()
    })

# ============== 1 ==============

@graph_bp.route('/ontology/generate', methods=['POST'])
def generate_ontology():
    """    1
    
    multipart/form-data
    
        files: PDF/MD/TXT
        simulation_requirement: 
        project_name: 
        additional_context: 
        
        {
            "success": true,
            "data": {
                "project_id": "proj_xxxx",
                "ontology": {
                    "entity_types": [...],
                    "edge_types": [...],
                    "analysis_summary": "..."
                },
                "files": [...],
                "total_text_length": 12345
            }
        }"""
    try:
        logger.info("=== ===")
        
        simulation_requirement = request.form.get('simulation_requirement', '')
        project_name = request.form.get('project_name', 'Unnamed Project')
        additional_context = request.form.get('additional_context', '')
        business_type = request.form.get('business_type') or None
        if business_type and business_type not in BUSINESS_TYPES:
            return jsonify({
                "success": False,
                "error": f"business_type must be one of {BUSINESS_TYPES}",
            }), 400
        
        logger.debug(f"Project name: {project_name}")
        logger.debug(f"Campaign goal: {simulation_requirement[:100]}...")
        
        if not simulation_requirement:
            return jsonify({
                "success": False,
                "error": t('api.requireSimulationRequirement')
            }), 400
        
        uploaded_files = request.files.getlist('files')
        if not uploaded_files or all(not f.filename for f in uploaded_files):
            return jsonify({
                "success": False,
                "error": t('api.requireFileUpload')
            }), 400
        
        project = ProjectManager.create_project(name=project_name)
        project.simulation_requirement = simulation_requirement
        logger.info(f"Created project: {project.project_id}")
        
        document_texts = []
        all_text = ""
        
        for file in uploaded_files:
            if file and file.filename and allowed_file(file.filename):
                file_info = ProjectManager.save_file_to_project(
                    project.project_id, 
                    file, 
                    file.filename
                )
                project.files.append({
                    "filename": file_info["original_filename"],
                    "size": file_info["size"]
                })
                
                text = FileParser.extract_text(file_info["path"])
                text = TextProcessor.preprocess_text(text)
                document_texts.append(text)
                all_text += f"\n\n=== {file_info['original_filename']} ===\n{text}"
        
        if not document_texts:
            ProjectManager.delete_project(project.project_id)
            return jsonify({
                "success": False,
                "error": t('api.noDocProcessed')
            }), 400
        
        project.total_text_length = len(all_text)
        ProjectManager.save_extracted_text(project.project_id, all_text)
        logger.info(f"Text extraction complete, total {len(all_text)} chars")
        
        logger.info("LLM ...")
        generator = OntologyGenerator()
        ontology = generator.generate(
            document_texts=document_texts,
            simulation_requirement=simulation_requirement,
            additional_context=additional_context if additional_context else None,
            business_type=business_type,
        )
        
        entity_count = len(ontology.get("entity_types", []))
        edge_count = len(ontology.get("edge_types", []))
        logger.info(f"Ontology generated: {entity_count} entity types, {edge_count} relationship types")
        
        project.ontology = {
            "entity_types": ontology.get("entity_types", []),
            "edge_types": ontology.get("edge_types", [])
        }
        project.analysis_summary = ontology.get("analysis_summary", "")
        project.status = ProjectStatus.ONTOLOGY_GENERATED
        ProjectManager.save_project(project)
        logger.info(f"=== Ontology complete === Project ID: {project.project_id}")

        # Record ownership + reusable brief text for this user.
        brief = BrandBrief(
            user_id=g.current_user.id,
            name=project_name,
            content=all_text,
            project_id=project.project_id,
            graph_status='pending',
            business_type=business_type,
        )
        db.session.add(brief)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "data": {
                "project_id": project.project_id,
                "project_name": project.name,
                "ontology": project.ontology,
                "analysis_summary": project.analysis_summary,
                "files": project.files,
                "total_text_length": project.total_text_length
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

# ============== 2 ==============

@graph_bp.route('/build', methods=['POST'])
def build_graph():
    """    2project_id
    
    JSON
        {
            "project_id": "proj_xxxx",  // 1
            "graph_name": "",    // 
            "chunk_size": 500,          // 500
            "chunk_overlap": 50         // 50
        }
        
        {
            "success": true,
            "data": {
                "project_id": "proj_xxxx",
                "task_id": "task_xxxx",
                "message": ""
            }
        }"""
    try:
        logger.info("=== ===")
        
        errors = []
        if Config.KG_BACKEND == 'zep' and not Config.ZEP_API_KEY:
            errors.append(t('api.zepApiKeyMissing'))
        if errors:
            logger.error(f"Config error: {errors}")
            return jsonify({
                "success": False,
                "error": t('api.configError', details="; ".join(errors))
            }), 500
        
        data = request.get_json() or {}
        project_id = data.get('project_id')
        logger.debug(f"Request params: project_id={project_id}")

        if not project_id:
            return jsonify({
                "success": False,
                "error": t('api.requireProjectId')
            }), 400

        brief = _owned_brief_for_project(project_id)
        if not brief:
            return jsonify({
                "success": False,
                "error": t('api.projectNotFound', id=project_id)
            }), 404

        project = ProjectManager.get_project(project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": t('api.projectNotFound', id=project_id)
            }), 404

        force = data.get('force', False)
        
        if project.status == ProjectStatus.CREATED:
            return jsonify({
                "success": False,
                "error": t('api.ontologyNotGenerated')
            }), 400
        
        if project.status == ProjectStatus.GRAPH_BUILDING and not force:
            return jsonify({
                "success": False,
                "error": t('api.graphBuilding'),
                "task_id": project.graph_build_task_id
            }), 400
        
        if force and project.status in [ProjectStatus.GRAPH_BUILDING, ProjectStatus.FAILED, ProjectStatus.GRAPH_COMPLETED]:
            project.status = ProjectStatus.ONTOLOGY_GENERATED
            project.graph_id = None
            project.graph_build_task_id = None
            project.error = None
        
        graph_name = data.get('graph_name', project.name or 'CampaignSim Graph')
        chunk_size = data.get('chunk_size', project.chunk_size or Config.DEFAULT_CHUNK_SIZE)
        chunk_overlap = data.get('chunk_overlap', project.chunk_overlap or Config.DEFAULT_CHUNK_OVERLAP)
        
        project.chunk_size = chunk_size
        project.chunk_overlap = chunk_overlap
        
        text = ProjectManager.get_extracted_text(project_id)
        if not text:
            return jsonify({
                "success": False,
                "error": t('api.textNotFound')
            }), 400
        
        ontology = project.ontology
        if not ontology:
            return jsonify({
                "success": False,
                "error": t('api.ontologyNotFound')
            }), 400
        
        from flask import current_app
        from ..services.graph_build_job import start_graph_build

        app_obj = current_app._get_current_object()
        brief_id = brief.id

        def _sync_brief(graph_id=None, status='ready'):
            with app_obj.app_context():
                b = db.session.get(BrandBrief, brief_id)
                if b:
                    if graph_id:
                        b.graph_id = graph_id
                    b.graph_status = status
                    db.session.commit()

        brief.graph_status = 'building'
        db.session.commit()

        task_id = start_graph_build(
            project=project,
            text=text,
            graph_name=graph_name,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            on_success=lambda gid: _sync_brief(graph_id=gid, status='ready'),
            on_failure=lambda err: _sync_brief(status='failed'),
        )

        return jsonify({
            "success": True,
            "data": {
                "project_id": project_id,
                "task_id": task_id,
                "message": t('api.graphBuildStarted', taskId=task_id)
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

# ==============  ==============

@graph_bp.route('/task/<task_id>', methods=['GET'])
def get_task(task_id: str):
    """..."""
    task = TaskManager().get_task(task_id)
    
    if not task:
        return jsonify({
            "success": False,
            "error": t('api.taskNotFound', id=task_id)
        }), 404
    
    return jsonify({
        "success": True,
        "data": task.to_dict()
    })

@graph_bp.route('/tasks', methods=['GET'])
def list_tasks():
    """..."""
    tasks = TaskManager().list_tasks()
    
    return jsonify({
        "success": True,
        "data": [t.to_dict() for t in tasks],
        "count": len(tasks)
    })

# ==============  ==============

@graph_bp.route('/data/<graph_id>', methods=['GET'])
def get_graph_data(graph_id: str):
    """..."""
    try:
        if not user_owns_graph(g.current_user, graph_id):
            return jsonify({"success": False, "error": "Graph not found"}), 404
        if Config.KG_BACKEND == 'zep' and not Config.ZEP_API_KEY:
            return jsonify({
                "success": False,
                "error": t('api.zepApiKeyMissing')
            }), 500
        
        builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)
        graph_data = builder.get_graph_data(graph_id)
        
        return jsonify({
            "success": True,
            "data": graph_data
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

@graph_bp.route('/delete/<graph_id>', methods=['DELETE'])
def delete_graph(graph_id: str):
    """    Zep"""
    try:
        if not user_owns_graph(g.current_user, graph_id):
            return jsonify({"success": False, "error": "Graph not found"}), 404
        if Config.KG_BACKEND == 'zep' and not Config.ZEP_API_KEY:
            return jsonify({
                "success": False,
                "error": t('api.zepApiKeyMissing')
            }), 500
        
        builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)
        builder.delete_graph(graph_id)
        
        return jsonify({
            "success": True,
            "message": t('api.graphDeleted', id=graph_id)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500
