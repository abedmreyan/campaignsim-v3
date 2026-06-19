# Phase 3 — Campaign Variables & A/B Testing

## Goal

Let users define multiple campaign variants (different content types, messages, or channels) and run them as parallel simulations. The system produces side-by-side action logs that can be compared by the recommendation engine in Phase 4.

**Done when:** A user can define 2–3 campaign variants in the UI, launch all simulations in parallel, monitor progress per variant, and see the raw results (action counts) per variant when all simulations complete.

---

## Key New Concept: Campaign Variant

A campaign variant is a single combination of:
- **Content format** (e.g. VideoAd, CarouselPost, EmailNewsletter)
- **Message / creative** (headline, body, CTA, visual description)
- **Channel** (Instagram, Email, etc.)
- **Target segment** (which customer personas to include in this run)

Multiple variants for the same campaign are run in parallel. Each produces its own set of action logs. Phase 4 then scores and ranks them.

---

## Step 1 — Define the Variant Data Model

**File:** `backend/app/models/campaign.py` (new file)

```python
"""
Campaign and Variant data models.
Stored as JSON alongside the project context.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


@dataclass
class CampaignContent:
    """The creative content for a single variant."""
    format: str                  # "VideoAd", "CarouselPost", "EmailNewsletter", "SearchAd"
    headline: str
    body: str
    cta: str
    visual_desc: str = ""        # describes the visual for LLM context
    email_subject: str = ""      # only for email variants
    tone: str = "neutral"        # "professional", "playful", "urgent", "inspirational"


@dataclass
class CampaignVariant:
    """A single testable combination of content + channel + segment."""
    variant_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    variant_name: str = ""           # human label e.g. "Video on Instagram – Millennials"
    channel: str = "instagram"       # "instagram", "email", "tiktok", "linkedin"
    content: CampaignContent = None
    target_segment: str = ""         # name of persona group to include (empty = all)
    max_rounds: int = 10

    # Set after simulation runs
    simulation_id: Optional[str] = None
    status: str = "pending"          # "pending", "running", "completed", "failed"
    output_dir: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


@dataclass
class Campaign:
    """Top-level campaign. Contains multiple variants."""
    campaign_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    brand_name: str = ""
    campaign_goal: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    variants: List[CampaignVariant] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d
```

---

## Step 2 — Create the Variant Runner

**File:** `backend/app/services/variant_runner.py` (new file)

This service launches all variants of a campaign in parallel using the existing `SimulationRunner` infrastructure. Each variant gets its own subprocess and its own output directory.

```python
"""
CampaignSim Variant Runner

Launches multiple simulation variants in parallel.
Each variant runs on a separate channel/content/segment combination.
"""

import concurrent.futures
import logging
import os
import uuid
from typing import List, Dict, Any, Callable, Optional

from ..models.campaign import Campaign, CampaignVariant
from ..services.simulation_runner import SimulationRunner
from ..services.simulation_config_generator import SimulationConfigGenerator
from ..config import Config

logger = logging.getLogger(__name__)


class VariantRunner:
    """
    Runs multiple campaign variants in parallel.
    
    Uses the existing SimulationRunner for each variant — no changes to
    the subprocess/IPC infrastructure needed.
    """

    def __init__(self):
        self.runner = SimulationRunner()

    def run_campaign(
        self,
        campaign: Campaign,
        profiles_by_segment: Dict[str, str],    # segment_name → path to personas JSON
        progress_callback: Optional[Callable] = None,
    ) -> Campaign:
        """
        Launch all variants of a campaign in parallel.

        Args:
            campaign: Campaign object with variants defined
            profiles_by_segment: maps segment name to the path of its personas JSON file.
                                  Use empty string key "" for "all personas".
            progress_callback: called with (variant_id, status, message) on updates

        Returns:
            Updated Campaign object with simulation_ids and output_dirs filled in
        """
        base_output_dir = Config.OASIS_SIMULATION_DATA_DIR

        def run_single_variant(variant: CampaignVariant) -> CampaignVariant:
            """Run one variant. Called in a thread pool."""
            sim_id = str(uuid.uuid4())
            variant.simulation_id = sim_id
            variant.status = "running"
            variant.output_dir = os.path.join(base_output_dir, sim_id, variant.channel)

            if progress_callback:
                progress_callback(variant.variant_id, "running", f"Starting {variant.variant_name}")

            # Resolve profiles path
            profiles_path = profiles_by_segment.get(
                variant.target_segment,
                profiles_by_segment.get("", "")   # fallback to all-personas file
            )
            if not profiles_path or not os.path.exists(profiles_path):
                variant.status = "failed"
                logger.error(f"Variant {variant.variant_id}: profiles not found at {profiles_path}")
                return variant

            # Generate simulation config JSON
            config_gen = SimulationConfigGenerator()
            sim_config = config_gen.generate_config(
                simulation_id=sim_id,
                channel=variant.channel,
                max_rounds=variant.max_rounds,
                profiles_path=profiles_path,
                output_dir=variant.output_dir,
                campaign={
                    "brand_name":     campaign.brand_name,
                    "campaign_goal":  campaign.campaign_goal,
                    "target_segment": variant.target_segment,
                },
                campaign_content={
                    "headline":      variant.content.headline,
                    "body":          variant.content.body,
                    "cta":           variant.content.cta,
                    "format":        variant.content.format,
                    "visual_desc":   variant.content.visual_desc,
                    "email_subject": variant.content.email_subject,
                    "tone":          variant.content.tone,
                },
            )

            # Launch subprocess via existing SimulationRunner
            try:
                self.runner.run(
                    simulation_id=sim_id,
                    channel=variant.channel,
                    config=sim_config,
                )
                variant.status = "completed"
                if progress_callback:
                    progress_callback(variant.variant_id, "completed", f"Completed {variant.variant_name}")
            except Exception as e:
                variant.status = "failed"
                logger.error(f"Variant {variant.variant_id} failed: {e}")
                if progress_callback:
                    progress_callback(variant.variant_id, "failed", str(e))

            return variant

        # Run all variants in parallel (one thread per variant)
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(campaign.variants)) as executor:
            futures = {
                executor.submit(run_single_variant, v): v
                for v in campaign.variants
            }
            for future in concurrent.futures.as_completed(futures):
                variant = futures[future]
                try:
                    updated = future.result()
                    # Update the variant in the campaign object in-place
                    for i, v in enumerate(campaign.variants):
                        if v.variant_id == updated.variant_id:
                            campaign.variants[i] = updated
                            break
                except Exception as e:
                    logger.error(f"Thread error for variant {variant.variant_id}: {e}")

        return campaign
```

---

## Step 3 — Add the A/B API Endpoint

**File:** `backend/app/api/simulation.py`

Add a new endpoint `/api/simulation/ab_test` that accepts a campaign with multiple variants:

```python
@simulation_bp.route('/ab_test', methods=['POST'])
def start_ab_test():
    """
    Start a multi-variant A/B simulation.

    Request body:
    {
        "project_id": "...",
        "brand_name": "FreshBrew Coffee",
        "campaign_goal": "Drive trial purchase",
        "variants": [
            {
                "variant_name": "Video on Instagram — Millennials",
                "channel": "instagram",
                "target_segment": "MillennialProfessionals",
                "content": {
                    "format": "VideoAd",
                    "headline": "Zero Sugar. Zero Wait.",
                    "body": "Our cold brew concentrate is ready in 30 seconds.",
                    "cta": "Try it — 20% off",
                    "visual_desc": "Fast-paced barista montage, upbeat music",
                    "tone": "playful"
                },
                "max_rounds": 10
            },
            {
                "variant_name": "Carousel on Instagram — Gen Z",
                "channel": "instagram",
                "target_segment": "GenZConsumers",
                "content": {
                    "format": "CarouselPost",
                    "headline": "The coffee that matches your pace.",
                    "body": "Swipe to see 5 ways to drink FreshBrew.",
                    "cta": "Shop now",
                    "visual_desc": "Bold colours, meme-adjacent captions",
                    "tone": "playful"
                },
                "max_rounds": 10
            },
            {
                "variant_name": "Email — All segments",
                "channel": "email",
                "target_segment": "",
                "content": {
                    "format": "EmailNewsletter",
                    "headline": "Introducing FreshBrew Cold Brew Concentrate",
                    "body": "Premium cold brew. Zero sugar. Ready in 30 seconds.",
                    "cta": "Get 20% off your first order",
                    "email_subject": "Your mornings just got better ☕",
                    "tone": "professional"
                },
                "max_rounds": 10
            }
        ]
    }

    Returns:
    {
        "task_id": "...",
        "campaign_id": "...",
        "variants": [
            {"variant_id": "abc123", "variant_name": "...", "status": "pending"}
        ]
    }
    """
    from ..models.campaign import Campaign, CampaignVariant, CampaignContent
    from ..services.variant_runner import VariantRunner
    from ..models.task import TaskManager

    data = request.json
    project_id = data.get("project_id")

    # Build Campaign object from request
    campaign = Campaign(
        brand_name=data["brand_name"],
        campaign_goal=data["campaign_goal"],
    )

    for v_data in data.get("variants", []):
        content_data = v_data.get("content", {})
        variant = CampaignVariant(
            variant_name=v_data.get("variant_name", "Variant"),
            channel=v_data.get("channel", "instagram"),
            target_segment=v_data.get("target_segment", ""),
            max_rounds=v_data.get("max_rounds", 10),
            content=CampaignContent(
                format=content_data.get("format", "CarouselPost"),
                headline=content_data.get("headline", ""),
                body=content_data.get("body", ""),
                cta=content_data.get("cta", ""),
                visual_desc=content_data.get("visual_desc", ""),
                email_subject=content_data.get("email_subject", ""),
                tone=content_data.get("tone", "neutral"),
            ),
        )
        campaign.variants.append(variant)

    # Retrieve profiles paths from project context
    project = ProjectManager.get(project_id)
    profiles_by_segment = project.get("profiles_by_segment", {"": project.get("profiles_path")})

    # Launch async task
    task_id = TaskManager.create_task("ab_test", campaign.campaign_id)
    
    def run_in_background():
        runner = VariantRunner()
        runner.run_campaign(
            campaign=campaign,
            profiles_by_segment=profiles_by_segment,
            progress_callback=lambda vid, status, msg: TaskManager.update_progress(
                task_id, f"Variant {vid}: {msg}"
            )
        )
        # Save campaign results to project context
        ProjectManager.update(project_id, {"campaign": campaign.to_dict()})
        TaskManager.complete_task(task_id, {"campaign_id": campaign.campaign_id})

    import threading
    threading.Thread(target=run_in_background, daemon=True).start()

    return jsonify({
        "task_id": task_id,
        "campaign_id": campaign.campaign_id,
        "variants": [
            {"variant_id": v.variant_id, "variant_name": v.variant_name, "status": v.status}
            for v in campaign.variants
        ]
    })
```

---

## Step 4 — Add Segment-Filtered Persona Generation

During persona generation (Step 3 of the workflow), users should be able to tag each generated persona with a segment name. Then when launching variants, the variant can specify `target_segment` to only include personas from that group.

**File:** `backend/app/services/oasis_profile_generator.py`

After profile generation, add a segment-assignment step:

```python
def assign_segments(
    self,
    profiles: List[OasisAgentProfile],
    segment_definitions: List[Dict[str, Any]],
) -> Dict[str, List[OasisAgentProfile]]:
    """
    Assign personas to named segments using LLM classification.

    Args:
        profiles: all generated personas
        segment_definitions: list of {"name": "...", "description": "..."}
            e.g. [
                {"name": "MillennialProfessionals", "description": "Age 28-38, urban, high income"},
                {"name": "GenZConsumers", "description": "Age 18-26, digital natives, price-conscious"},
            ]

    Returns:
        dict mapping segment_name → list of matching personas
    """
    segments: Dict[str, List] = {s["name"]: [] for s in segment_definitions}
    segments["Unassigned"] = []

    for profile in profiles:
        prompt = f"""You are a marketing segmentation assistant.

Persona:
- Name: {profile.name}
- Age: {profile.age}
- Profession: {profile.profession}
- Bio: {profile.bio}
- Interested topics: {profile.interested_topics}

Available segments:
{chr(10).join(f'- {s["name"]}: {s["description"]}' for s in segment_definitions)}

Which segment best fits this persona? Reply with ONLY the segment name, exactly as listed.
If none fit well, reply "Unassigned"."""

        try:
            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=50,
            )
            segment_name = resp.choices[0].message.content.strip()
            if segment_name in segments:
                segments[segment_name].append(profile)
            else:
                segments["Unassigned"].append(profile)
        except Exception as e:
            logger.warning(f"Segment assignment failed for {profile.name}: {e}")
            segments["Unassigned"].append(profile)

    return segments
```

**File:** `backend/app/api/simulation.py`

Add an endpoint to trigger segment assignment and save each segment's personas file:

```python
@simulation_bp.route('/assign_segments', methods=['POST'])
def assign_segments():
    """
    Assign generated personas to named segments.
    Saves a separate profiles JSON file per segment under the project uploads directory.
    
    Request: { "project_id": "...", "segments": [{"name": "...", "description": "..."}] }
    Returns: { "task_id": "...", "segments": {"SegmentName": count, ...} }
    """
    # ... implementation ...
```

---

## Step 5 — Campaign Variables UI

**File:** `frontend/src/components/Step3Simulation.vue`

Replace the simple "start simulation" form with a variant builder:

```
┌─────────────────────────────────────────────────────┐
│  Campaign Setup                                      │
│  Brand: FreshBrew Coffee                             │
│  Goal: Drive trial purchase                          │
├─────────────────────────────────────────────────────┤
│  Variants                              [+ Add Variant] │
│                                                      │
│  ┌── Variant 1 ──────────────────────────────────┐  │
│  │  Name: [Video on Instagram — Millennials     ] │  │
│  │  Channel: [Instagram ▼]  Segment: [Millennials ▼] │
│  │  Format:  [VideoAd ▼]    Tone: [Playful ▼]   │  │
│  │  Headline: [___________________________________] │
│  │  Body:     [___________________________________] │
│  │  CTA:      [___________________________________] │
│  │  Visual:   [___________________________________] │
│  └───────────────────────────────────────────────┘  │
│                                                      │
│  ┌── Variant 2 ──────────────────────────────────┐  │
│  │  ...                                           │  │
│  └───────────────────────────────────────────────┘  │
│                                                      │
│  Simulation rounds per variant: [10]                 │
│                                                      │
│  [▶ Run All Variants]                                │
└─────────────────────────────────────────────────────┘
```

Vue component structure:

```vue
<script setup>
import { ref } from 'vue'
import { startABTest } from '../api/simulation.js'

const variants = ref([
  {
    variant_name: '',
    channel: 'instagram',
    target_segment: '',
    max_rounds: 10,
    content: {
      format: 'CarouselPost',
      headline: '',
      body: '',
      cta: '',
      visual_desc: '',
      email_subject: '',
      tone: 'neutral',
    }
  }
])

function addVariant() {
  variants.value.push({ ...variants.value[0], variant_name: '' })
}

async function runAll() {
  const resp = await startABTest({
    project_id: props.projectId,
    brand_name: props.brandName,
    campaign_goal: props.campaignGoal,
    variants: variants.value,
  })
  emit('simulation-started', resp.data)
}
</script>
```

---

## Step 6 — Real-Time Progress Dashboard

**File:** `frontend/src/views/SimulationRunView.vue`

Update the existing simulation run view to show per-variant progress cards instead of a single progress bar:

```
┌─────────────────────────────────────────────────────┐
│  Running Campaign Simulation                         │
├─────────────────────────────────────────────────────┤
│  Variant 1: Video on Instagram — Millennials         │
│  [████████░░░░░░] Round 8 / 10    Status: Running   │
│                                                      │
│  Variant 2: Carousel on Instagram — Gen Z            │
│  [██████████████] Round 10 / 10   Status: ✓ Done    │
│                                                      │
│  Variant 3: Email — All segments                     │
│  [████░░░░░░░░░░] Round 4 / 10    Status: Running   │
├─────────────────────────────────────────────────────┤
│  Overall: 2 / 3 variants complete                    │
│  [View Recommendations ▶]  (active when all done)   │
└─────────────────────────────────────────────────────┘
```

Poll the `/api/simulation/ab_status/<campaign_id>` endpoint every 5 seconds and update the cards.

---

## Checklist

- [x] `backend/app/models/campaign.py` created with `Campaign`, `CampaignVariant`, `CampaignContent`
- [x] `backend/app/services/variant_runner.py` created
- [x] `/api/simulation/ab_test` POST endpoint added
- [x] `/api/simulation/ab_status/<campaign_id>` GET endpoint added
- [x] `assign_segments` method added to `OasisProfileGenerator` (batched LLM classification)
- [x] `/api/simulation/assign_segments` POST endpoint added
- [x] Segment persona files saved per segment under uploads/simulations/{sim_id}/
- [ ] Variant builder UI component built (deferred — UI phase)
- [ ] Multi-variant progress dashboard built (deferred — UI phase)
- [ ] End-to-end test: 2 variants run in parallel, both produce action logs
