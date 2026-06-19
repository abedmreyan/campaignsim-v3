"""
CampaignSim Variant Scorer

Reads simulation action logs and computes engagement metrics per variant.
Uses CAMPAIGN_ACTION_WEIGHTS from config to score each action type.
"""

import json
import os
from typing import Dict, Any, List
from collections import defaultdict

from ..config import Config


class VariantScorer:
    """
    Reads action logs from completed simulation variants and produces
    engagement metrics used by the recommendation engine.
    """

    def score_variant(self, variant_output_dir: str, variant_meta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a single simulation variant.

        Args:
            variant_output_dir: path to the simulation output directory for this variant
            variant_meta: dict with variant metadata (variant_id, channel, content_format,
                          target_segment, variant_name)

        Returns:
            Scored variant dict with engagement metrics.

        File format:
            Each line in actions.jsonl is:
              {"variant_id": "...", "channel": "...", "agent_id": 1,
               "action_type": "LIKE_POST", "info": {...}, "timestamp": "..."}
            Action type strings are OASIS ActionType names matching keys in
            Config.CAMPAIGN_ACTION_WEIGHTS.
        """
        actions_file = os.path.join(variant_output_dir, "actions.jsonl")

        if not os.path.exists(actions_file):
            return {
                **variant_meta,
                "status": "no_data",
                "total_agents": 0,
                "total_actions": 0,
                "positive_actions": 0,
                "negative_actions": 0,
                "engagement_score": 0.0,
                "engagement_rate_pct": 0.0,
                "action_breakdown": {},
                "per_round_engagement": [],
                "per_agent_scores": {},
                "trend": "flat",
            }

        # Read num_rounds from simulation_config so normalisation is correct
        num_rounds = self._read_num_rounds(variant_output_dir)

        weights = Config.CAMPAIGN_ACTION_WEIGHTS
        total_agents: set = set()
        action_counts: Dict[str, int] = defaultdict(int)
        per_agent: Dict[int, float] = defaultdict(float)
        all_records: List[Dict] = []

        with open(actions_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Skip sentinel records written by run_channel_simulation.py
                event_type = record.get("event_type")
                if event_type in ("round_end", "simulation_end"):
                    continue

                agent_id = record.get("agent_id")
                action_type = record.get("action_type", "DO_NOTHING")

                if agent_id is not None:
                    total_agents.add(agent_id)
                action_counts[action_type] += 1
                weight = weights.get(action_type, 0.0)
                if agent_id is not None:
                    per_agent[agent_id] += weight
                all_records.append(record)

        # Per-round breakdown — split records into 5 equal time-slices
        per_round: List[float] = []
        if all_records:
            chunk_size = max(1, len(all_records) // 5)
            for i in range(0, len(all_records), chunk_size):
                chunk = all_records[i: i + chunk_size]
                chunk_score = sum(
                    weights.get(r.get("action_type", "DO_NOTHING"), 0.0)
                    for r in chunk
                )
                per_round.append(chunk_score / len(chunk) if chunk else 0.0)

        num_agents = max(len(total_agents), 1)
        # total_possible = one action per agent per round
        total_possible = num_agents * max(num_rounds, 1)
        raw_total_score = sum(per_agent.values())
        engagement_score = raw_total_score / total_possible if total_possible > 0 else 0.0

        positive_actions = sum(
            count for action, count in action_counts.items()
            if weights.get(action, 0.0) > 0
        )
        negative_actions = sum(
            count for action, count in action_counts.items()
            if weights.get(action, 0.0) < 0
        )
        total_actions = sum(action_counts.values())

        trend = "flat"
        if len(per_round) > 1:
            trend = "improving" if per_round[-1] > per_round[0] else (
                "declining" if per_round[-1] < per_round[0] else "flat"
            )

        return {
            **variant_meta,
            "status": "scored",
            "total_agents": num_agents,
            "total_actions": total_actions,
            "positive_actions": positive_actions,
            "negative_actions": negative_actions,
            "engagement_score": round(engagement_score, 4),
            "engagement_rate_pct": round(engagement_score * 100, 2),
            "action_breakdown": dict(action_counts),
            "per_round_engagement": [round(x, 4) for x in per_round],
            "per_agent_scores": {str(k): round(v, 4) for k, v in per_agent.items()},
            "trend": trend,
        }

    def score_campaign(self, campaign: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Score all completed variants of a campaign.

        Completion is determined by the presence of actions.jsonl in the
        variant output_dir (the subprocess writes env_status.json when done,
        and run_channel_simulation.py writes actions.jsonl at the same time),
        so we don't rely on the stored status field in the campaign JSON.

        Args:
            campaign: Campaign dict (from Campaign.to_dict() or loaded JSON)

        Returns:
            List of scored variant dicts sorted by engagement_score descending.
        """
        scored = []
        for variant in campaign.get("variants", []):
            output_dir = variant.get("output_dir")
            if not output_dir or not os.path.isdir(output_dir):
                continue

            # Include the variant if actions.jsonl exists (even if empty — will score 0)
            actions_path = os.path.join(output_dir, "actions.jsonl")
            if not os.path.exists(actions_path):
                continue

            content = variant.get("content") or {}
            meta = {
                "variant_id":     variant.get("variant_id", ""),
                "variant_name":   variant.get("variant_name", ""),
                "channel":        variant.get("channel", ""),
                "content_format": content.get("format", ""),
                "target_segment": variant.get("target_segment", "All"),
                "tone":           content.get("tone", "neutral"),
            }
            result = self.score_variant(output_dir, meta)
            scored.append(result)

        return sorted(scored, key=lambda x: x.get("engagement_score", 0), reverse=True)

    @staticmethod
    def _read_num_rounds(variant_output_dir: str) -> int:
        """Read num_rounds from simulation_config.json; default to 10."""
        config_path = os.path.join(variant_output_dir, "simulation_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                return int(cfg.get("num_rounds", 10))
            except (json.JSONDecodeError, ValueError):
                pass
        return 10
