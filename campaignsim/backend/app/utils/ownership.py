"""Per-user data ownership checks (DB-backed).

Centralises the "does this user own this resource" logic used across
graph.py, simulation_core.py, interviews.py, campaigns.py, and segments.py.
IDs (graph_id, simulation_id, campaign_id) are unguessable generated
identifiers, but that alone is not access control — every authenticated
user must still be prevented from reaching another user's resource by ID.
"""

from ..models.orm import BrandBrief, CampaignRecord, SimulationRecord
from ..models.project import ProjectManager


def user_owns_project(user, project_id: str) -> bool:
    """True if the user has a brand_briefs row backed by this legacy project_id."""
    if not project_id:
        return False
    return BrandBrief.query.filter_by(user_id=user.id, project_id=project_id).first() is not None


def user_owns_graph(user, graph_id: str) -> bool:
    """True if any of the user's brand briefs (or their backing project) reference this graph."""
    if not graph_id:
        return False
    briefs = BrandBrief.query.filter_by(user_id=user.id).all()
    for b in briefs:
        if b.graph_id == graph_id:
            return True
    for b in briefs:
        if b.project_id:
            project = ProjectManager.get_project(b.project_id)
            if project and project.graph_id == graph_id:
                return True
    return False


def user_owns_simulation(user, simulation_id: str) -> bool:
    """True if a SimulationRecord for this sim_key belongs to the user."""
    if not simulation_id:
        return False
    rec = SimulationRecord.query.filter_by(sim_key=simulation_id).first()
    return bool(rec and rec.user_id == user.id)


def user_owns_campaign(user, campaign_id: str) -> bool:
    """True if a CampaignRecord for this campaign_ref belongs to the user."""
    if not campaign_id:
        return False
    rec = CampaignRecord.query.filter_by(campaign_ref=campaign_id).first()
    return bool(rec and rec.user_id == user.id)
