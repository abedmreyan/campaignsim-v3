"""Shared background job for building a knowledge graph from project text.

Extracted from api/graph.py so both the graph routes and the brand-brief
routes (rebuild-graph) can launch the identical build flow.
"""

import threading
import traceback

from ..config import Config
from ..models.project import ProjectManager, ProjectStatus
from ..models.task import TaskManager, TaskStatus
from ..services.graph_builder import GraphBuilderService
from ..services.text_processor import TextProcessor
from ..utils.locale import t, get_locale, set_locale
from ..utils.logger import get_logger

logger = get_logger('campaignsim.services.graph_build_job')


def start_graph_build(
    project,
    text: str,
    graph_name: str,
    chunk_size: int,
    chunk_overlap: int,
    on_success=None,
    on_failure=None,
    user_id=None,
) -> str:
    """Start the KG build in a daemon thread. Returns the task_id immediately.

    on_success(graph_id) / on_failure(error_str) are invoked at the end of the
    background thread — callers that touch the DB must wrap their callback in
    an app context themselves.
    """
    task_manager = TaskManager()
    task_id = task_manager.create_task(f"Build graph: {graph_name}", user_id=str(user_id) if user_id else None)
    logger.info(f"Created graph build task: task_id={task_id}, project_id={project.project_id}")

    project.status = ProjectStatus.GRAPH_BUILDING
    project.graph_build_task_id = task_id
    project.chunk_size = chunk_size
    project.chunk_overlap = chunk_overlap
    ProjectManager.save_project(project)

    current_locale = get_locale()
    project_id = project.project_id
    ontology = project.ontology

    def build_task():
        set_locale(current_locale)
        build_logger = get_logger('campaignsim.build')
        try:
            build_logger.info(f"[{task_id}] Starting graph build...")
            task_manager.update_task(
                task_id,
                status=TaskStatus.PROCESSING,
                message=t('progress.initGraphService')
            )

            builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)

            task_manager.update_task(task_id, message=t('progress.textChunking'), progress=5)
            chunks = TextProcessor.split_text(text, chunk_size=chunk_size, overlap=chunk_overlap)
            total_chunks = len(chunks)

            task_manager.update_task(task_id, message=t('progress.creatingZepGraph'), progress=10)
            graph_id = builder.create_graph(name=graph_name)

            project.graph_id = graph_id
            ProjectManager.save_project(project)

            task_manager.update_task(task_id, message=t('progress.settingOntology'), progress=15)
            builder.set_ontology(graph_id, ontology)

            def add_progress_callback(msg, progress_ratio):
                task_manager.update_task(
                    task_id, message=msg, progress=15 + int(progress_ratio * 40)
                )

            task_manager.update_task(
                task_id, message=t('progress.addingChunks', count=total_chunks), progress=15
            )
            episode_uuids = builder.add_text_batches(
                graph_id, chunks, batch_size=3, progress_callback=add_progress_callback
            )

            task_manager.update_task(
                task_id, message=t('progress.waitingZepProcess'), progress=55
            )

            def wait_progress_callback(msg, progress_ratio):
                task_manager.update_task(
                    task_id, message=msg, progress=55 + int(progress_ratio * 35)
                )

            builder._wait_for_episodes(episode_uuids, wait_progress_callback)

            task_manager.update_task(
                task_id, message=t('progress.fetchingGraphData'), progress=95
            )
            graph_data = builder.get_graph_data(graph_id)

            project.status = ProjectStatus.GRAPH_COMPLETED
            ProjectManager.save_project(project)

            node_count = graph_data.get("node_count", 0)
            edge_count = graph_data.get("edge_count", 0)
            build_logger.info(
                f"[{task_id}] Graph build complete: graph_id={graph_id}, "
                f"nodes={node_count}, edges={edge_count}"
            )

            task_manager.update_task(
                task_id,
                status=TaskStatus.COMPLETED,
                message=t('progress.graphBuildComplete'),
                progress=100,
                result={
                    "project_id": project_id,
                    "graph_id": graph_id,
                    "node_count": node_count,
                    "edge_count": edge_count,
                    "chunk_count": total_chunks
                }
            )
            if on_success:
                on_success(graph_id)

        except Exception as e:
            build_logger.error(f"[{task_id}] Graph build failed: {str(e)}")
            build_logger.debug(traceback.format_exc())

            project.status = ProjectStatus.FAILED
            project.error = str(e)
            ProjectManager.save_project(project)

            task_manager.update_task(
                task_id,
                status=TaskStatus.FAILED,
                message=t('progress.buildFailed', error=str(e)),
                error=traceback.format_exc()
            )
            if on_failure:
                on_failure(str(e))

    threading.Thread(target=build_task, daemon=True).start()
    return task_id
