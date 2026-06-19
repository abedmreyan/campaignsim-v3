# CampaignSim — Testing & Evaluation Plan

**Status:** Draft  
**Last updated:** 2026-06-04  
**Purpose:** Reference document for thesis validation chapter and project discussion demo.

---

## 1. Dataset Decision

### Why UCI Bank Marketing Dataset Was Rejected

The UCI Bank Marketing dataset (Portuguese bank, 45k rows, phone telemarketing) was the first candidate considered. It was rejected because:

- **Domain mismatch** — telemarketing calls ≠ social media content campaigns. The ground-truth signals (call duration, job type, marital status → subscription Y/N) don't map to any metric CampaignSim produces.
- **No campaign content dimension** — the dataset has no ad copy, no creative, no channel. CampaignSim's core thesis is that *content* and *knowledge graph relationships* drive campaign outcomes. A dataset with no content column can't validate that.
- **Metric incompatibility** — click-through rate, engagement rate, and persona resonance scores can't be derived from a phone call outcome column.

### Better Dataset Options

| Option | Why It Fits | Source |
|---|---|---|
| Facebook/Meta Ad Performance (Kaggle) | Real spend, impressions, clicks, CTR by audience segment | Kaggle — search "Facebook Ad Performance" |
| Social Media Advertising Dataset (Kaggle, ~600k rows) | Multi-platform campaigns with engagement signals | Kaggle — `sakshigoyal7/social-media-advertising` |
| Synthetic controlled scenario | Full control over ground truth; easiest to match to KG structure | Generated internally |
| Documented real brand case study | Gives a concrete reference point; shows real-world relevance | Published marketing research papers |

**Recommended path for thesis:** Use a synthetic controlled scenario for the ablation study (see §3), and reference a real Kaggle dataset to anchor the persona/segment design to realistic distributions.

---

## 2. Evaluation Structure (6 Layers)

### Layer 1 — Sanity Tests (System Correctness)

Verify the pipeline runs end-to-end without errors across normal and edge-case inputs.

- Upload a valid graph → simulation runs → report generates (happy path)
- Upload malformed data → error is caught and surfaced clearly
- Concurrent simulations don't corrupt each other's state
- Stop simulation mid-run → state cleaned up correctly

**Pass criteria:** All happy-path tests green; error cases return structured error responses, not stack traces.

### Layer 2 — Knowledge Graph Precision / Recall

Validate that the KG construction step accurately captures the relationships in the input data.

- **Precision:** Of all edges added to the KG, what fraction are semantically correct?
- **Recall:** Of all real relationships that should exist, what fraction did the KG capture?
- **Method:** Manually annotate a small gold-standard graph (30–50 nodes) and compare against the system's output.

**Target:** Precision ≥ 0.80, Recall ≥ 0.70 on the gold-standard set.

### Layer 3 — Persona Diversity

Verify that generated personas span the intended demographic/psychographic space and don't collapse into a single archetype.

- Compute pairwise cosine distance between persona embeddings
- Check that personas cluster into ≥ N distinct groups (N = number of segments requested)
- Verify no two personas share an identical attribute vector

**Target:** Mean pairwise distance > 0.3; no duplicate personas.

### Layer 4 — Simulation Consistency

Run the same scenario twice with the same seed and verify results are deterministic. Then vary one input at a time and verify outputs change in the expected direction.

- Same input + same seed → identical output (determinism)
- Higher budget → higher reach (monotonicity)
- Broader audience → lower resonance per persona (dilution effect)
- Remove KG → engagement scores flatten toward baseline (KG contribution check)

**Pass criteria:** Determinism holds 100%; monotonicity holds for budget/reach in ≥ 90% of test cases.

### Layer 5 — Ablation Study (Strongest Academic Contribution)

This is the core academic validation. Compare three system configurations:

| Configuration | Description |
|---|---|
| **Full pipeline** | KG + multi-persona + LLM scoring |
| **No KG** | personas generated without knowledge graph; LLM scores without relationship context |
| **Reduced personas** | Full KG, but only 1 persona per segment instead of N |

Run each configuration on the same 3–5 campaign scenarios. Compare:
- Engagement score distributions
- Inter-segment variance (does removing the KG collapse all segments toward a mean score?)
- Report coherence (subjective, Likert-rated by evaluators)

**Expected finding:** Full pipeline produces higher inter-segment variance (the KG differentiates personas) and richer, more specific report language.

**Why this is strong:** Ablation studies are the standard way to attribute performance to architectural decisions in systems research. It directly answers "what does the KG actually add?"

### Layer 6 — Expert Likert Review

Have 3–5 reviewers (advisor, a marketing professional if available, peers) rate the system's outputs on a 5-point Likert scale across:

1. Persona realism ("These personas feel like real audience segments")
2. Report usefulness ("I could act on the recommendations in this report")
3. Campaign insight depth ("This analysis goes beyond surface-level observations")
4. Overall credibility ("I trust this system's outputs")

**Target:** Mean score ≥ 3.5/5.0 across all dimensions.

---

## 3. Ablation Study — Detailed Design

### Scenarios to Run

Design 3–5 controlled campaign scenarios. Each scenario should have:

- A defined product/brand (e.g., a fitness app, a sustainable fashion brand, a fintech startup)
- A target demographic (e.g., 18–25 urban women interested in wellness)
- A campaign objective (awareness vs. conversion vs. engagement)
- 2–3 ad copy variants

### Metrics to Collect Per Variant

- Predicted engagement rate per persona segment
- Inter-segment score variance (σ²)
- KG node activation count (how many KG relationships were consulted)
- Report word count and specificity score (can be approximated by unique noun count)

### Statistical Analysis

- Run each configuration 3× with different random seeds
- Report mean ± std for each metric
- Run a simple t-test or Mann-Whitney U between Full Pipeline vs. No KG on engagement variance

---

## 4. Demo Strategy (Project Discussion)

### Three-Phase Demo Structure

**Phase 1 — Data Input (2 min)**  
Upload a pre-prepared graph file. Walk through what the nodes and edges represent. Explain the KG construction step.

**Phase 2 — Simulation Run (3 min)**  
Trigger a simulation live. Show the real-time status indicator. If timing is a concern, pre-run the simulation and skip directly to results.

**Phase 3 — Report & Insights (5 min)**  
Walk through the generated report. Point to specific persona segments and explain how the KG relationships influenced their scores. Show the ablation comparison slide (full vs. no-KG output side by side).

### Fallback Plan

- If the live backend is unavailable: switch to the v2 frontend with `VITE_USE_MOCKS=false` toggled to `true` (mock mode) — the UI remains fully functional.
- Have screenshots of 2–3 completed simulation reports printed or in a slide deck as a last resort.
- Pre-record a 3-minute screen capture of a clean end-to-end run as insurance.

### Talking Points for "Why Not Just Use Existing Tools?"

- Existing tools (Google Ads planner, HubSpot analytics) work *after* campaigns run — they don't simulate before launch.
- CampaignSim's KG encodes *why* audiences respond, not just *that* they responded.
- The persona generation step lets marketers explore segments they haven't targeted yet.

---

## 5. Advisor Feedback Summary

The advisor reviewed the evaluation approach and recommended:

1. **Drop the UCI dataset** — domain mismatch makes any validation against it misleading.
2. **Prioritize ablation over ground-truth comparison** — there is no universally accepted ground truth for "good" campaign simulation; ablation directly attributes performance to architectural choices.
3. **Component-level validation is more defensible than end-to-end comparison** — evaluating each layer (KG, personas, simulation, report) separately makes it easier to identify where the system adds value.
4. **Expert Likert review adds credibility** — a quantitative-only evaluation looks thin for a systems thesis; Likert ratings from domain-knowledgeable reviewers strengthen the human validation story.
5. **Synthetic controlled scenarios are fine** — the thesis isn't claiming to predict real campaign outcomes; it's claiming the simulation is internally consistent and produces meaningful differentiation. Controlled synthetic inputs make that claim easier to support.

---

## 6. Next Steps (When You Return to This)

- [ ] Pick 3 campaign scenarios and write them up as structured inputs
- [ ] Define the gold-standard KG for Layer 2 (precision/recall) — 30–50 nodes
- [ ] Run ablation study (requires backend running with all three configurations)
- [ ] Recruit 3 expert reviewers for Likert evaluation
- [ ] Add evaluation section to thesis draft referencing this plan
- [ ] Prepare demo script and pre-recorded backup video
