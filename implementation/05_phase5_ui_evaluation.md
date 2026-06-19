# Phase 5 — UI Polish, Evaluation & Thesis Deliverables

## Goal

Transform the functional prototype into a polished marketer-facing tool, conduct a user study or benchmark evaluation that validates the simulation's usefulness, and produce all required thesis deliverables.

**Done when:** The UI is self-explanatory to a non-technical marketer, the evaluation demonstrates that simulation predictions correlate with (or provide useful signal for) real marketing intuition, and all thesis chapters are supportable with data from the system.

---

## Part A — UI Polish

### A1. Landing Page Redesign

**File:** `frontend/src/views/Home.vue`

The landing page already has the marketing-focused design implemented. Polish and refine it:

```
Hero Section:
  Headline: "Test Your Campaign Before It Launches"
  Subline:  "Upload your brief. Simulate thousands of customer reactions.
             Get ranked recommendations — before spending a dollar."
  CTA:      [Start a Simulation →]

How It Works (3 icons):
  1. Upload your brief    → we extract your brand landscape
  2. We generate personas → realistic customer simulations
  3. Get recommendations  → best channel × content × segment

Use Cases:
  - New product launch
  - Channel selection
  - Creative A/B testing
  - Audience segment prioritisation

Footer:
  Built with CAMEL-AI OASIS · Zep GraphRAG · Vue 3
```

### A2. Campaign Dashboard

**New File:** `frontend/src/views/Dashboard.vue`

Replace the "History Database" view with a proper campaign dashboard:

```
┌─────────────────────────────────────────────────────┐
│  My Campaigns                          [+ New]       │
├─────────────────────────────────────────────────────┤
│  FreshBrew Cold Brew Launch                          │
│  Status: ✓ Completed  |  3 variants  |  May 2026     │
│  Top rec: VideoAd on Instagram — Millennials (34%)   │
│  [View Report]  [Clone]  [Delete]                    │
├─────────────────────────────────────────────────────┤
│  NovaTech SaaS Onboarding Email Test                 │
│  Status: ⏳ Running  |  2 variants  |  May 2026      │
│  [View Progress]                                     │
└─────────────────────────────────────────────────────┘
```

### A3. Guided Onboarding (First-Run Walkthrough)

Add a step-by-step onboarding modal that appears on first visit. Uses Vue's built-in transitions:

```
Step 1: "Welcome! Let's simulate your first campaign."
        "Start by uploading your brand brief — a PDF, Word doc, or plain text
         describing your brand, product, target audience, and competitors."
        [Upload Now]

Step 2: "We'll extract your brand landscape"
        "Our AI identifies your brand entities, customer segments, channels,
         and competitors, and builds a knowledge graph."

Step 3: "Then generate customer personas"
        "We create realistic customer agents based on your audience data.
         You can review and approve them before running simulations."

Step 4: "Design your campaign variants"
        "Define 2–3 variants (different content formats, messages, or channels)
         to compare head-to-head."

Step 5: "Get your recommendations"
        "After simulation, you'll see which variant performed best — with
         engagement scores, segment breakdowns, and strategic rationale."
```

### A4. Improve the Graph Visualisation

**File:** `frontend/src/components/GraphPanel.vue`

The existing D3.js graph visualisation works but is generic. Add:
1. **Node colour coding by entity type** — use a colour legend (Brand=blue, CustomerPersona=green, MarketingChannel=orange, Competitor=red, ContentFormat=purple)
2. **Node size by degree** — larger nodes have more connections
3. **Hover tooltip** showing node name, type, and summary from Zep

```javascript
// In GraphPanel.vue — color scale by entity type
const colorByType = {
  'Brand':            '#3B82F6',   // blue
  'CustomerPersona':  '#10B981',   // green
  'MarketingChannel': '#F59E0B',   // orange
  'Competitor':       '#EF4444',   // red
  'ContentFormat':    '#8B5CF6',   // purple
  'Campaign':         '#06B6D4',   // cyan
  'Person':           '#6B7280',   // grey
  'default':          '#9CA3AF',
}
```

### A5. Recommendation Report Visualisations

**File:** `frontend/src/views/ReportView.vue`

Add three charts to the report view using D3.js (already a dependency):

1. **Engagement Bar Chart** — one bar per variant, sorted by engagement rate
2. **Radar Chart** — per variant, show 5 dimensions: engagement, positive actions, negative actions, trend direction, agent coverage
3. **Heatmap** — segment × channel matrix, cell colour = engagement rate

---

## Part B — Evaluation

### B1. Evaluation Strategy Options

Choose ONE of these evaluation approaches for your thesis. Option 1 is the strongest academically.

#### Option 1 — Expert Validation Study (Recommended)

**What:** Recruit 5–10 marketing professionals. Show them simulation results for 2–3 fictional brands WITHOUT telling them the engagement scores. Ask them to predict which variant would perform best. Compare their predictions to the simulation rankings.

**Metric:** Agreement rate between human expert prediction and simulation ranking (top-1 and top-2 accuracy).

**Why strong:** Directly validates that the simulation captures real marketing intuition. Does not require real campaign data (which you may not have).

**Protocol:**
```
1. Create 3 fictional brand briefs (different industries: FMCG, SaaS, Fashion)
2. Run 3 variants per brand (2 channels × different content formats)
3. Show experts the campaign brief + persona profiles but NOT the scores
4. Ask: "Which variant do you think would perform best? Rank them."
5. Reveal simulation scores and compare
6. Follow-up interview: "Does this match your intuition? Where does it diverge?"
```

#### Option 2 — Internal Consistency Test

**What:** Run the same campaign brief multiple times with different random seeds / persona counts. Measure variance in the recommendation output.

**Metric:** Standard deviation of engagement scores across runs. Low variance = consistent and reliable.

**Why useful:** Easy to run without external participants. Validates the simulation is deterministic enough to be useful.

#### Option 3 — Ablation Study

**What:** Compare three versions of the system:
- Full system (knowledge graph + persona generation + simulation)  
- No knowledge graph (personas generated from plain text only)
- No LLM personas (rule-based profiles from Phase 1 fallbacks)

**Metric:** Qualitative richness of personas; user-rated usefulness of recommendations.

**Why useful:** Demonstrates that each architectural component (Zep graph, LLM persona generation) adds value.

---

### B2. Evaluation Data Collection

**File:** `backend/app/api/evaluation.py` (new file)

Add endpoints to record user study responses:

```python
@evaluation_bp.route('/record_prediction', methods=['POST'])
def record_expert_prediction():
    """
    Record a human expert's variant ranking prediction.
    {
        "study_id": "...",
        "participant_id": "...",
        "campaign_id": "...",
        "predicted_ranking": ["variant_id_1", "variant_id_2", "variant_id_3"]
    }
    """
    # Save to a study results JSON file
    ...

@evaluation_bp.route('/compare_results/<study_id>', methods=['GET'])
def compare_study_results(study_id):
    """
    Compare human predictions against simulation rankings.
    Returns agreement rates.
    """
    ...
```

---

### B3. Evaluation Metrics to Report in Thesis

| Metric | How to Measure | Target |
|--------|---------------|--------|
| Expert agreement (top-1) | % of experts who predicted the simulation's top variant | > 60% |
| Expert agreement (top-2) | % who had simulation top variant in their top 2 | > 75% |
| Simulation consistency | StdDev of engagement score across 3 runs of same brief | < 5% |
| Persona diversity | Avg pairwise cosine distance between persona embeddings | > 0.3 |
| Report usefulness | User-rated 1–5 on "Would this help you make a decision?" | > 3.5/5 |
| System latency | End-to-end time: upload → recommendation | Document actual |

---

## Part C — Thesis Chapter Support

### Chapter Mapping

| Thesis Chapter | What to Build / Document |
|---|---|
| 1. Introduction | Screenshot of landing page; problem statement from the gap between campaign testing tools |
| 2. Literature Review | OASIS paper (CAMEL-AI), GraphRAG literature, multi-agent simulation in marketing, prior campaign simulation work |
| 3. System Architecture | Architecture diagram (use the mapping table from overview doc); data flow diagram |
| 4. Implementation | Reference phases 1–4; include key code excerpts for ontology prompt, persona generator, variant scorer, report agent |
| 5. Evaluation | Results from B1 or B2; statistical analysis; discussion of limitations |
| 6. Conclusion | Business implications; academic contributions; future work |

### Architecture Diagram (for Chapter 3)

Draw this in any diagram tool (draw.io, Mermaid, Figma):

```
User
 │
 │ Upload Brief
 ▼
┌──────────────┐    LLM API    ┌────────────────────────┐
│  Flask API   │ ◄──────────► │  Marketing Ontology    │
│  (Python)    │               │  Generator             │
└──────┬───────┘               └────────────────────────┘
       │
       │ Graph Build
       ▼
┌──────────────┐    Zep Cloud  ┌────────────────────────┐
│  Knowledge   │ ◄──────────► │  Brand Landscape Graph  │
│  Graph       │               │  (Entities + Relations) │
└──────┬───────┘               └────────────────────────┘
       │
       │ Entity Extraction
       ▼
┌──────────────┐    LLM API    ┌────────────────────────┐
│  Customer    │ ◄──────────► │  Persona Generator     │
│  Personas    │               │  (OASIS profiles)      │
└──────┬───────┘               └────────────────────────┘
       │
       │ Per-Variant Subprocess
       ▼
┌──────────────┐    CAMEL-AI   ┌────────────────────────┐
│  Channel     │ ◄──────────► │  OASIS Multi-Agent     │
│  Simulation  │   OASIS       │  Social Simulation     │
│  (×N variants│               └────────────────────────┘
└──────┬───────┘
       │
       │ Action Logs
       ▼
┌──────────────┐               ┌────────────────────────┐
│  Variant     │               │  Engagement Scores     │
│  Scorer      │ ──────────►  │  per Variant           │
└──────┬───────┘               └────────────────────────┘
       │
       │ ReACT Loop
       ▼
┌──────────────┐    LLM API    ┌────────────────────────┐
│  Campaign    │ ◄──────────► │  Recommendation Report  │
│  Report Agent│               │  + Top Recommendation  │
└──────┬───────┘               └────────────────────────┘
       │
       ▼
  Vue 3 Frontend
```

---

### B4. Sample Dataset for Evaluation

Prepare 3 brand briefs representing different industries for the expert study:

**Brand 1 — FMCG (Consumer Goods)**
- FreshBrew Cold Brew Coffee (used throughout this implementation)

**Brand 2 — SaaS (B2B)**
```
Brand: Taskflow
Product: Project management software (free tier + paid upgrade)
Target: Small business owners aged 30–50, overwhelmed by complexity
Key Message: "Get organised in 10 minutes. No training required."
Campaign Goal: Free trial sign-ups
Channels to test: LinkedIn, Email
Competitors: Asana, Monday.com, Notion
Brand Voice: Friendly, simple, confident
```

**Brand 3 — Fashion / D2C**
```
Brand: Rove Studio
Product: Sustainable travel wear (new season launch)
Target: Frequent travellers aged 28–40, sustainability-conscious, premium spenders
Key Message: "Built for everywhere. Made responsibly."
Campaign Goal: Drive first purchase from Instagram discovery
Channels to test: Instagram, TikTok
Competitors: Patagonia, Allbirds, Everlane
Brand Voice: Aspirational, honest, minimal
```

---

## Checklist

### UI
- [ ] Landing page redesigned with marketing copy
- [ ] Campaign dashboard view showing campaign history
- [ ] First-run onboarding walkthrough added
- [x] Graph node colours by entity type (semantic map: Brand=blue, CustomerPersona=green, etc.)
- [x] Graph node size by degree (proportional to edge count, radius 7–17px)
- [x] Campaign Recommendation Report view (`/campaign/:campaignId/report`) — renders top rec card, variant rankings table, full markdown report
- [ ] Engagement bar chart in report view
- [ ] Heatmap (segment × channel) in report view
- [ ] Report export (Markdown) working

### Evaluation
- [ ] 3 brand briefs prepared and simulations run
- [ ] Evaluation protocol documented (participant instructions)
- [x] `/api/evaluation/record_prediction` endpoint working
- [x] `/api/evaluation/compare_results/<study_id>` endpoint working (computes top-1 and top-2 agreement rates)
- [ ] Expert predictions collected (or consistency test data gathered)
- [ ] Results tabulated and statistical summary written

### Thesis
- [ ] Architecture diagram drawn
- [ ] Key code excerpts selected for implementation chapter
- [ ] Evaluation results section written
- [ ] System limitations documented (simulation caveats)
- [ ] Future work section drafted (additional channels, real-world validation, personalisation)
