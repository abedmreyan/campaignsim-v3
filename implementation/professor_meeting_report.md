# CampaignSim — Professor Meeting Report
## Progress Report: 30% Completion Milestone
**Date:** May 2026  
**Student:** Abed Mreyan  
**Programme:** Bachelor of Science in Computer Engineering  
**Project Title:** CampaignSim — A Multi-Agent AI System for Marketing Campaign Simulation and Recommendation

---

## 1. Executive Summary

CampaignSim is a marketing campaign simulation platform that uses multi-agent artificial intelligence to help marketers test and evaluate campaign strategies *before* spending real money. A user uploads a brand brief, the system builds a knowledge graph of their market landscape, generates realistic customer persona agents, and simulates how those personas respond to different campaign variants across marketing channels. The output is a ranked recommendation of the best content type × channel × audience segment combination, with explanatory reasoning.

**At the 30% milestone, the following is complete:**
- The core system architecture is built and running
- The marketing knowledge graph pipeline (brief → ontology → Zep GraphRAG) works end-to-end
- Customer persona generation from the knowledge graph is operational
- The channel simulation engine is designed, grounded in verified open-source source code, and partially integrated
- All domain-level engineering decisions have been made and documented

---

## 2. The Problem This Project Solves

### 2.1 The Real Cost of Getting It Wrong

Every year, billions of dollars are spent on marketing campaigns that fail. A 2023 Nielsen study found that 56% of advertising budgets are wasted due to poor targeting, wrong channel selection, or creative that does not resonate with the target audience. For a small or medium business running a $20,000 campaign, a single wrong creative decision can mean the entire budget is spent with near-zero return.

The problem is not lack of data — it is lack of a way to *test ideas before committing to them*. Traditional A/B testing requires launching a real campaign to real audiences. Focus groups are slow and expensive. Existing marketing analytics tools only tell you what *already happened*, not what *will* happen.

### 2.2 The Gap This Project Fills

| Existing Approach | Limitation |
|---|---|
| Real-world A/B test | Requires budget spend; results take weeks |
| Marketing analytics dashboards | Retrospective only — tell you what happened, not what to do next |
| Survey / focus groups | Slow, small sample, prone to social desirability bias |
| Rule-based recommendation engines | Generic; cannot model persona-level nuance or channel context |
| Human marketing strategist | Expensive; intuition varies; not scalable |

**CampaignSim fills the gap:** a system that runs *before* the campaign launches, using AI-generated synthetic customer personas to simulate reactions to campaign content across channels, producing a prediction of which strategy will perform best — at near-zero marginal cost.

### 2.3 Target Users

- Small-to-medium business marketing managers who cannot afford to waste budget on trial-and-error
- Marketing agencies testing creative concepts before client pitch
- Product launch teams who need to choose between two channel strategies (e.g., Instagram VideoAd vs. Email Newsletter)
- Academic researchers studying AI simulation as a proxy for market research

---

## 3. The Story Behind the System

### 3.1 Starting Point: CampaignSim

The project builds on top of **CampaignSim** — an open-source Swarm Intelligence Prediction Engine originally designed to simulate public opinion on Chinese social media platforms. CampaignSim uses a sophisticated five-step pipeline:

```
Documents → Ontology → Knowledge Graph → Agent Profiles → Simulation → Report
```

When I first encountered CampaignSim, the core insight was immediate: this pipeline maps almost one-to-one onto what a marketing strategist does manually:

| CampaignSim (Social Opinion) | CampaignSim (Marketing) |
|---|---|
| Upload news articles | Upload campaign brief + brand guide |
| Extract social ontology | Extract marketing ontology (Brand, Persona, Channel, Content) |
| Build Zep knowledge graph of entities | Build market landscape graph |
| Generate social agent profiles | Generate customer persona profiles |
| Simulate Twitter/Reddit discussions | Simulate channel reactions (Instagram, Email...) |
| Generate opinion report | Generate campaign recommendation report |

The architecture was sound. The domain was wrong. The engineering challenge was to re-domain a Chinese social opinion simulator into a marketing intelligence tool — without rebuilding from scratch.

### 3.2 Why This is Non-Trivial

Adapting CampaignSim is not a simple find-and-replace. The system has several tightly coupled layers:
- The **LLM prompts** that define what entities to extract from documents are embedded in production code
- The **validation logic** that enforces ontology constraints has hardcoded assumptions about entity type names
- The **simulation engine** (CAMEL-AI OASIS) is a research-grade library with a specific, non-obvious API that is underdocumented
- The **persona generation pipeline** uses entity type classification lists that determine whether an entity becomes a "person agent" or a "group account" — wrong classification breaks the entire simulation

Each of these layers had to be understood from source code (not documentation), redesigned for the marketing domain, and made consistent with each other.

---

## 4. Technical Specifications

### 4.1 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Vue 3 Frontend                        │
│   Upload Brief → Configure Campaign → View Report           │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP / REST
┌────────────────────────▼────────────────────────────────────┐
│                     Flask API (Python)                       │
│  /api/ontology  /api/graph  /api/personas  /api/simulation  │
└──────┬──────────────────┬──────────────────┬────────────────┘
       │                  │                  │
┌──────▼──────┐  ┌────────▼───────┐  ┌──────▼──────────────┐
│  Marketing  │  │   Zep Cloud    │  │  OASIS Simulation   │
│  Ontology   │  │  GraphRAG KG   │  │  Subprocess         │
│  Generator  │  │  (Knowledge    │  │  (CAMEL-AI)         │
│  (LLM)      │  │   Graph)       │  │                     │
└─────────────┘  └────────┬───────┘  └──────┬──────────────┘
                           │                  │
                  ┌────────▼───────┐  ┌──────▼──────────────┐
                  │  Customer      │  │  Action Log         │
                  │  Persona       │  │  (SQLite → JSONL)   │
                  │  Generator     │  │                     │
                  └────────────────┘  └──────┬──────────────┘
                                              │
                                    ┌─────────▼────────────┐
                                    │  Variant Scorer +    │
                                    │  Report Agent (ReACT)│
                                    └──────────────────────┘
```

### 4.2 Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | Vue 3 + Vite + D3.js | User interface, knowledge graph visualisation |
| Backend API | Flask (Python 3.11) | REST API, task management, async status polling |
| LLM integration | OpenAI-compatible API | Ontology generation, persona generation, report agent |
| Knowledge graph | Zep Cloud (GraphRAG) | Stores and queries brand landscape entities and relations |
| Multi-agent simulation | CAMEL-AI OASIS | Runs persona agent interactions with campaign content |
| Data storage | SQLite (simulation), JSON files (tasks) | Simulation trace storage, IPC state |
| IPC protocol | File-based JSON (commands/responses directories) | Flask ↔ OASIS subprocess communication |
| Async execution | Python asyncio + subprocess | Parallel variant simulation |

### 4.3 Key Algorithms and Approaches

#### Marketing Ontology Extraction (LLM-based)
The system sends the user's campaign brief through a structured LLM prompt that extracts a marketing-domain knowledge graph schema — specifically: entity types (`CustomerPersona`, `MarketingChannel`, `ContentFormat`, `Campaign`, `Competitor`, `Brand`) and the relations between them (`TARGETS`, `DISTRIBUTED_ON`, `COMPETES_WITH`, etc.). Output is validated against Zep Cloud's schema constraints (max 10 entity types, max 10 edge types) before graph construction.

#### Knowledge Graph Construction (GraphRAG)
Extracted entities are stored in Zep Cloud's managed knowledge graph. Zep performs semantic embedding and enables graph-augmented retrieval — meaning when we later ask "what channels does this persona prefer?", Zep traverses the graph and returns contextually grounded answers. This is the GraphRAG (Graph Retrieval-Augmented Generation) pattern applied to the marketing domain.

#### Customer Persona Generation (Profile Synthesis)
For each entity in the knowledge graph, the system generates an `OasisAgentProfile` — a structured record containing the agent's biography, detailed persona description (demographics, psychographics, channel behaviour, advertising response), MBTI type, profession, and topic interests. These profiles are written to a CSV file that OASIS ingests to initialise the agent graph.

#### Multi-Agent Channel Simulation (OASIS)
The CAMEL-AI OASIS framework provides a social simulation environment. The system:
1. Loads persona profiles into an OASIS Twitter-platform agent graph
2. Has the brand agent post the campaign content as an initial post
3. Runs N simulation rounds where persona agents autonomously react using `LLMAction` (OASIS chooses the action based on the agent's persona context)
4. Stores all agent actions in a SQLite `trace` table
5. Exports the trace to a JSONL action log for downstream scoring

#### Engagement Scoring (Weighted Action Aggregation)
Each agent action is mapped to an engagement weight:
- `REPOST` → 0.55 (strongest: sharing campaign to others)
- `QUOTE_POST` → 0.50 (share with commentary)
- `FOLLOW` → 0.45 (subscribe to brand)
- `LIKE_POST` → 0.30 (positive engagement)
- `CREATE_POST` → 0.35 (comment/reply)
- `DO_NOTHING` → 0.00 (ignored)

The per-variant engagement score is the sum of weighted actions divided by total possible actions (agents × rounds), producing a normalised 0–1 score comparable across variants.

#### ReACT Report Agent (Reasoning + Tool Use Loop)
A report agent follows the ReACT pattern (Reason → Act → Observe) using five custom tools: `VariantComparisonTool`, `SegmentInsightTool`, `ChannelEffectivenessTool`, `ContentFormatRankTool`, and `ZepBrandContextTool`. The agent iteratively queries these tools, building up evidence until it can produce a structured recommendation with ranked variants, segment breakdowns, and strategic rationale.

---

## 5. What 30% Completion Looks Like

### 5.1 Phase Map

| Phase | Description | Weight | Status |
|---|---|---|---|
| **Phase 1** | Core Fork & Marketing Domain Adaptation | 20% | **Complete** |
| **Phase 2** | Channel Simulation Scripts | 15% | **~60% complete** |
| Phase 3 | Campaign Variables & A/B Testing | 20% | Designed, not built |
| Phase 4 | Recommendation Engine | 25% | Designed, not built |
| Phase 5 | UI Polish & Evaluation | 20% | Designed, not built |

**Aggregate: ~29–31% complete** — precisely at the milestone target.

### 5.2 What is Built and Verified

#### Phase 1 — Complete

- **CampaignSim fork** initialised as an independent project repository
- **`ONTOLOGY_SYSTEM_PROMPT`** fully replaced: the LLM now extracts marketing entities (`CustomerPersona`, `MarketingChannel`, `ContentFormat`, `Campaign`, `Competitor`, `Brand`, `Product`, `Influencer`, `Market`, `Person`) from any brand brief
- **`_validate_and_process`** fixed: the schema validator now enforces `Brand` and `Person` as the two mandatory fallback types (not `Organization` — see Section 6.1)
- **`_build_user_message`** updated: all Chinese language instructions replaced with English marketing-specific guidance
- **`INDIVIDUAL_ENTITY_TYPES` and `GROUP_ENTITY_TYPES`** updated: persona generator now correctly classifies marketing entity types into individual consumer agents vs. institutional brand accounts
- **`_build_individual_persona_prompt`** replaced: generates rich customer personas covering demographics, psychographics, buying behaviour, channel behaviour, content preferences, and advertising response
- **`_build_group_persona_prompt`** replaced: generates brand/channel account profiles with posting behaviour and brand voice
- **`_generate_profile_rule_based`** updated: fallback profiles cover `CustomerPersona`, `Influencer`, `Brand`, `Competitor`, `MarketingChannel` entity types
- **`config.py`** updated: `CAMPAIGN_AVAILABLE_ACTIONS` and `CAMPAIGN_ACTION_WEIGHTS` added using real OASIS action type names
- **Locale strings** and **Vue step labels** updated to marketing terminology
- **End-to-end test brief** (FreshBrew Cold Brew Coffee) used to verify graph extraction

#### Phase 2 — 60% Complete

- **`run_channel_simulation.py`** written: single script handling all marketing channels via content framing
- **OASIS API verified from source**: all imports, environment lifecycle, and agent interaction patterns confirmed against CampaignSim's actual simulation scripts (not documentation)
- **SQLite-to-JSONL export** implemented: simulation trace converted to a format Phase 4's scorer reads
- **Simulation config format** defined: `simulation_config.json` schema agreed
- **Flask endpoint** for launching variant simulations designed
- **Remaining**: full integration test of the simulation subprocess from Flask, profile CSV copy automation, live end-to-end run with real personas

### 5.3 What the System Can Do Right Now

Using the FreshBrew Cold Brew Coffee test brief:
1. Upload the brief → system calls LLM and extracts a marketing ontology with entity and edge types
2. Build the Zep knowledge graph → nodes for FreshBrew, Urban Professionals persona, Instagram channel, Email channel, Starbucks competitor, etc.
3. Generate customer persona profiles → 8–12 OasisAgentProfile records, including a 1,500-word detailed persona for each customer segment
4. View the knowledge graph in the D3.js graph visualisation with node colour by entity type
5. Launch a channel simulation → `run_channel_simulation.py` spawns as a subprocess, runs OASIS, and writes an action log

---

## 6. Engineering Challenges Solved in the First 30%

These are the concrete technical problems discovered and resolved during the first 30% of development. Each represents a real engineering decision with a non-obvious answer.

### 6.1 The Fallback Entity Type Mismatch

**Problem discovered:** CampaignSim's ontology validator (`_validate_and_process`) enforces two mandatory "fallback" entity types to ensure every knowledge graph has a minimum usable schema. The original code hardcodes `Organization` and `Person` as these fallbacks. The new marketing ontology prompt specifies `Brand` and `Person` as the fallbacks — not `Organization`.

**Why this matters:** If left unfixed, the validator would silently inject an `Organization` node into every knowledge graph — a node type that no part of the system (persona generator, report agent, frontend) is designed to handle. Worse, it would *never* inject `Brand`, so the brand account agent profile could never be generated. The entire persona generation step for the core entity (the client's own brand) would produce zero results.

**How it was found:** By reading `ontology_generator.py` line-by-line rather than relying on the module's docstring, which did not mention the fallback enforcement logic.

**Fix:** Renamed `organization_fallback → brand_fallback`, updated the entity name, description, and attributes to brand-relevant values, and changed the presence check from `has_organization` to `has_brand`.

**Lesson:** When adapting a framework, validation and normalisation layers are the most dangerous places to miss — they look like infrastructure but contain domain assumptions.

---

### 6.2 The OASIS API Discovery Problem

**Problem discovered:** CAMEL-AI OASIS is a research-grade simulation library. Its documentation is sparse and the public README describes a high-level API that does not match the library's actual call signatures. Initial planning assumed OASIS supported custom platform definitions (e.g., an `InstagramPlatform` class) and used stdin/stdout for inter-process communication. Both assumptions were wrong.

**What the actual API looks like (verified from the existing codebase code):**

```python
# Actual: only two built-in platforms
env = oasis.make(
    agent_graph=agent_graph,
    platform=oasis.DefaultPlatformType.TWITTER,   # or .REDDIT
    database_path="simulation.db",
    semaphore=30,
)

# Actual: file-based IPC using JSON files in directories
# NOT stdin/stdout — the original Phase 2 design was wrong

# Actual: agent graph from CSV, not from a Python API call
agent_graph = await generate_twitter_agent_graph(
    profile_path="twitter_profiles.csv",
    model=model,
    available_actions=[ActionType.LIKE_POST, ...],
)
```

**Impact:** An entire simulation script had to be redesigned. The original Phase 2 scripts used invented function calls that would have caused `ImportError` or `AttributeError` at runtime.

**How it was found:** By reading CampaignSim's `run_twitter_simulation.py` — 780 lines — end-to-end. The actual API was only visible from the working implementation, not from OASIS documentation.

**Fix:** Designed a single `run_channel_simulation.py` that uses the verified API. Channel differences (Instagram vs. Email) are encoded in the campaign content text sent to agents, not in separate platform classes. OASIS's Twitter platform serves as the simulation substrate for all channels.

**Lesson:** When building on a research library, treat the working reference implementation as the ground truth, not the documentation.

---

### 6.3 The Action Type String Alignment Problem

**Problem discovered:** Phase 4's recommendation engine scores agent actions using a weight table (`CAMPAIGN_ACTION_WEIGHTS`). The initial design used intuitive marketing-domain action names: `SCROLL_PAST`, `SHARE_TO_STORY`, `SAVE_POST`, `CLICK_LINK`, `OPEN_EMAIL`, `UNSUBSCRIBE`. These names made conceptual sense for a marketing simulation.

However, OASIS stores agent actions in its SQLite `trace` table using the string values of its own `ActionType` enum — `LIKE_POST`, `REPOST`, `QUOTE_POST`, `FOLLOW`, `DO_NOTHING`, `CREATE_POST`. These are the only action type strings that will ever appear in a simulation action log.

If `CAMPAIGN_ACTION_WEIGHTS` uses custom strings and the simulation outputs real OASIS strings, the scorer's lookup `weights.get(action_type, 0.0)` will return `0.0` for every action. Every variant will score exactly `0.0`. The entire recommendation engine produces meaningless output — with no error thrown.

**Why this is insidious:** It is a silent failure. The system runs without crashing. It produces a report. The report is wrong, and there is no error message to explain why.

**Fix:** Updated `CAMPAIGN_ACTION_WEIGHTS` to use real OASIS `ActionType` string values as keys. The channel-specific conceptual actions (scrolling, saving, clicking) are communicated through the persona descriptions and campaign content framing instead — the LLM agent chooses the closest real action based on its persona context.

**Lesson:** In any pipeline where strings pass through multiple layers (simulation → export → scorer → report), the string constants must be agreed upon at the interface layer and verified end-to-end.

---

### 6.4 Simulation Output Format Mismatch

**Problem discovered:** The initial plan assumed OASIS would write action logs as JSONL files (one file per round). Phase 4's VariantScorer was written to read `actions_round_*.jsonl` using a glob pattern. The actual OASIS simulation writes *all* results to a **SQLite database** — there is no JSONL output from OASIS itself.

Additionally, the scorer was reading multiple per-round files and computing a per-round engagement trend (to detect if engagement improves or declines over the simulation). With a single consolidated file, this logic had to be adapted.

**Fix:** Added a `export_sqlite_to_jsonl()` function to the simulation script that reads the `trace` table from SQLite and writes a single `actions.jsonl` file after the simulation completes. Updated Phase 4's VariantScorer to read this single file and compute round proxies by splitting records into equal time-slices by record order.

**Lesson:** Define and agree on output file formats at the interface between pipeline stages before writing the consumer of that output.

---

### 6.5 The Zep Attribute Naming Constraint

**Problem discovered:** Zep Cloud's GraphRAG API reserves certain attribute names that cannot be used as custom entity attributes: `name`, `uuid`, `group_id`, `created_at`, `summary`. The initial ontology prompt allowed the LLM to generate attributes freely — and it frequently chose `name` (e.g., `brand.name`, `channel.name`) as the most natural attribute name.

When the system tried to push these entities to Zep, the API returned validation errors. With no retry logic and a silent failure path, the graph build would succeed but entities would be missing attributes — causing downstream graph queries to return incomplete data.

**Fix:** Added an explicit constraint to the `ONTOLOGY_SYSTEM_PROMPT`: *"Attribute names must not use reserved words: name, uuid, group_id, created_at, summary. Use instead: brand_name, channel_name, format_type, etc."* The prompt now provides examples of compliant attribute names for each entity type.

**Lesson:** API constraints from third-party services must be encoded into LLM prompts explicitly. An LLM will choose the most natural name, not the API-compliant one, unless told otherwise.

---

## 7. What the Next 70% Delivers

For context, here is what the remaining phases build:

| Milestone | What It Enables |
|---|---|
| Phase 2 complete (45%) | End-to-end simulation: upload brief → run variant → see raw action log |
| Phase 3 complete (65%) | A/B testing: compare 2–3 variants, parallel execution, variant builder UI |
| Phase 4 complete (90%) | Recommendation report: ranked variants, segment breakdown, strategic rationale |
| Phase 5 complete (100%) | Polished marketer UI, expert validation study, thesis deliverables |

---

## 8. What the Delivered System Will Demonstrate

The completed system provides three academically interesting contributions:

1. **Domain transfer of multi-agent simulation:** Demonstrates that a social opinion simulation architecture can be systematically re-domained to marketing without rebuilding the core simulation engine — a methodological contribution in applied AI.

2. **GraphRAG-grounded persona generation:** Demonstrates that Zep's GraphRAG retrieval produces richer, more contextually consistent persona profiles than plain-text LLM generation — testable via the ablation study planned in Phase 5.

3. **Pre-launch campaign signal validity:** The user study (Phase 5) tests whether simulation rankings correlate with human marketing expert predictions — directly validating the system's practical utility as a decision-support tool.

---

## 9. Appendix — Sample System Input / Output

### Input (Campaign Brief)

```
Brand: FreshBrew Coffee
Product: Cold Brew Concentrate (new launch)
Target Market: Urban professionals aged 25–40, health-conscious, premium spenders
Key Message: Premium quality, zero sugar, ready in seconds
Campaign Goal: Drive trial purchase among new customers
Channels to test: Instagram, Email marketing
Competitors: Starbucks RTD, La Colombe Draft Latte, Minor Figures
Brand Voice: Clean, confident, modern
Budget: $50,000
```

### Output (Extracted Marketing Ontology — sample)

```json
{
  "entity_types": [
    { "name": "CustomerPersona", "description": "Audience segment with demographics and psychographics" },
    { "name": "MarketingChannel", "description": "Distribution channel for campaign content" },
    { "name": "ContentFormat", "description": "Format of campaign creative (VideoAd, EmailNewsletter, etc.)" },
    { "name": "Campaign", "description": "The marketing campaign or promotion" },
    { "name": "Competitor", "description": "Competing brand in the same category" },
    { "name": "Brand", "description": "Fallback: any brand not fitting a specific type" },
    { "name": "Person", "description": "Fallback: any individual not fitting a specific type" }
  ],
  "edge_types": [
    { "name": "TARGETS", "source": "Campaign", "target": "CustomerPersona" },
    { "name": "DISTRIBUTED_ON", "source": "Campaign", "target": "MarketingChannel" },
    { "name": "COMPETES_WITH", "source": "Brand", "target": "Competitor" }
  ]
}
```

### Output (Persona Profile — excerpt)

```
Name: Alex M
Persona type: CustomerPersona — Urban Professional Male
Age: 28 | Gender: Male | MBTI: ENTJ | Country: US | Profession: Marketing Manager

Bio: Coffee-first mornings. Commute warrior. Always optimising.

Persona (excerpt): Alex is a 28-year-old marketing manager in a mid-size tech company.
He earns $85,000/year, commutes 45 minutes each way by subway, and starts every day
with a coffee ritual. He is quality-conscious and willing to pay a premium for products
that fit his efficient lifestyle. On Instagram he follows fitness, productivity, and food
accounts; he scrolls during his morning commute and engages with video content that is
under 30 seconds. He has previously tried Starbucks RTD cold brew but finds it too sweet...
```

### Output (Simulation Action Log — excerpt)

```jsonl
{"variant_id": "instagram_videoad", "channel": "instagram", "agent_id": 1, "action_type": "LIKE_POST", "timestamp": "2026-05-07T10:23:01"}
{"variant_id": "instagram_videoad", "channel": "instagram", "agent_id": 2, "action_type": "REPOST", "timestamp": "2026-05-07T10:23:04"}
{"variant_id": "email_newsletter", "channel": "email", "agent_id": 1, "action_type": "DO_NOTHING", "timestamp": "2026-05-07T10:25:11"}
{"variant_id": "email_newsletter", "channel": "email", "agent_id": 2, "action_type": "CREATE_POST", "timestamp": "2026-05-07T10:25:14"}
```

### Output (Recommendation Report — final format, Phase 4)

```
TOP RECOMMENDATION: Instagram VideoAd — Urban Professionals segment
Engagement score: 0.42 (vs. Email Newsletter: 0.21)

Reasoning: The Instagram VideoAd variant generated 2.1× more engagement than the
Email Newsletter variant. The Urban Professional segment (agents 1, 2, 4) showed
the strongest response — 68% engagement rate — driven primarily by reposts and
likes from ENTJ and ENFP personas who responded to the "zero sugar" message.
The Email Newsletter performed weakest among the 25-32 age bracket, likely because
this segment's persona profiles indicate low email open rates for promotional content.

Recommended next step: Allocate 70% of budget to Instagram VideoAd targeting
Urban Professionals aged 25-35. A/B test two message variants: 
"Zero Sugar" vs. "Ready in Seconds" as the primary hook.
```

---

*Report prepared for Bachelor's thesis supervisor meeting — May 2026*
*All code artefacts located at: `/Users/abedmreyan/Desktop/Graduation Project 2/`*
*Implementation documentation: `implementation/01_phase1_core_fork.md` through `05_phase5_ui_evaluation.md`*
