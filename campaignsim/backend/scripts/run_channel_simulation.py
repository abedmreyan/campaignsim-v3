"""
CampaignSim — Channel Simulation Script

Runs an OASIS Twitter-substrate simulation where:
- Agent 0 (brand agent) posts the campaign content as the initial post
- Persona agents (agents 1..N) react over num_rounds using LLMAction
- Results are logged live, per round, with real round numbers
- A final reconciliation pass catches any trailing trace rows

Usage:
    python run_channel_simulation.py --config /path/to/simulation_config.json
    python run_channel_simulation.py --config /path/to/simulation_config.json --no-wait

Channel mechanics (from simulation_config.json's "channel_def" block, written
by VariantRunner from the channel registry):
- available_actions / action_weights / funnel_map are channel-specific real
  OASIS ActionType.value strings (lowercase snake_case) — see CAMEL-AI OASIS's
  ActionType enum (social_platform/typing.py) for the full valid vocabulary.
- kind="feed": agents see and can react to the shared social graph (posts,
  reposts, replies) — the platform's built-in recommendation feed, as before.
- kind="direct": the channel has no sharing mechanic (email, SMS) — this is
  enforced by the channel definition's available_actions simply not including
  repost/quote_post/create_comment, so agents cannot amplify content into a
  shared feed even though OASIS's underlying platform is still a single
  shared substrate. NOTE: OASIS does not provide a private/isolated feed
  primitive, so persona agents technically still query the same platform
  recommendation system LLMAction always triggers; true per-recipient content
  isolation would require running one isolated `oasis.make()` environment per
  agent, which is a larger change deferred past this pass. This is a
  documented approximation, not a silent gap.
"""

import argparse
import asyncio
import json
import logging
import os
import random
import signal
import sqlite3
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import oasis
from oasis import (
    ActionType,
    LLMAction,
    ManualAction,
    generate_twitter_agent_graph,
)
from camel.models import ModelFactory
from camel.types import ModelPlatformType

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("campaignsim.channel_simulation")

# Shutdown event — set by SIGTERM/SIGINT handler
_shutdown_event: Optional[asyncio.Event] = None

# Used only when a config has no channel_def block (legacy/back-compat).
LEGACY_AVAILABLE_ACTIONS = [
    ActionType.CREATE_POST,
    ActionType.LIKE_POST,
    ActionType.REPOST,
    ActionType.QUOTE_POST,
    ActionType.FOLLOW,
    ActionType.DO_NOTHING,
]


def load_config(config_path: str) -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_available_actions(channel_def: Optional[Dict[str, Any]]) -> List[ActionType]:
    """Convert a channel_def's available_actions (real ActionType.value strings,
    e.g. "create_post") into ActionType enum members. Falls back to the legacy
    fixed Twitter-style action set if no channel_def is present."""
    if not channel_def or not channel_def.get("available_actions"):
        return LEGACY_AVAILABLE_ACTIONS

    resolved = []
    for action_str in channel_def["available_actions"]:
        try:
            resolved.append(ActionType(action_str))
        except ValueError:
            logger.warning(f"Unknown action '{action_str}' in channel_def — skipping")
    return resolved or LEGACY_AVAILABLE_ACTIONS


def create_model(config: Dict[str, Any]):
    """Create the LLM model from environment variables."""
    llm_api_key = os.environ.get("LLM_API_KEY", "")
    llm_base_url = os.environ.get("LLM_BASE_URL", "")
    llm_model = os.environ.get("LLM_MODEL_NAME", "") or config.get("llm_model", "gpt-4o-mini")

    if llm_api_key:
        os.environ["OPENAI_API_KEY"] = llm_api_key
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("Missing API key — set LLM_API_KEY in environment")
    if llm_base_url:
        os.environ["OPENAI_API_BASE_URL"] = llm_base_url

    return ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=llm_model,
    )


def write_status(simulation_dir: str, status: str, extra: dict = None):
    """Write simulation status to env_status.json (for Flask polling)."""
    data = {"status": status, "timestamp": datetime.utcnow().isoformat()}
    if extra:
        data.update(extra)
    status_path = os.path.join(simulation_dir, "env_status.json")
    with open(status_path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def write_round_sentinel(actions_log_path: str, round_num: int, total_rounds: int):
    """Append a round_end sentinel to the JSONL log (for live progress polling)."""
    sentinel = {
        "event_type": "round_end",
        "round_num": round_num,
        "total_rounds": total_rounds,
        "timestamp": datetime.utcnow().isoformat(),
    }
    with open(actions_log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(sentinel) + "\n")


def export_new_trace_rows(
    db_path: str,
    output_path: str,
    variant_id: str,
    channel: str,
    round_num: int,
    since_rowid: int,
) -> int:
    """
    Append any trace rows with rowid > since_rowid to the JSONL action log,
    tagged with the real round_num they occurred in.

    Called after every env.step() so actions.jsonl reflects real, live,
    per-round data — not a single end-of-run dump with a fake 5-slice
    approximation. Returns the highest rowid seen (0 if none), so the caller
    can advance its cursor.

    Each line:
    {
        "variant_id": "...", "channel": "...", "round_num": 3,
        "agent_id": 42, "action_type": "like_post", "info": {...},
        "timestamp": "..."
    }
    action_type is the raw OASIS ActionType.value string (lowercase snake_case)
    — this MUST match the channel registry's action_weights keys exactly.
    """
    if not os.path.exists(db_path):
        return since_rowid

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT rowid, user_id, action, info, created_at FROM trace "
            "WHERE rowid > ? ORDER BY rowid",
            (since_rowid,),
        ).fetchall()
    except sqlite3.OperationalError as e:
        logger.error(f"Failed to read trace table: {e}")
        return since_rowid
    finally:
        conn.close()

    if not rows:
        return since_rowid

    max_rowid = since_rowid
    with open(output_path, "a", encoding="utf-8") as f:
        for rowid, user_id, action, info_json, created_at in rows:
            max_rowid = max(max_rowid, rowid)
            try:
                info = json.loads(info_json) if info_json else {}
            except json.JSONDecodeError:
                info = {"raw": info_json}

            entry = {
                "variant_id": variant_id,
                "channel": channel,
                "round_num": round_num,
                "agent_id": user_id,
                "action_type": action,
                "info": info,
                "timestamp": created_at,
            }
            f.write(json.dumps(entry) + "\n")

    return max_rowid


async def run_simulation(config_path: str):
    """Main simulation coroutine."""
    config = load_config(config_path)
    simulation_dir = os.path.dirname(os.path.abspath(config_path))

    variant_id = config.get("variant_id", "unknown")
    channel = config.get("channel", "instagram")
    channel_def = config.get("channel_def") or {}
    channel_kind = channel_def.get("kind", "feed")
    num_rounds = config.get("num_rounds", 10)
    brand_agent_id = config.get("brand_agent_id", 0)
    campaign_content = config.get("campaign_content", "")
    agent_configs = config.get("agent_configs", [])

    available_actions = resolve_available_actions(channel_def)

    print(
        f"Starting channel simulation: variant={variant_id}, channel={channel} "
        f"(kind={channel_kind}), rounds={num_rounds}, "
        f"actions={[a.value for a in available_actions]}"
    )
    write_status(simulation_dir, "starting")

    # Build the model
    model = create_model(config)

    # Agent graph from CSV
    profile_path = os.path.join(simulation_dir, "twitter_profiles.csv")
    if not os.path.exists(profile_path):
        msg = f"Profile CSV not found: {profile_path}"
        write_status(simulation_dir, "failed", {"error": msg})
        print(f"Error: {msg}", file=sys.stderr)
        return False

    print(f"Loading agent graph from {profile_path}")
    agent_graph = await generate_twitter_agent_graph(
        profile_path=profile_path,
        model=model,
        available_actions=available_actions,
    )

    # Environment (uses Twitter as the simulation substrate for all channels)
    db_path = os.path.join(simulation_dir, "channel_simulation.db")
    if os.path.exists(db_path):
        os.remove(db_path)  # fresh run each time

    env = oasis.make(
        agent_graph=agent_graph,
        platform=oasis.DefaultPlatformType.TWITTER,
        database_path=db_path,
        semaphore=30,
    )
    await env.reset()
    write_status(simulation_dir, "running")

    # JSONL log path (appended live during simulation for real-time monitoring)
    actions_log_path = os.path.join(simulation_dir, "actions.jsonl")
    open(actions_log_path, "w").close()  # clear any previous log
    trace_cursor = 0  # highest trace rowid already exported

    # Initial post: brand agent publishes campaign content
    if campaign_content:
        try:
            brand_agent = env.agent_graph.get_agent(brand_agent_id)
            await env.step({brand_agent: ManualAction(
                action_type=ActionType.CREATE_POST,
                action_args={"content": campaign_content}
            )})
            print(f"Brand agent posted campaign content ({len(campaign_content)} chars)")
            trace_cursor = export_new_trace_rows(
                db_path, actions_log_path, variant_id, channel, round_num=0,
                since_rowid=trace_cursor,
            )
        except Exception as e:
            print(f"Warning: could not post initial campaign content: {e}")

    # Persona agent IDs (everyone except brand agent)
    if agent_configs:
        persona_ids = [
            c["agent_id"] for c in agent_configs
            if c.get("agent_id") != brand_agent_id
        ]
    else:
        # Fallback: skip agent 0 (brand), use all others
        total = agent_graph.graph.number_of_nodes() if hasattr(agent_graph, 'graph') else 50
        persona_ids = list(range(1, total))

    if not persona_ids:
        print("Warning: no persona agents found — check twitter_profiles.csv")
        write_status(simulation_dir, "failed", {"error": "No persona agents found"})
        await env.close()
        return False

    print(f"Running {num_rounds} rounds with {len(persona_ids)} persona agents")

    # Main simulation loop
    start_time = datetime.now()
    for round_num in range(num_rounds):
        if _shutdown_event and _shutdown_event.is_set():
            print("Shutdown requested — stopping simulation early")
            break

        # Randomly activate a subset of persona agents each round
        active_count = min(len(persona_ids), random.randint(max(1, len(persona_ids) // 3), len(persona_ids)))
        active_ids = random.sample(persona_ids, active_count)

        actions = {}
        for agent_id in active_ids:
            try:
                agent = env.agent_graph.get_agent(agent_id)
                actions[agent] = LLMAction()
            except Exception:
                pass

        if actions:
            await env.step(actions)

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"Round {round_num + 1}/{num_rounds} — {len(actions)} agents active — {elapsed:.1f}s elapsed")

        # Live export: real actions from this exact round, tagged with the
        # real round_num — replaces the old end-of-run-only, fake 5-slice
        # per_round_engagement approximation.
        trace_cursor = export_new_trace_rows(
            db_path, actions_log_path, variant_id, channel,
            round_num=round_num + 1, since_rowid=trace_cursor,
        )

        # Write round sentinel to log for live progress tracking
        write_round_sentinel(actions_log_path, round_num + 1, num_rounds)

    total_elapsed = (datetime.now() - start_time).total_seconds()
    print(f"Simulation loop done in {total_elapsed:.1f}s")

    # Reconciliation pass: catch any trailing rows not yet flushed (e.g. an
    # in-flight action at the moment of an early shutdown). Uses the same
    # cursor so nothing already exported is duplicated.
    trace_cursor = export_new_trace_rows(
        db_path, actions_log_path, variant_id, channel,
        round_num=num_rounds, since_rowid=trace_cursor,
    )
    num_actions = trace_cursor  # rowid count is a reasonable proxy for total actions exported

    # Append simulation_end sentinel
    with open(actions_log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "event_type": "simulation_end",
            "variant_id": variant_id,
            "channel": channel,
            "total_actions": num_actions,
            "timestamp": datetime.utcnow().isoformat(),
        }) + "\n")

    write_status(simulation_dir, "completed", {
        "variant_id": variant_id,
        "channel": channel,
        "total_actions": num_actions,
        "actions_log": actions_log_path,
        "elapsed_seconds": total_elapsed,
    })

    await env.close()
    print(f"Simulation complete — {num_actions} actions exported to {actions_log_path}")
    return True


async def main():
    parser = argparse.ArgumentParser(description="CampaignSim Channel Simulation")
    parser.add_argument("--config", required=True, help="Path to simulation_config.json")
    parser.add_argument("--no-wait", action="store_true", default=False,
                        help="Do not wait for IPC commands after simulation completes")
    parser.add_argument("--max-rounds", type=int, default=None,
                        help="Override num_rounds from config (for testing)")
    args = parser.parse_args()

    global _shutdown_event
    _shutdown_event = asyncio.Event()

    if not os.path.exists(args.config):
        print(f"Error: config not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    # Override num_rounds if --max-rounds is given
    if args.max_rounds is not None:
        config = load_config(args.config)
        config["num_rounds"] = args.max_rounds
        with open(args.config, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

    success = await run_simulation(args.config)
    sys.exit(0 if success else 1)


def _setup_signal_handlers():
    def handler(signum, frame):
        print(f"\nReceived signal {signum}, shutting down...")
        if _shutdown_event:
            _shutdown_event.set()
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)


if __name__ == "__main__":
    _setup_signal_handlers()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        print("Channel simulation process exited")
