"""Campaign iteration lineage (Phase 3).

Campaigns form a linear chain via CampaignRecord.parent_campaign_id — an
Insight session's redesign proposal, once committed through a fresh Designer
session, becomes iteration N+1 pointing back at iteration N. This module
walks that chain in both directions and attaches each iteration's scored
results (from its campaign JSON's campaign_report, if generated) so the
chain can be rendered as a comparison table.
"""

import json
import os
from typing import Any, Dict, List, Optional

from ..models.orm import CampaignRecord
from .simulation_helpers import _campaigns_dir


def _load_report(campaign_ref: Optional[str]) -> Optional[Dict[str, Any]]:
    if not campaign_ref:
        return None
    path = os.path.join(_campaigns_dir(), f"{campaign_ref}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f).get("campaign_report")


def _summarize(record: CampaignRecord) -> Dict[str, Any]:
    report = _load_report(record.campaign_ref)
    scored = (report or {}).get("scored_variants") or []
    rates = [v.get("engagement_rate_pct", 0.0) for v in scored]
    best = scored[0] if scored else None
    return {
        "id": str(record.id),
        "campaign_ref": record.campaign_ref,
        "iteration": record.iteration,
        "brand_name": record.brand_name,
        "campaign_goal": record.campaign_goal,
        "objective": record.objective,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "scored": bool(scored),
        "avg_engagement_rate_pct": round(sum(rates) / len(rates), 2) if rates else None,
        "best_variant_name": best.get("variant_name") if best else None,
        "best_engagement_rate_pct": best.get("engagement_rate_pct") if best else None,
    }


def get_lineage_chain(campaign_record: CampaignRecord) -> List[Dict[str, Any]]:
    """Return every iteration of this campaign's lineage, oldest first."""
    ancestors: List[CampaignRecord] = []
    node = campaign_record
    seen = {node.id}
    while node.parent_campaign_id:
        parent = CampaignRecord.query.get(node.parent_campaign_id)
        if not parent or parent.id in seen:
            break
        ancestors.append(parent)
        seen.add(parent.id)
        node = parent

    descendants: List[CampaignRecord] = []
    node = campaign_record
    while True:
        child = CampaignRecord.query.filter_by(parent_campaign_id=node.id).first()
        if not child or child.id in seen:
            break
        descendants.append(child)
        seen.add(child.id)
        node = child

    chain = list(reversed(ancestors)) + [campaign_record] + descendants
    return [_summarize(c) for c in chain]
