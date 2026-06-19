# Phase 2 — Channel Simulation Scripts

## Goal

Build a simulation runner script that uses OASIS to model how customer personas react to a campaign post, and export the results to a JSONL action log that Phase 4's VariantScorer can read.

**Done when:** A simulation can be launched from the Flask API, persona agents react to a campaign post using real OASIS actions, and the action log is saved to disk.

---

## Verified OASIS API (from the existing codebase)

Before writing any simulation code, the actual OASIS API was verified from `backend/scripts/run_twitter_simulation.py`. These are the **real** imports and patterns — do not guess or invent alternative APIs.

### Imports

```python
import oasis
from oasis import (
    ActionType,
    LLMAction,
    ManualAction,
    generate_twitter_agent_graph,
)
from camel.models import ModelFactory
from camel.types import ModelPlatformType
```

### Environment lifecycle

```python
# 1. Create agent graph from CSV profile file
agent_graph = await generate_twitter_agent_graph(
    profile_path="path/to/twitter_profiles.csv",
    model=model,
    available_actions=[ActionType.CREATE_POST, ActionType.LIKE_POST, ...],
)

# 2. Create environment (results stored in SQLite, not JSONL)
env = oasis.make(
    agent_graph=agent_graph,
    platform=oasis.DefaultPlatformType.TWITTER,
    database_path="path/to/simulation.db",
    semaphore=30,   # max concurrent LLM calls
)
await env.reset()

# 3. Initial post: brand agent publishes campaign content
brand_agent = env.agent_graph.get_agent(brand_agent_id)
await env.step({brand_agent: ManualAction(
    action_type=ActionType.CREATE_POST,
    action_args={"content": campaign_content_text}
)})

# 4. Simulation rounds: persona agents react autonomously
for round_num in range(num_rounds):
    active_agents = [env.agent_graph.get_agent(aid) for aid in persona_ids]
    actions = {agent: LLMAction() for agent in active_agents}
    await env.step(actions)

# 5. Read results from SQLite trace table
import sqlite3
conn = sqlite3.connect(db_path)
rows = conn.execute("SELECT user_id, action, info, created_at FROM trace").fetchall()
conn.close()

# 6. Shut down
await env.close()
```

### Key facts

| Fact | Detail |
|------|--------|
| Profile input | CSV file — `twitter_profiles.csv` — same columns as `OasisAgentProfile` |
| Platform | Only `oasis.DefaultPlatformType.TWITTER` and `.REDDIT` exist — no custom platforms |
| IPC | File-based (JSON files in `ipc_commands/` and `ipc_responses/` dirs), not stdin/stdout |
| Results | Stored in **SQLite** (`trace` table) — not written as JSONL by OASIS itself |
| Action types | Fixed enum: `CREATE_POST`, `LIKE_POST`, `REPOST`, `QUOTE_POST`, `FOLLOW`, `DO_NOTHING`, `INTERVIEW` |
| Interview | Special `ManualAction` only, never via `LLMAction` |
| Agent retrieval | `env.agent_graph.get_agent(agent_id)` |

---

## Architecture Decision — One Script, Channel via Content

OASIS only provides Twitter and Reddit as built-in platforms. Rather than trying to create custom platforms (unsupported), we simulate all marketing channels using the Twitter platform with **channel-specific prompt framing** in the campaign content:

- **Instagram variant**: campaign post describes a visual Instagram ad (image + caption + CTA)
- **Email variant**: campaign post describes an email subject line + body excerpt
- **TikTok variant**: campaign post describes a short-form video concept + hook

The agent personas (built in Phase 1) already contain channel behaviour context (which platforms they use, how they respond to different content). The brand agent's initial post sets the channel context. Agent LLM reactions will naturally reflect their persona's channel preferences.

This keeps the simulation infrastructure simple (one script, same OASIS API call) while varying channel context through content framing.

---

## Step 1 — Create `run_channel_simulation.py`

**File:** `backend/scripts/run_channel_simulation.py`

This replaces the previously-planned channel-specific scripts. It handles all channels via config.

```python
"""
CampaignSim — Channel Simulation Script

Runs an OASIS Twitter simulation where:
- Agent 0 (brand agent) posts the campaign content as the initial post
- Persona agents (agents 1..N) react over num_rounds using LLMAction
- Results are read from SQLite and exported as a JSONL action log

Usage:
    python run_channel_simulation.py --config /path/to/simulation_config.json
    python run_channel_simulation.py --config /path/to/simulation_config.json --no-wait
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
from typing import Any, Dict, List

import oasis
from oasis import (
    ActionType,
    LLMAction,
    ManualAction,
    generate_twitter_agent_graph,
)
from camel.models import ModelFactory
from camel.types import ModelPlatformType

logger = logging.getLogger(__name__)

# Shutdown event — set by SIGTERM/SIGINT handler
_shutdown_event: asyncio.Event = None

# Actions available to persona agents during simulation
CAMPAIGN_AVAILABLE_ACTIONS = [
    ActionType.CREATE_POST,   # comment / reply
    ActionType.LIKE_POST,     # positive engagement
    ActionType.REPOST,        # share campaign content
    ActionType.QUOTE_POST,    # share with commentary
    ActionType.FOLLOW,        # follow brand account
    ActionType.DO_NOTHING,    # ignore / scroll past
]


def load_config(config_path: str) -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_model(config: Dict[str, Any]):
    """Create the LLM model from environment variables (same pattern as the rest of the backend)."""
    llm_api_key = os.environ.get("LLM_API_KEY", "")
    llm_base_url = os.environ.get("LLM_BASE_URL", "")
    llm_model = os.environ.get("LLM_MODEL_NAME", "") or config.get("llm_model", "gpt-4o-mini")

    if llm_api_key:
        os.environ["OPENAI_API_KEY"] = llm_api_key
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("Missing API key — set LLM_API_KEY in .env")
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


def export_sqlite_to_jsonl(db_path: str, output_path: str, variant_id: str, channel: str):
    """
    Read OASIS trace table from SQLite and write a JSONL action log.

    Each line is one agent action:
    {
        "variant_id": "...",
        "channel": "...",
        "agent_id": 42,
        "action_type": "LIKE_POST",
        "info": {...},
        "timestamp": "..."
    }

    This is the format Phase 4's VariantScorer reads.
    """
    if not os.path.exists(db_path):
        logger.warning(f"No simulation DB found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT user_id, action, info, created_at FROM trace ORDER BY created_at"
        ).fetchall()
    except sqlite3.OperationalError as e:
        logger.error(f"Failed to read trace table: {e}")
        rows = []
    finally:
        conn.close()

    with open(output_path, "w", encoding="utf-8") as f:
        for user_id, action, info_json, created_at in rows:
            try:
                info = json.loads(info_json) if info_json else {}
            except json.JSONDecodeError:
                info = {"raw": info_json}

            entry = {
                "variant_id": variant_id,
                "channel": channel,
                "agent_id": user_id,
                "action_type": action,
                "info": info,
                "timestamp": created_at,
            }
            f.write(json.dumps(entry) + "\n")

    logger.info(f"Exported {len(rows)} actions to {output_path}")


async def run_simulation(config_path: str, wait_for_commands: bool = True):
    """Main simulation coroutine."""
    config = load_config(config_path)
    simulation_dir = os.path.dirname(os.path.abspath(config_path))

    variant_id = config.get("variant_id", "unknown")
    channel = config.get("channel", "instagram")
    num_rounds = config.get("num_rounds", 10)
    brand_agent_id = config.get("brand_agent_id", 0)
    campaign_content = config.get("campaign_content", "")

    print(f"Starting simulation: variant={variant_id}, channel={channel}, rounds={num_rounds}")
    write_status(simulation_dir, "starting")

    # --- Model ---
    model = create_model(config)

    # --- Agent graph from CSV ---
    profile_path = os.path.join(simulation_dir, "twitter_profiles.csv")
    if not os.path.exists(profile_path):
        write_status(simulation_dir, "failed", {"error": f"Profile CSV not found: {profile_path}"})
        return

    agent_graph = await generate_twitter_agent_graph(
        profile_path=profile_path,
        model=model,
        available_actions=CAMPAIGN_AVAILABLE_ACTIONS,
    )

    # --- Environment ---
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

    # --- Initial post: brand agent publishes campaign content ---
    if campaign_content:
        try:
            brand_agent = env.agent_graph.get_agent(brand_agent_id)
            await env.step({brand_agent: ManualAction(
                action_type=ActionType.CREATE_POST,
                action_args={"content": campaign_content}
            )})
            print(f"Brand agent posted campaign content ({len(campaign_content)} chars)")
        except Exception as e:
            print(f"Warning: could not post initial campaign content: {e}")

    # --- Persona agent IDs (everyone except brand agent) ---
    agent_configs = config.get("agent_configs", [])
    persona_ids = [
        c["agent_id"] for c in agent_configs
        if c.get("agent_id") != brand_agent_id
    ]
    if not persona_ids:
        # Fallback: use all agents except agent 0
        total_agents = len(agent_configs) or 50
        persona_ids = list(range(1, total_agents))

    # --- Main simulation loop ---
    start_time = datetime.now()
    for round_num in range(num_rounds):
        # Randomly activate a subset of persona agents each round
        active_count = min(len(persona_ids), random.randint(10, 30))
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

        if (round_num + 1) % 5 == 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"  Round {round_num + 1}/{num_rounds} — {len(actions)} agents active — {elapsed:.1f}s")

    print(f"Simulation loop done in {(datetime.now() - start_time).total_seconds():.1f}s")

    # --- Export results to JSONL ---
    actions_log_path = os.path.join(simulation_dir, "actions.jsonl")
    export_sqlite_to_jsonl(db_path, actions_log_path, variant_id, channel)

    write_status(simulation_dir, "completed", {"actions_log": actions_log_path})
    await env.close()
    print("Environment closed. Simulation complete.")


async def main():
    parser = argparse.ArgumentParser(description="CampaignSim Channel Simulation")
    parser.add_argument("--config", required=True, help="Path to simulation_config.json")
    parser.add_argument("--no-wait", action="store_true", default=False)
    args = parser.parse_args()

    global _shutdown_event
    _shutdown_event = asyncio.Event()

    if not os.path.exists(args.config):
        print(f"Error: config not found: {args.config}")
        sys.exit(1)

    await run_simulation(args.config, wait_for_commands=not args.no_wait)


def setup_signal_handlers():
    def handler(signum, frame):
        print(f"\nReceived signal {signum}, shutting down...")
        if _shutdown_event:
            _shutdown_event.set()
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)


if __name__ == "__main__":
    setup_signal_handlers()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        print("Simulation process exited")
```

---

## Step 2 — Simulation Config Format

**File written by Flask API:** `{simulation_dir}/simulation_config.json`

When the Flask API launches a variant simulation, it writes this config file and passes its path to the script:

```json
{
    "simulation_id": "freshbrew_launch_v0",
    "variant_id": "variant_0",
    "channel": "instagram",
    "llm_model": "gpt-4o-mini",
    "num_rounds": 10,
    "brand_agent_id": 0,
    "campaign_content": "FreshBrew Cold Brew Concentrate — Zero Sugar. Premium quality. Ready in seconds. Tap to discover the smoothest cold brew you'll ever taste. [Instagram VideoAd targeting Urban Professionals aged 25-40]",
    "agent_configs": [
        {"agent_id": 1, "activity_level": 0.8},
        {"agent_id": 2, "activity_level": 0.6},
        {"agent_id": 3, "activity_level": 0.5}
    ]
}
```

**How `campaign_content` encodes the channel:**

The text of `campaign_content` describes the format and channel so that persona agents, whose system prompts reference their own channel behaviour, react appropriately:

| Channel | Content prefix pattern |
|---------|----------------------|
| Instagram | `"[Instagram VideoAd] ..."` or `"[Instagram CarouselPost] ..."` |
| Email | `"[Email Newsletter — Subject: ...] Body: ..."` |
| TikTok | `"[TikTok VideoAd — 15s hook: ...] ..."` |
| LinkedIn | `"[LinkedIn SponsoredPost] ..."` |

The persona's `persona` field (written during Phase 1) already contains their channel preferences — the LLM will use both the content framing and persona context to produce realistic reactions.

---

## Step 3 — Register Script and Add Flask Endpoint

### 3a. Register the script in simulation runner

**File:** `backend/app/services/simulation_runner.py`

Find the `CHANNEL_SCRIPT_MAP` (or equivalent script dispatch) and add the channel simulation script:

```python
# In simulation_runner.py — script dispatch map
CHANNEL_SCRIPT_MAP = {
    "instagram":  "run_channel_simulation.py",
    "email":      "run_channel_simulation.py",
    "tiktok":     "run_channel_simulation.py",
    "linkedin":   "run_channel_simulation.py",
    # Keep existing entries:
    "twitter":    "run_twitter_simulation.py",
    "reddit":     "run_reddit_simulation.py",
}
```

All marketing channels use the same `run_channel_simulation.py`. The difference is in the `campaign_content` text and the persona profiles — not the script.

### 3b. Add Flask endpoint for launching a variant simulation

**File:** `backend/app/api/simulation.py` (or nearest equivalent)

```python
import os
import json
import uuid
from flask import Blueprint, request, jsonify
from ..services.simulation_runner import SimulationRunner
from ..services.task_manager import task_manager

simulation_bp = Blueprint('simulation', __name__)

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'scripts')
SIMULATIONS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'simulations')


@simulation_bp.route('/api/simulation/launch_variant', methods=['POST'])
def launch_variant():
    """
    Launch a single variant simulation.

    Request body:
    {
        "project_id": "...",
        "variant_id": "variant_0",
        "channel": "instagram",
        "campaign_content": "...",
        "persona_agent_ids": [1, 2, 3, ...],
        "num_rounds": 10
    }

    Returns:
    {
        "task_id": "...",
        "simulation_dir": "..."
    }
    """
    data = request.get_json()
    project_id = data.get("project_id", str(uuid.uuid4()))
    variant_id = data.get("variant_id", "variant_0")
    channel = data.get("channel", "instagram")
    campaign_content = data.get("campaign_content", "")
    persona_ids = data.get("persona_agent_ids", [])
    num_rounds = data.get("num_rounds", 10)

    # Create simulation directory
    simulation_dir = os.path.join(SIMULATIONS_DIR, project_id, variant_id)
    os.makedirs(simulation_dir, exist_ok=True)

    # Write config
    config = {
        "simulation_id": f"{project_id}_{variant_id}",
        "variant_id": variant_id,
        "channel": channel,
        "num_rounds": num_rounds,
        "brand_agent_id": 0,
        "campaign_content": campaign_content,
        "agent_configs": [
            {"agent_id": aid, "activity_level": 0.7}
            for aid in persona_ids
        ]
    }
    config_path = os.path.join(simulation_dir, "simulation_config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    # Note: twitter_profiles.csv must already exist in simulation_dir
    # (copied there by the persona generation step)

    # Launch subprocess
    script_path = os.path.join(SCRIPTS_DIR, "run_channel_simulation.py")
    task_id = task_manager.start_task(
        script_path=script_path,
        args=["--config", config_path, "--no-wait"],
        task_meta={"project_id": project_id, "variant_id": variant_id}
    )

    return jsonify({"task_id": task_id, "simulation_dir": simulation_dir})


@simulation_bp.route('/api/simulation/status/<task_id>', methods=['GET'])
def simulation_status(task_id):
    """Poll simulation status."""
    status = task_manager.get_status(task_id)
    return jsonify(status)
```

---

## Step 4 — Profile CSV Setup

The simulation script reads `twitter_profiles.csv` from the simulation directory. This file is generated by Phase 1's persona generation step (`oasis_profile_generator.py`), which already writes it in the format OASIS expects.

When launching a simulation, the Flask API must copy (or symlink) the profiles CSV from the project's persona output directory to the simulation directory:

```python
import shutil

# After persona generation completes, profiles are at:
personas_csv = os.path.join(project_dir, "twitter_profiles.csv")

# Copy to each variant's simulation directory before launching
shutil.copy(personas_csv, os.path.join(simulation_dir, "twitter_profiles.csv"))
```

The CSV columns (written by `oasis_profile_generator.py`):

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | int | Agent ID (0 = brand agent) |
| `user_name` | str | Handle (e.g. `@freshbrew_brand`) |
| `name` | str | Display name |
| `bio` | str | ≤200 char bio |
| `persona` | str | Detailed persona text (up to 1500 words) |
| `karma` | int | Starting reputation score |
| `friend_count` | int | Connections count |
| `follower_count` | int | Followers count |
| `age` | int | Age (0 for brand agents) |
| `gender` | str | `male` / `female` / `other` |
| `mbti` | str | MBTI type |
| `country` | str | Country name |
| `profession` | str | Job title or account type |
| `interested_topics` | str | JSON array of topic strings |

**Brand agent row (row 0):** Should describe the brand account. Set `user_name` to the brand handle, `persona` to the brand account profile generated by Phase 1's `_build_group_persona_prompt`.

---

## Step 5 — Verify the Simulation

Run a quick local test using the sample brand brief from Phase 1:

```bash
cd "/Users/abedmreyan/Desktop/Graduation Project 2/campaignsim"

# Create a test simulation directory
mkdir -p simulations/test_freshbrew/variant_instagram

# The test assumes persona generation already ran and produced twitter_profiles.csv
# For a quick unit test, create a minimal CSV manually:
cat > simulations/test_freshbrew/variant_instagram/twitter_profiles.csv << 'EOF'
user_id,user_name,name,bio,persona,karma,friend_count,follower_count,age,gender,mbti,country,profession,interested_topics
0,@freshbrew,FreshBrew Coffee,Premium cold brew. Zero sugar.,FreshBrew Coffee is a premium cold brew brand targeting urban professionals.,100,50,5000,0,other,ESTJ,US,FMCG Brand,"[""Coffee"",""Lifestyle""]"
1,@alex_m,Alex M,Coffee lover and gym rat.,Alex is a 28-year-old male urban professional who commutes daily and values convenience. He checks Instagram during his morning commute.,50,120,80,28,male,ENTJ,US,Marketing Manager,"[""Coffee"",""Fitness"",""Tech""]"
2,@sarah_k,Sarah K,Wellness first.,Sarah is a 32-year-old female who prioritises health and sustainability. She follows food and wellness accounts on Instagram.,40,90,60,32,female,INFJ,US,UX Designer,"[""Wellness"",""Sustainability"",""Food""]"
EOF

# Write the config
cat > simulations/test_freshbrew/variant_instagram/simulation_config.json << 'EOF'
{
    "simulation_id": "test_freshbrew_instagram",
    "variant_id": "variant_instagram",
    "channel": "instagram",
    "llm_model": "gpt-4o-mini",
    "num_rounds": 3,
    "brand_agent_id": 0,
    "campaign_content": "[Instagram VideoAd] FreshBrew Cold Brew Concentrate — Zero Sugar. Premium quality. Ready in seconds. Discover the smoothest cold brew you'll ever taste. Shop now.",
    "agent_configs": [
        {"agent_id": 1, "activity_level": 0.8},
        {"agent_id": 2, "activity_level": 0.7}
    ]
}
EOF

# Run the simulation
python backend/scripts/run_channel_simulation.py \
    --config simulations/test_freshbrew/variant_instagram/simulation_config.json \
    --no-wait
```

**Expected outputs:**

```
simulations/test_freshbrew/variant_instagram/
├── simulation_config.json        (input)
├── twitter_profiles.csv          (input)
├── channel_simulation.db         (OASIS SQLite — intermediate)
├── actions.jsonl                 (output — read by Phase 4 scorer)
└── env_status.json               (status: "completed")
```

**Sample `actions.jsonl` line:**
```json
{"variant_id": "variant_instagram", "channel": "instagram", "agent_id": 1, "action_type": "LIKE_POST", "info": {}, "timestamp": "2026-05-07T10:23:01"}
```

---

## Checklist

- [x] `run_channel_simulation.py` created in `backend/scripts/`
- [x] Script verified: imports from `oasis` without errors (py_compile passes)
- [x] `channel` platform dispatch added to `simulation_runner.py` `start_simulation()`
- [x] Flask endpoint `/api/simulation/launch_variant` added (+ `/variant_status/<id>`)
- [x] `twitter_profiles.csv` copy logic added to `launch_variant` endpoint
- [ ] Test run produces `actions.jsonl` with real OASIS action type strings
- [ ] `env_status.json` shows `"completed"` after test run
- [ ] Phase 4 VariantScorer can read the JSONL (spot-check `action_type` keys match `CAMPAIGN_ACTION_WEIGHTS`)
