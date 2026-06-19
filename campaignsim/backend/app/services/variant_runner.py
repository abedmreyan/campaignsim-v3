"""
CampaignSim — Variant Runner

Launches all variants of a campaign, each as a separate channel simulation
subprocess via SimulationRunner (platform="channel"). All variants start
immediately; each runs independently in its own directory.
"""

import json
import logging
import os
import shutil
from typing import Callable, Dict, List, Optional

from ..models.campaign import Campaign, CampaignVariant
from ..services.simulation_runner import SimulationRunner
from ..utils.logger import get_logger

logger = get_logger("campaignsim.variant_runner")


class VariantRunner:
    """
    Launches multiple campaign variants in parallel.

    Each variant maps to a separate SimulationRunner subprocess using the
    "channel" platform dispatch added in Phase 2. Because start_simulation()
    returns immediately (the monitor thread runs in the background), simply
    calling it N times in a loop achieves true parallelism.
    """

    def launch_all(
        self,
        campaign: Campaign,
        progress_callback: Optional[Callable[[str, str, str], None]] = None,
    ) -> Campaign:
        """
        Launch all variants of a campaign.

        Args:
            campaign: Campaign with variants defined and simulation_id set
                      to the parent simulation that already ran /prepare
                      (needed to locate twitter_profiles.csv).
            progress_callback: called with (variant_id, status, message)

        Returns:
            Updated Campaign with variant_sim_id, status, and output_dir filled in.
        """
        parent_sim_id = campaign.simulation_id
        if not parent_sim_id:
            raise ValueError("campaign.simulation_id must be set before launching variants")

        parent_sim_dir = os.path.join(SimulationRunner.RUN_STATE_DIR, parent_sim_id)
        profiles_src = os.path.join(parent_sim_dir, "twitter_profiles.csv")

        if not os.path.exists(profiles_src):
            raise FileNotFoundError(
                f"twitter_profiles.csv not found at {profiles_src}. "
                "Run /prepare on the parent simulation first."
            )

        # Load parent config once — used to copy agent_configs to variants
        parent_config_path = os.path.join(parent_sim_dir, "simulation_config.json")
        base_agent_configs = []
        if os.path.exists(parent_config_path):
            with open(parent_config_path, "r", encoding="utf-8") as f:
                parent_config = json.load(f)
            raw_agents = parent_config.get("agent_configs", [])
            base_agent_configs = [
                {
                    "agent_id": a.get("agent_id", a.get("user_id")),
                    "activity_level": a.get("activity_level", 0.7),
                }
                for a in raw_agents
                if a.get("agent_id", a.get("user_id")) is not None
            ]

        for variant in campaign.variants:
            self._launch_variant(
                variant=variant,
                campaign=campaign,
                parent_sim_dir=parent_sim_dir,
                profiles_src=profiles_src,
                base_agent_configs=base_agent_configs,
                progress_callback=progress_callback,
            )

        return campaign

    def _launch_variant(
        self,
        variant: CampaignVariant,
        campaign: Campaign,
        parent_sim_dir: str,
        profiles_src: str,
        base_agent_configs: List[Dict],
        progress_callback: Optional[Callable],
    ):
        """Set up and launch a single variant subprocess."""
        variant_sim_id = f"{campaign.simulation_id}__{variant.variant_id}"
        variant.variant_sim_id = variant_sim_id
        variant.status = "running"

        if progress_callback:
            progress_callback(variant.variant_id, "running", f"Starting {variant.variant_name}")

        try:
            # Create variant simulation directory
            variant_sim_dir = os.path.join(SimulationRunner.RUN_STATE_DIR, variant_sim_id)
            os.makedirs(variant_sim_dir, exist_ok=True)
            variant.output_dir = variant_sim_dir

            # Copy persona profiles — use segment-filtered CSV if available
            profiles_dst = os.path.join(variant_sim_dir, "twitter_profiles.csv")
            if variant.target_segment:
                seg_filename = f"profiles_{variant.target_segment.replace(' ', '_')}.csv"
                seg_path = os.path.join(parent_sim_dir, seg_filename)
                profiles_src_for_variant = seg_path if os.path.exists(seg_path) else profiles_src
                if not os.path.exists(seg_path):
                    logger.warning(
                        f"Segment CSV {seg_filename} not found; falling back to full profiles CSV"
                    )
            else:
                profiles_src_for_variant = profiles_src
            shutil.copy2(profiles_src_for_variant, profiles_dst)

            # Build framed campaign content string
            campaign_content = variant.formatted_content()
            if not campaign_content:
                raise ValueError(f"Variant {variant.variant_id}: campaign content is empty")

            # Write variant simulation_config.json
            variant_config = {
                "simulation_id": variant_sim_id,
                "variant_id": variant.variant_id,
                "channel": variant.channel,
                "num_rounds": variant.max_rounds,
                "brand_agent_id": 0,
                "campaign_content": campaign_content,
                "agent_configs": base_agent_configs,
                "campaign_meta": {
                    "brand_name": campaign.brand_name,
                    "campaign_goal": campaign.campaign_goal,
                    "variant_name": variant.variant_name,
                    "target_segment": variant.target_segment,
                },
            }
            config_path = os.path.join(variant_sim_dir, "simulation_config.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(variant_config, f, indent=2, ensure_ascii=False)

            # Launch subprocess (returns immediately; monitor thread tracks progress)
            state = SimulationRunner.start_simulation(
                simulation_id=variant_sim_id,
                platform="channel",
                max_rounds=variant.max_rounds,
            )

            logger.info(
                f"Variant launched: variant_sim_id={variant_sim_id}, "
                f"channel={variant.channel}, pid={state.process_pid}"
            )

        except Exception as e:
            variant.status = "failed"
            variant.error = str(e)
            logger.error(f"Variant {variant.variant_id} launch failed: {e}")
            if progress_callback:
                progress_callback(variant.variant_id, "failed", str(e))

    def get_variant_status(self, variant_sim_id: str) -> Dict:
        """
        Return current status for a single variant simulation.

        Reads env_status.json (written by the script) and the SimulationRunner
        state, then counts exported action log entries.
        """
        sim_dir = os.path.join(SimulationRunner.RUN_STATE_DIR, variant_sim_id)
        if not os.path.isdir(sim_dir):
            return {"variant_sim_id": variant_sim_id, "runner_status": "not_found"}

        state = SimulationRunner.get_run_state(variant_sim_id)
        runner_status = state.runner_status if state else "unknown"

        env_status = {}
        env_status_path = os.path.join(sim_dir, "env_status.json")
        if os.path.exists(env_status_path):
            with open(env_status_path, "r", encoding="utf-8") as f:
                env_status = json.load(f)

        actions_count = 0
        actions_path = os.path.join(sim_dir, "actions.jsonl")
        if os.path.exists(actions_path):
            with open(actions_path, "r", encoding="utf-8") as f:
                actions_count = sum(
                    1 for line in f
                    if line.strip() and '"event_type"' not in line
                )

        return {
            "variant_sim_id": variant_sim_id,
            "runner_status": runner_status,
            "env_status": env_status,
            "actions_count": actions_count,
        }

    def get_campaign_status(self, campaign: Campaign) -> Dict:
        """
        Return status for all variants in a campaign.

        Returns summary counts and per-variant status.
        """
        variant_statuses = []
        for variant in campaign.variants:
            if variant.variant_sim_id:
                status = self.get_variant_status(variant.variant_sim_id)
                status["variant_id"] = variant.variant_id
                status["variant_name"] = variant.variant_name
                status["channel"] = variant.channel
            else:
                status = {
                    "variant_id": variant.variant_id,
                    "variant_name": variant.variant_name,
                    "channel": variant.channel,
                    "runner_status": variant.status,
                    "actions_count": 0,
                }
            variant_statuses.append(status)

        completed = sum(
            1 for s in variant_statuses
            if s.get("env_status", {}).get("status") == "completed"
               or s.get("runner_status") == "completed"
        )
        failed = sum(
            1 for s in variant_statuses
            if s.get("runner_status") == "failed"
        )
        total = len(variant_statuses)
        all_done = (completed + failed) == total

        return {
            "campaign_id": campaign.campaign_id,
            "total_variants": total,
            "completed": completed,
            "failed": failed,
            "all_done": all_done,
            "variants": variant_statuses,
        }
