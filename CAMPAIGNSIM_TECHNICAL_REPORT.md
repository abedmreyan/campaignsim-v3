# CampaignSim — Complete Technical Handoff Report
### Thesis Documentation Reference · June 2026
### Written from the v3 codebase — all details verified against the actual source code

---

> **How to use this document**
> This report is the single authoritative reference for writing the thesis, creating diagrams, producing the literature review, and documenting the system for the graduation project committee. It supersedes all previous briefing documents. Every technical detail has been verified directly against the source code — do not rely on earlier drafts.

---

## Table of Contents

| # | Section |
|---|---------|
| 1 | [Project Concept & Problem Statement](#1-project-concept--problem-statement) |
| 2 | [Market Context & Positioning](#2-market-context--positioning) |
| 3 | [High-Level System Architecture](#3-high-level-system-architecture) |
| 4 | [End-to-End User Workflow (5 Phases)](#4-end-to-end-user-workflow-5-phases) |
| 5 | [Module A — Knowledge Graph System](#5-module-a--knowledge-graph-system) |
| 6 | [Module B — OASIS Persona Generation](#6-module-b--oasis-persona-generation) |
| 7 | [Module C — Simulation Engine](#7-module-c--simulation-engine) |
| 8 | [Module D — A/B Campaign Testing](#8-module-d--ab-campaign-testing) |
| 9 | [Module E — Variant Scoring Engine](#9-module-e--variant-scoring-engine) |
| 10 | [Module F — Campaign Recommendation Agent](#10-module-f--campaign-recommendation-agent) |
| 11 | [Module G — Single Simulation Report Agent](#11-module-g--single-simulation-report-agent) |
| 12 | [Frontend Architecture (Vue 3)](#12-frontend-architecture-vue-3) |
| 13 | [Backend Architecture (Flask)](#13-backend-architecture-flask) |
| 14 | [Complete Data Models](#14-complete-data-models) |
| 15 | [Complete API Reference](#15-complete-api-reference) |
| 16 | [Key Design Decisions & Rationale](#16-key-design-decisions--rationale) |
| 17 | [End-to-End Example Scenario](#17-end-to-end-example-scenario) |
| 18 | [Full Technology Stack](#18-full-technology-stack) |
| 19 | [Academic Research Context & Citations](#19-academic-research-context--citations) |
| 20 | [Environment & Deployment Configuration](#20-environment--deployment-configuration) |
| 21 | [Diagram Specifications for Visual Team](#21-diagram-specifications-for-visual-team) |

---

## 1. Project Concept & Problem Statement

### What Is CampaignSim?

**CampaignSim** is an AI-powered marketing campaign simulation and recommendation platform. It allows marketing teams to test how real customer audiences would respond to a campaign — before spending any advertising budget.

The system creates a high-fidelity digital sandbox where AI-driven customer personas autonomously interact with campaign content across different channels (Instagram, Email, TikTok, LinkedIn). It outputs ranked recommendations showing which combination of content format, marketing channel, and audience segment will perform best — with a full evidence trail explaining why.

### Core Value Proposition (One Sentence)

> Upload a brand brief → get AI-generated customer personas grounded in your brand's market landscape → define campaign variants → run parallel simulations → receive a ranked recommendation report — all before launching the real campaign.

### The Three Problems CampaignSim Solves

**Problem 1 — Pre-launch decisions are made on gut instinct**
Choosing between a video ad and a carousel post, Instagram versus email, a playful tone versus a professional one — these decisions are typically based on guesswork or extrapolation from unrelated past campaigns. The wrong choice can waste thousands of dollars and weeks of time.

**Problem 2 — Real A/B testing is slow and expensive**
Running an actual A/B test requires launching live ads, spending real budget, and waiting days or weeks for statistically significant results. By then, the market window may have closed. Small-to-medium businesses cannot afford the cost.

**Problem 3 — Campaigns succeed or fail without explaining why**
Traditional analytics show *what* happened after a campaign launched. They do not explain *which audience segment* responded, *on which channel*, *to which content element*, or *why*. There is no mechanism to ask the audience.

**CampaignSim's Answers**
- Simulate thousands of customer reactions in minutes before any spend
- Compare multiple campaign variants simultaneously for ~$1–2 per simulation run
- Interview individual simulated personas to understand the reasoning behind their responses
- Get a structured, explainable recommendation grounded in brand-specific knowledge

### Target Users

| User | Primary Use |
|---|---|
| Marketing managers at SMBs | Pre-test new product launch campaigns |
| Digital marketing agencies | Present data-backed recommendations to clients |
| Brand strategists | Compare channel and format hypotheses |
| Growth marketers | Optimise audience segment targeting |
| Marketing educators & students | Teach campaign strategy with real simulation data |

### Vision Statement

To become the standard pre-launch testing layer for marketing teams — sitting between campaign ideation and real-world spend, enabling data-driven decisions without requiring data from the market itself.

---

## 2. Market Context & Positioning

### Market Size

The global digital advertising market was valued at approximately **$600 billion in 2024** and is projected to exceed **$870 billion by 2028**. Despite this scale, industry research consistently shows that **60–80% of new product campaigns fail to meet their KPIs** — a primary driver of demand for pre-launch validation tools.

### Competitive Landscape

| Tool | Category | What It Does | Critical Gap |
|---|---|---|---|
| Google Optimize / Optimizely | A/B Testing | Tests live traffic variants | Requires real audience and real spend |
| HubSpot / Marketo | Campaign Management | Analytics on running campaigns | Post-launch only; no prediction |
| Persado | AI Copywriting | Generates copy variants | Does not simulate customer reactions |
| Brandwatch / Sprout Social | Social Listening | Sentiment after publication | Reactive, not predictive |
| Nielsen Ad Intelligence | Panel Testing | Focus group-style testing | Expensive ($5,000+), slow (weeks) |
| Synthetic AI Focus Groups | Qualitative AI | Interview AI personas | Not grounded in brand-specific knowledge |

**The gap CampaignSim fills:** No existing tool combines (1) brand-specific knowledge graph construction, (2) LLM-grounded customer personas, (3) multi-agent behavioural simulation, and (4) cross-channel, cross-variant scoring with explainable recommendations — in a single, low-cost, fast workflow.

### Positioning

CampaignSim occupies the space **between qualitative insight and quantitative validation**:

| Dimension | CampaignSim | A/B Testing | Focus Groups |
|---|---|---|---|
| Speed | Minutes | Days–Weeks | Days–Weeks |
| Cost per run | ~$1–2 | $1,000s+ in ad spend | $5,000–$50,000 |
| Explainability | High (interview personas) | Low (just outcomes) | Medium |
| Brand specificity | High (built from your brief) | Medium | Low |
| Pre-launch | ✅ Yes | ❌ No | ✅ Yes |

---

## 3. High-Level System Architecture

### Three-Tier Architecture

```
╔══════════════════════════════════════════════════════════════╗
║                  WEB FRONTEND (Vue 3 + Vite)                 ║
║                                                              ║
║  5-phase guided workflow  ·  D3.js knowledge graph           ║
║  Real-time simulation progress  ·  Recommendation reports    ║
║  Agent interview interface  ·  Campaign history browser      ║
╚══════════════════════════╦═══════════════════════════════════╝
                           ║  REST API  (HTTP/JSON)
                           ▼
╔══════════════════════════════════════════════════════════════╗
║               FLASK BACKEND (Python 3.11+)                   ║
║                                                              ║
║  API Blueprints: graph.py  simulation.py  report.py          ║
║  ┌────────────────────────────────────────────────────────┐  ║
║  │ SERVICES LAYER                                         │  ║
║  │  OntologyGenerator · GraphBuilderService               │  ║
║  │  OasisProfileGenerator · SimulationConfigGenerator     │  ║
║  │  SimulationManager · SimulationRunner                  │  ║
║  │  VariantRunner · VariantScorer                         │  ║
║  │  CampaignReportAgent · ReportAgent                     │  ║
║  └────────────────────────────────────────────────────────┘  ║
╚═══════╦════════════════════╦════════════════════════════════╝
        ║                    ║
        ▼                    ▼
╔═══════════════╗   ╔════════════════════════════════════╗
║ LOCAL SQLite  ║   ║  LLM API (OpenAI-compatible)       ║
║ KNOWLEDGE     ║   ║                                    ║
║ GRAPH         ║   ║  Qwen-plus / GPT-4o-mini           ║
║               ║   ║  · Entity extraction               ║
║ One .db per   ║   ║  · Persona generation              ║
║ graph         ║   ║  · Config generation               ║
║               ║   ║  · Report & recommendation         ║
║ Nodes, Edges, ║   ║  · Embeddings (text-embedding-3)   ║
║ Episodes,     ║   ╚════════════════════════════════════╝
║ Ontology      ║
╚═══════════════╝   ╔════════════════════════════════════╗
                    ║  OASIS SIMULATION ENGINE           ║
                    ║  (Python subprocess)               ║
                    ║                                    ║
                    ║  run_twitter_simulation.py         ║
                    ║  run_reddit_simulation.py          ║
                    ║  run_parallel_simulation.py        ║
                    ║  run_channel_simulation.py         ║
                    ║                                    ║
                    ║  → SQLite trace databases          ║
                    ║  → actions.jsonl action logs       ║
                    ╚════════════════════════════════════╝
```

> **Important correction from earlier documentation:** The Knowledge Graph is **NOT** hosted on Zep Cloud. It is a fully self-contained, locally-hosted SQLite-based system built in `backend/app/services/kg/`. The `KGClient` class is a drop-in replacement for the Zep SDK so all existing service code continues to work unchanged. The config still supports `KG_BACKEND=zep` as a fallback option, but the default and production mode is `KG_BACKEND=local`.

---

## 4. End-to-End User Workflow (5 Phases)

### Phase Overview

```
[Home Page]
Upload brand brief (PDF/MD/TXT) + enter campaign goal
       │
       ▼
[Phase 1 — Knowledge Graph Build]
POST /api/graph/ontology/generate
  → LLM reads document, identifies entity types and relationship types
  → Persists as project with ontology schema
POST /api/graph/build
  → Document chunked → episodes submitted → LLM extracts entities + edges
  → Nodes and edges stored in SQLite knowledge graph
  → D3.js graph renders live as nodes accumulate (polls every 10 s)
       │
       ▼
[Phase 2 — Simulation Preparation]
POST /api/simulation/create
  → Creates simulation record linked to graph_id
POST /api/simulation/prepare
  → Reads KG entities → generates OASIS persona profiles (parallel LLM calls)
  → Saves twitter_profiles.csv + reddit_profiles.json
  → LLM generates simulation_config.json (agent schedules, events, hot topics)
       │
       ▼
[Phase 3 — Simulation Run]
POST /api/simulation/start  (platform: twitter | reddit | parallel)
  → Spawns OASIS subprocess
  → Brand agent (ID 0) posts campaign content
  → Persona agents react autonomously over N rounds
  → Actions logged to actions.jsonl in real time
  → GET /api/simulation/{id}/run-status  (polled by frontend)
       │
       ▼
[Phase 4 — Single Report]           [Phase 4 — A/B Campaign]
POST /api/report/generate           POST /api/simulation/ab_test
  → ReACT report agent runs           → VariantRunner launches N
  → Analyses action logs                variant subprocesses in parallel
  → Produces 7-section report        GET /api/simulation/ab_status/{id}
GET /api/report/{id}                  → Poll until all variants complete
POST /api/report/chat               POST /api/simulation/campaign_recommendations
  → Follow-up Q&A                     → VariantScorer + CampaignReportAgent
                                     GET /api/simulation/campaign_report/{id}
       │
       ▼
[Phase 5 — Agent Interview]
POST /api/simulation/interview
  → IPC command sent to live OASIS subprocess
  → Agent responds in character to user's question
```

---

## 5. Module A — Knowledge Graph System

### 5.1 Purpose & Role

The Knowledge Graph is the system's memory of a brand's market landscape. It stores the entities extracted from the uploaded brand brief (brands, products, customer segments, channels, competitors, influencers, etc.) and the relationships between them. It serves two critical functions:

1. **Grounding persona generation** — the personas the system creates are derived from the actual entities in the graph, not from generic training data
2. **Enriching recommendations** — the Campaign Report Agent can search the graph to retrieve relevant brand context when explaining its reasoning

### 5.2 Architecture

```
Brand Documents (PDF / MD / TXT)
        │
        ▼  text extraction + 500-token chunks with 50-token overlap
TextProcessor
        │
        ▼
OntologyGenerator (LLM call)
  → Analyses full document
  → Produces entity_types: list of [{name, description}]
  → Produces edge_types:  list of [{name, description, source_type, target_type}]
  → Persists to project JSON
        │
        ▼
GraphBuilderService.build_graph_async()
  → Creates SQLite .db file for this graph_id
  → Stores ontology in 'ontology' table
  → Submits text chunks as Episodes via KGClient
  → Background ThreadPoolExecutor runs extraction per episode:
        ├── LLM extracts entities + relationships from chunk
        ├── upsert_node() — merge by name_lower (no duplicates)
        ├── upsert_edge() — link source → target by resolved UUIDs
        ├── embed_texts() — generate embeddings for new nodes/edges
        └── mark episode processed=True
```

### 5.3 Database Schema

One SQLite file is created per graph at `uploads/knowledge_graphs/{graph_id}.db`, opened in **WAL (Write-Ahead Logging)** mode for safe simultaneous reads and writes.

#### Table: `nodes`
| Column | Type | Notes |
|---|---|---|
| `uuid` | TEXT PK | UUID4 |
| `name` | TEXT | Entity name as extracted from text |
| `name_lower` | TEXT | Lowercase; used for deduplication on upsert |
| `labels` | TEXT | JSON array, e.g. `["CustomerPersona"]` |
| `summary` | TEXT | 1–2 sentence LLM description |
| `attributes` | TEXT | JSON object with extra fields |
| `embedding` | BLOB | Float32 vector (OpenAI or TF-IDF fallback) |
| `created_at` | TEXT | ISO 8601 timestamp |

#### Table: `edges`
| Column | Type | Notes |
|---|---|---|
| `uuid` | TEXT PK | UUID4 |
| `name` | TEXT | Relationship type, e.g. `TARGETS` |
| `fact` | TEXT | Natural-language sentence describing the relationship |
| `source_node_uuid` | TEXT FK | Source node |
| `target_node_uuid` | TEXT FK | Target node |
| `attributes` | TEXT | JSON object |
| `embedding` | BLOB | Float32 vector of the fact sentence |
| `created_at`, `valid_at`, `invalid_at`, `expired_at` | TEXT | Temporal validity fields |
| `episodes` | TEXT | JSON array of contributing episode UUIDs |

#### Table: `episodes`
| Column | Type | Notes |
|---|---|---|
| `uuid_` | TEXT PK | UUID4 (underscore convention from Zep API) |
| `data` | TEXT | Raw text chunk |
| `type` | TEXT | Always `"text"` |
| `processed` | INTEGER | 0 = pending extraction, 1 = done |
| `created_at` | TEXT | ISO 8601 timestamp |

#### Table: `ontology`
| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | Always row 1 (one ontology per graph) |
| `entity_types` | TEXT | JSON array of `{name, description, attributes}` |
| `edge_types` | TEXT | JSON array of `{name, description, source_targets}` |

### 5.4 Concurrency Model

- A module-level `_registry` dictionary maps `graph_id → SQLiteStore` instance, protected by a `_registry_lock`.
- Each `SQLiteStore` has a `_write_lock` (`threading.Lock`) serialising all writes.
- Reads open a separate connection without locking, benefiting from WAL mode.
- The extraction background pool runs up to **2 concurrent workers** (`_EXTRACTOR_WORKERS = 2`).

### 5.5 LLM Extraction Process (Per Episode)

When a text chunk is submitted:

1. Inserted into `episodes` table as `processed = False`
2. Scheduled on the ThreadPoolExecutor
3. Worker retrieves the stored ontology and the episode text
4. Sends a structured prompt to the LLM:
   - **System**: "You are a knowledge graph extraction engine. Return ONLY valid JSON."
   - **User**: Ontology (valid entity types + edge types) + text chunk (max 4,000 chars)
   - **Expected response**: `{"entities": [...], "relationships": [...]}`
5. Entities and relationships are validated against the ontology — unknown types discarded
6. `upsert_node()` called per entity (merges by `name_lower` if already exists)
7. `upsert_edge()` called per relationship (resolves node UUIDs by name)
8. Embeddings generated for all **new** nodes and edges in one batch call
9. Episode marked `processed = True`

### 5.6 Search System — How KG Search Works

The system implements a hybrid search combining vector similarity and keyword matching, merged via **Reciprocal Rank Fusion (RRF)**.

```
User Query
    │
    ├── Step 1: Embed query → query_vector
    │
    ├── Step 2A: Semantic ranking
    │     For each stored node/edge:
    │       cosine_similarity(query_vector, stored_embedding)
    │     Sort descending by score
    │
    ├── Step 2B: Keyword ranking (BM25)
    │     Tokenise query and corpus
    │     BM25Okapi.get_scores(query_tokens)
    │     Sort descending by score
    │
    ├── Step 3: RRF Merge
    │     For rank r in each list:
    │       rrf_score(item) += 1 / (60 + r)
    │     Final sort by combined rrf_score
    │
    └── Optional Step 4: LLM Cross-Encoder Reranking
          Send top-N results to LLM: "Score each 0–10 for relevance"
          Re-sort by LLM scores
          (More accurate, used for specific queries)
```

**Search scopes:**
- `"edges"` — search relationship facts (default, used by report agents)
- `"nodes"` — search entity summaries
- `"both"` — search both and merge results

### 5.7 Embedding Fallback Strategy

| Mode | Trigger | Method |
|---|---|---|
| Primary | API available | OpenAI-compatible `/v1/embeddings` endpoint, model `text-embedding-3-small`, batch size 100 |
| Fallback | API error | TF-IDF (max 8,192 features, bigrams) + TruncatedSVD (256 dimensions) from scikit-learn |

The fallback is entirely local and requires no external service. It re-fits on every call so new documents are always included.

### 5.8 Marketing Ontology — Typical Entity and Edge Types

The ontology is **generated fresh per brand brief** by the LLM, not hardcoded. These are representative types that commonly appear:

**Entity Types**
| Type | Description |
|---|---|
| `CustomerPersona` | Audience segment with demographics and behavioural traits |
| `MarketingChannel` | Distribution channel (Instagram, Email, TikTok, LinkedIn) |
| `ContentFormat` | Type of ad creative (VideoAd, CarouselPost, EmailNewsletter) |
| `Brand` | The brand being analysed |
| `Product` | Product or service being promoted |
| `Competitor` | Competing brand or product |
| `Influencer` | Content creator or key opinion leader |
| `Market` | Geographic or vertical market segment |

**Edge Types**
| Relationship | Source → Target | Meaning |
|---|---|---|
| `TARGETS` | Campaign → CustomerPersona | Campaign aims at this segment |
| `DISTRIBUTED_ON` | Campaign → MarketingChannel | Campaign runs on this channel |
| `USES_FORMAT` | Campaign → ContentFormat | Campaign uses this format |
| `COMPETES_WITH` | Brand → Competitor | Competitive relationship |
| `ACTIVE_ON` | CustomerPersona → MarketingChannel | Persona uses this channel |
| `RESPONDS_TO` | CustomerPersona → ContentFormat | Persona engages with this content type |
| `INFLUENCES` | Influencer → CustomerPersona | Influencer reaches this audience |

---

## 6. Module B — OASIS Persona Generation

### 6.1 Purpose

This module reads the entities stored in the knowledge graph and generates fully detailed, behaviourally consistent social media agent profiles. These profiles are the inputs to the OASIS simulation engine — they determine how each simulated "customer" will behave.

### 6.2 The OasisAgentProfile Data Structure

Every generated persona is an `OasisAgentProfile` with the following fields:

| Field | Type | Description |
|---|---|---|
| `user_id` | int | Sequential ID. **Agent 0 is always the brand.** Personas start at 1. |
| `user_name` | str | Social media handle, e.g. `@alex_morning_runner` |
| `name` | str | Display name |
| `bio` | str | 1–2 sentence personal biography |
| `persona` | str | 3–5 sentence behavioural description used to guide the agent's LLM decisions |
| `age` | int | Age |
| `gender` | str | Gender |
| `mbti` | str | Myers-Briggs personality type (e.g. `ENTJ`) |
| `country` | str | Country of origin |
| `profession` | str | Job title |
| `interested_topics` | list[str] | Topics this persona follows and engages with |
| `karma` | int | Reddit-style influence score (default: 1,000) |
| `friend_count` | int | Twitter friend count |
| `follower_count` | int | Twitter follower count |
| `statuses_count` | int | Number of posts made |
| `source_entity_uuid` | str | UUID of the KG entity this persona was derived from |
| `source_entity_type` | str | Entity type label from the ontology |

### 6.3 Generation Pipeline

```
SimulationManager.prepare_simulation()
  │
  ├── Stage 1: Read entities from KG
  │     ZepEntityReader.filter_defined_entities(graph_id, entity_types)
  │       → reads all nodes from KG (paginated, max 2,000 nodes)
  │       → filters to requested entity types
  │       → enriches each node with its connected edges
  │
  ├── Stage 2: Generate persona profiles
  │     OasisProfileGenerator.generate_profiles_from_entities()
  │       → for each KG entity:
  │           build prompt with: name, labels, summary, attributes, edges
  │           call LLM (async, up to parallel_count=5 concurrent calls)
  │           parse response → OasisAgentProfile
  │           append to output file immediately (real-time progress)
  │       → Brand agent (user_id=0) is always inserted as first profile
  │
  ├── Stage 3: Save profiles to disk
  │     save_profiles(platform="reddit") → reddit_profiles.json
  │     save_profiles(platform="twitter") → twitter_profiles.csv
  │
  └── Stage 4: Generate simulation configuration
        SimulationConfigGenerator.generate_config()
          → LLM reads all profiles + campaign goal + document context
          → Produces simulation_config.json
```

### 6.4 Profile Output Formats

**`twitter_profiles.csv`** (used by Twitter simulation and A/B channel simulations)

```
user_id,name,bio,persona,age,gender,mbti,country,profession,interested_topics,...
0,FreshBrew Coffee,Zero-sugar coffee ready in 30 seconds.,Brand promoting...,,,,,Marketing,["coffee","wellness"],,,
1,Alex Chen,Marathoner startup founder always caffeinated.,Health-conscious millennial...,31,male,ENTJ,US,Startup Founder,"['fitness','productivity']",...
```

**`reddit_profiles.json`** (used by Reddit simulation)

```json
[
  {
    "user_id": 0,
    "username": "freshbrew_brand",
    "name": "FreshBrew Coffee",
    "bio": "Zero-sugar coffee. Ready in 30 seconds.",
    "persona": "Brand account for FreshBrew Coffee...",
    "karma": 5000,
    "created_at": "2025-01-15"
  },
  {
    "user_id": 1,
    "username": "alex_morning_runner",
    "name": "Alex Chen",
    "bio": "Marathoner, startup founder, always caffeinated.",
    "persona": "Health-conscious millennial who values efficiency...",
    "age": 31, "gender": "male", "mbti": "ENTJ",
    "country": "US", "profession": "Startup Founder",
    "interested_topics": ["fitness", "productivity", "nutrition"],
    "karma": 1420,
    "created_at": "2025-03-10"
  }
]
```

### 6.5 Simulation Configuration Generation

After profiles are saved, `SimulationConfigGenerator` calls the LLM with the full profile list and campaign context. It produces `simulation_config.json`:

```json
{
  "simulation_id": "sim_abc123ef4567",
  "time_config": {
    "total_simulation_hours": 72,
    "minutes_per_round": 30
  },
  "agent_configs": [
    { "agent_id": 0, "activity_level": 0.9 },
    { "agent_id": 1, "activity_level": 0.65 }
  ],
  "event_config": {
    "initial_posts": ["FreshBrew Coffee is here! Zero sugar. Ready in 30 seconds. Try it now."],
    "hot_topics": ["sugar-free beverages", "morning coffee routines", "productivity hacks"]
  },
  "twitter_config": { "max_rounds": 144, "post_frequency": "moderate" },
  "reddit_config": { "subreddit": "r/coffee", "max_rounds": 144 },
  "generation_reasoning": "Selected 72-hour window to capture morning and evening usage peaks..."
}
```

### 6.6 Audience Segment Assignment

Segments allow an A/B test to target different subgroups with different variants.

**Endpoint:** `POST /api/simulation/assign_segments`

**Process:**
1. Read all personas from `twitter_profiles.csv`
2. Separate brand agent (user_id = 0) from personas
3. For each named segment (e.g. `"MillennialProfessionals"`, `"GenZConsumers"`), classify every persona using an LLM call (reads name, age, profession, bio, interests)
4. Write one filtered CSV per segment: `profiles_MillennialProfessionals.csv`
5. A/B test variants with a matching `target_segment` will automatically use the filtered CSV

---

## 7. Module C — Simulation Engine

### 7.1 Architecture Decision: Subprocesses, Not Threads

**Every simulation runs as a separate operating system subprocess.** This is the central architectural decision of the simulation engine.

Reasons:
- OASIS simulations run their own async event loops internally, which cannot safely share a thread with Flask
- Subprocess isolation means one crashing simulation cannot affect the Flask server or other simulations
- Multiple simulations (and multiple A/B variants) can run truly in parallel, limited only by CPU cores

### 7.2 State Machine

Two parallel state tracking systems exist:

**SimulationState** (high-level lifecycle, managed by `SimulationManager`)

```
created → preparing → ready → running → completed
                                      → stopped
                                      → failed
                                      → paused
```

Persisted to: `uploads/simulations/{sim_id}/state.json`

**SimulationRunState** (live execution metrics, managed by `SimulationRunner`)

Tracks real-time process metrics: PID, current round, action counts, per-platform status, timestamp of last update.

Persisted to: `uploads/simulations/{sim_id}/run_state.json`

### 7.3 Simulation Script Dispatch

When `POST /api/simulation/start` is called with a `platform` value:

| `platform` value | Script launched |
|---|---|
| `"twitter"` | `scripts/run_twitter_simulation.py` |
| `"reddit"` | `scripts/run_reddit_simulation.py` |
| `"parallel"` | `scripts/run_parallel_simulation.py` |
| `"channel"` | `scripts/run_channel_simulation.py` (used for A/B variants) |

Each script is launched via `subprocess.Popen`. A monitor thread runs in the Flask process background, reading `run_state.json` to track progress and detect when the process exits.

### 7.4 File System Layout Per Simulation

```
uploads/simulations/{simulation_id}/
├── state.json                   — SimulationManager high-level state
├── run_state.json               — SimulationRunner live metrics (PID, round, counts)
├── simulation_config.json       — LLM-generated OASIS configuration
├── reddit_profiles.json         — Reddit agent profiles
├── twitter_profiles.csv         — Twitter agent profiles
├── profiles_{SegmentName}.csv   — Segment-filtered profiles (if assigned)
├── reddit_simulation.db         — OASIS SQLite: posts and comments
├── twitter_simulation.db        — OASIS SQLite: tweets and retweets
├── actions.jsonl                — Agent action log (one JSON object per line)
└── simulation.log               — Process stdout/stderr output
```

### 7.5 Action Log Format (`actions.jsonl`)

One JSON object per line for every agent action:

```jsonc
// Normal action record
{"round_num": 5, "timestamp": "2025-12-01T10:30:00", "platform": "twitter",
 "agent_id": 3, "agent_name": "Alex Chen", "action_type": "LIKE_POST",
 "action_args": {"post_id": 42}, "result": null, "success": true}

// Sentinel: round boundary
{"event_type": "round_end", "round_num": 5, "timestamp": "2025-12-01T10:31:00"}

// Sentinel: simulation complete
{"event_type": "simulation_end", "timestamp": "2025-12-01T16:00:00"}
```

Sentinel records are written by the simulation script and are skipped during scoring (the scorer checks for the `event_type` key and excludes those lines).

### 7.6 Agent Action Types

All action types are real OASIS `ActionType` enum values (not custom strings):

| Action Type | Marketing Meaning |
|---|---|
| `DO_NOTHING` | Saw the content, scrolled past — no engagement |
| `LIKE_POST` | Positive reaction, low commitment |
| `CREATE_POST` | Commented or replied — active interest |
| `REPOST` | Shared to own followers — strongest virality signal |
| `QUOTE_POST` | Shared with added commentary — social amplification |
| `FOLLOW` | Followed the brand account — strong purchase-intent signal |

### 7.7 RunnerStatus Enum

| Status | Meaning |
|---|---|
| `idle` | No process started |
| `starting` | Subprocess launching |
| `running` | Actively simulating |
| `paused` | Paused via IPC command |
| `stopping` | Stop signal sent, awaiting clean exit |
| `stopped` | Exited after stop command |
| `completed` | All rounds finished naturally |
| `failed` | Process crashed |

### 7.8 Agent Interview via IPC

While a simulation is running, the system can interact with individual agents using `SimulationIPCClient`. The frontend sends a prompt to `POST /api/simulation/interview`, which:

1. Validates the simulation environment is alive (`check_env_alive`)
2. The prompt is first passed through `optimize_interview_prompt()` to make it more effective
3. An IPC command is sent to the running subprocess
4. The targeted agent's LLM is called with the user's question, constrained by the agent's persona
5. The in-character response is returned and stored in interview history

### 7.9 Graph Memory Update (Optional)

When `ZepGraphMemoryUpdater` is enabled, a background thread runs continuously while a simulation is active. It reads new lines from `actions.jsonl` and feeds them as episodes back into the knowledge graph via `KGClient.graph.add()`. This means agent social behaviour during the simulation is recorded as new graph knowledge — the graph learns from the simulation.

---

## 8. Module D — A/B Campaign Testing

### 8.1 Concept

A/B testing in CampaignSim means running **the same population of persona agents** against **multiple campaign variants simultaneously**. Each variant has its own:
- Channel (Instagram, Email, TikTok, LinkedIn)
- Content format (VideoAd, CarouselPost, EmailNewsletter, ShortFormVideo)
- Message (headline, body copy, call-to-action, tone)
- Target audience segment (optional)

All variants launch in parallel and run independently. Their action logs are scored, and the Campaign Recommendation Agent produces a ranked comparison.

### 8.2 Campaign Data Model

**Campaign**
```
campaign_id        — Generated ID (e.g. "camp_abc123ef")
simulation_id      — Parent simulation that provided the personas
brand_name         — e.g. "FreshBrew Coffee"
campaign_goal      — e.g. "Drive trial purchase among health-conscious millennials"
variants           — list of CampaignVariant objects
campaign_report    — dict (populated after scoring + recommendation generation)
created_at         — ISO 8601 timestamp
```

**CampaignVariant**
```
variant_id         — e.g. "variant_0", "variant_1"
variant_name       — e.g. "Video on Instagram — Millennials"
channel            — "instagram" | "email" | "tiktok" | "linkedin"
target_segment     — Segment name (e.g. "MillennialProfessionals") or empty = all
max_rounds         — Number of simulation rounds (default: 10)
content:
  format           — "VideoAd" | "CarouselPost" | "EmailNewsletter" | "ShortFormVideo"
  headline         — Campaign headline text
  body             — Main body copy
  cta              — Call-to-action (e.g. "Try it — 20% off")
  visual_desc      — Description of visual/creative elements
  email_subject    — Subject line (email channel only)
  tone             — "playful" | "professional" | "urgent" | "neutral"
variant_sim_id     — ID of the variant's own simulation run directory
output_dir         — File path to variant's simulation directory
status             — "running" | "completed" | "failed"
error              — Error message if failed (else null)
```

**CampaignContent** is assembled into a structured campaign brief string by `formatted_content()` and passed to the channel simulation script as the brand's opening post.

### 8.3 A/B Test Launch Sequence

1. Frontend sends `POST /api/simulation/ab_test` with the campaign structure
2. Server builds `Campaign` object and calls `VariantRunner.launch_all(campaign)`
3. `VariantRunner` iterates over variants and calls `_launch_variant()` for each:
   - Creates directory: `uploads/simulations/{sim_id}__{variant_id}/`
   - Copies `twitter_profiles.csv` (or segment-filtered CSV if segment is set)
   - Writes `simulation_config.json` specific to this variant (channel, content, rounds)
   - Calls `SimulationRunner.start_simulation(variant_sim_id, platform="channel")`
   - Records `variant.variant_sim_id`, `variant.output_dir`, `variant.status = "running"`
4. `SimulationRunner.start_simulation()` returns immediately; subprocess runs independently
5. Campaign JSON persisted to `uploads/campaigns/{campaign_id}.json`
6. API returns immediately with `campaign_id`

Because `start_simulation()` is non-blocking and each subprocess runs independently, all N variants start and run in true parallel.

### 8.4 Campaign Polling

`GET /api/simulation/ab_status/{campaign_id}` returns the status of every variant:

```json
{
  "campaign_id": "camp_abc123",
  "total_variants": 3,
  "completed": 2,
  "failed": 0,
  "all_done": false,
  "variants": [
    {
      "variant_id": "variant_0",
      "variant_name": "Video on Instagram",
      "channel": "instagram",
      "variant_sim_id": "sim_xyz__variant_0",
      "runner_status": "completed",
      "env_status": {"status": "completed", "timestamp": "2025-12-08T12:30:00"},
      "actions_count": 142
    }
  ]
}
```

Completion is detected by checking `env_status.json` (written by the script) and the runner state. The `actions_count` is a live count of non-sentinel lines in `actions.jsonl`.

---

## 9. Module E — Variant Scoring Engine

### 9.1 Purpose

After all variant simulations complete, the `VariantScorer` reads each variant's `actions.jsonl` and converts raw action counts into a normalised **engagement score** that allows fair comparison between variants.

### 9.2 Engagement Score Formula

```
engagement_score = Σ(per_agent_weighted_score) / (num_agents × num_rounds)
engagement_rate_pct = engagement_score × 100
```

Where `per_agent_weighted_score` for each agent = sum of `action_weight` for every action that agent took.

The normalisation denominator `(num_agents × num_rounds)` represents the theoretical maximum engagement if every agent performed the highest-weight action in every round. This makes scores comparable across variants with different agent counts or round lengths.

### 9.3 Action Weights (from `Config.CAMPAIGN_ACTION_WEIGHTS`)

| Action Type | Weight | Marketing Rationale |
|---|---|---|
| `DO_NOTHING` | 0.0 | Saw content, scrolled past — zero engagement |
| `LIKE_POST` | 0.3 | Mild positive signal, low commitment |
| `CREATE_POST` | 0.35 | Commented/replied — active interest |
| `FOLLOW` | 0.45 | Followed brand — strong purchase-intent signal |
| `QUOTE_POST` | 0.5 | Shared with commentary — social amplification |
| `REPOST` | 0.55 | Pure share — strongest virality signal |

### 9.4 Full Metrics Output Per Variant

| Metric | How Computed |
|---|---|
| `engagement_score` | Normalised weighted score (0.0–theoretically ~2.0) |
| `engagement_rate_pct` | `engagement_score × 100` |
| `total_agents` | Count of distinct agent IDs in action log |
| `total_actions` | Total non-sentinel action records |
| `positive_actions` | Count of actions where weight > 0 |
| `negative_actions` | Count of actions where weight < 0 (currently none, reserved for dislike etc.) |
| `action_breakdown` | Dict `{action_type: count}` |
| `per_agent_scores` | Dict `{agent_id: cumulative_weighted_score}` |
| `per_round_engagement` | List of 5 average-score slices (time-series of engagement trend) |
| `trend` | `"improving"` if last slice > first slice, `"declining"` if lower, else `"flat"` |

### 9.5 Campaign-Level Scoring

`VariantScorer.score_campaign(campaign_dict)` runs `score_variant()` for every variant whose `actions.jsonl` file exists, then **sorts results by `engagement_score` descending** (best performer first). This sorted list is passed to the Campaign Recommendation Agent.

---

## 10. Module F — Campaign Recommendation Agent

### 10.1 Purpose

After variants are scored, the `CampaignReportAgent` uses an LLM in a **ReACT (Reasoning + Acting)** loop to synthesise scores and brand context into a structured, evidence-backed marketing recommendation report.

### 10.2 What is the ReACT Pattern?

ReACT is a prompting strategy where an AI agent alternates between:
- **Reasoning** (analysing the current situation, deciding what information is needed)
- **Acting** (calling a tool to retrieve specific data)
- **Observing** (reading the tool result and updating understanding)

This produces more accurate and traceable outputs than a single LLM call over raw data, because the agent is forced to use domain-specific analytical tools before drawing conclusions.

### 10.3 ReACT Loop Execution

```
[User message]
"Generate a campaign recommendation report. Brand: FreshBrew Coffee.
 Goal: Drive trial purchase. 3 variants tested."
       │
       ▼ [LLM call 1]
[Thought] "I need to compare variant performance before making recommendations."
[Action] Call variant_comparison tool
       │
       ▼ [Tool result]
Ranked table: Variant 1 (35.2%), Variant 2 (28.9%), Variant 3 (19.4%)
       │
       ▼ [LLM call 2]
[Thought] "I should understand which segments responded to each variant."
[Action] Call segment_insights tool
       │
       ▼ [Tool result]
MillennialProfessionals: Variant 1 = 38.1%, Variant 2 = 25.3%
GenZConsumers: Variant 2 = 31.2%, Variant 1 = 22.4%
       │
       ▼ [LLM call 3]
[Thought] "I should check channel effectiveness."
[Action] Call channel_effectiveness tool
       │
       ▼ [Tool result]
instagram: 32.1% avg, email: 19.4% avg
       │
       ▼ [LLM call 4, if graph_id provided]
[Thought] "I should look up brand context from the knowledge graph."
[Action] Call brand_context tool with query="FreshBrew target audience preferences"
       │
       ▼ [Tool result]
KG search results: "Urban professionals value speed and quality..."
       │
       ▼ [LLM call 5]
[No more tool calls — LLM produces final report text]
```

### 10.4 Available Tools

| Tool Class | `tool_name` | Input | Returns |
|---|---|---|---|
| `VariantComparisonTool` | `variant_comparison` | Scored variants list | Markdown table ranked by engagement rate |
| `SegmentInsightTool` | `segment_insights` | Scored variants list | Breakdown: which segments preferred which variants |
| `ChannelEffectivenessTool` | `channel_effectiveness` | Scored variants list | Aggregate engagement grouped by channel |
| `ContentFormatRankTool` | `content_format_ranking` | Scored variants list | Engagement ranked by content format |
| `ZepBrandContextTool` | `brand_context` | Search query string | KG semantic search results (entity facts) |

The brand_context tool is only available if a `graph_id` was provided when calling `/campaign_recommendations`.

### 10.5 Mandatory Report Structure

The system prompt requires the LLM to always produce these 7 sections in order:

1. **Executive Summary** — 3–4 sentences summarising the key finding
2. **Best Performing Variant** — Named variant with evidence (specific engagement percentages)
3. **Segment Analysis** — Which audience segment to prioritise and why
4. **Channel Recommendation** — Best channel with supporting engagement data
5. **Content Format Recommendation** — Best format with supporting data
6. **Top 3 Recommendations** — Ranked, each with a confidence level (High / Medium / Low)
7. **Risks & Limitations** — Simulation caveats and what to validate in the real world

### 10.6 Top Recommendation Extraction

After the report text is generated, a second LLM call extracts a structured summary for the UI:

```json
{
  "best_variant_name": "Video on Instagram — MillennialProfessionals",
  "best_channel": "instagram",
  "best_content_format": "VideoAd",
  "best_segment": "MillennialProfessionals",
  "engagement_rate_pct": 38.5,
  "confidence": "High",
  "one_line_rationale": "VideoAd on Instagram drove 2× more shares than carousel content."
}
```

### 10.7 Safety Guards

- `Config.REPORT_AGENT_MAX_TOOL_CALLS = 5` limits tool invocations per report
- If the limit is hit without a final text response, a fallback report noting the issue is returned
- `Config.REPORT_AGENT_TEMPERATURE = 0.5` balances creativity vs. factual grounding
- The top recommendation extraction uses `temperature=0.0` for maximum consistency

### 10.8 Complete Output Saved to Campaign JSON

```json
{
  "report_text": "## Campaign Recommendation Report\n\n### 1. Executive Summary\n...",
  "top_recommendation": { ... },
  "scored_variants": [ ... ],
  "tool_calls_log": [
    {"tool": "variant_comparison", "input": {}, "output_preview": "| Variant | ..."},
    {"tool": "segment_insights", "input": {}, "output_preview": "..."}
  ]
}
```

---

## 11. Module G — Single Simulation Report Agent

This module is separate from the Campaign Report Agent. It operates on a **single** Twitter/Reddit simulation (not A/B campaign) and produces a detailed behavioural analysis of how the entire simulated audience responded to the campaign.

### 11.1 Purpose vs. Campaign Report Agent

| | Single Report Agent | Campaign Report Agent |
|---|---|---|
| Input | One simulation's action log + social graph | Multiple scored variants |
| Output | Behavioural analysis, narrative, agent insights | Variant ranking, channel/segment recommendations |
| Key questions answered | "How did the community react?" "Who were the influencers?" "What sentiment emerged?" | "Which variant should we launch?" "Which channel is most effective?" |
| Used when | Single simulation run | A/B campaign with multiple variants |

### 11.2 Report Generation Flow

```
POST /api/report/generate
  → Background thread starts, returns report_id immediately
  → ReportAgent initialises with simulation context
  → ReACT loop: reads action logs, interviews agents, searches KG
  → Produces structured report with sections
  → Saves to report file

GET /api/report/generate/status
  → Polls progress (percentage, current step description)

GET /api/report/{report_id}
  → Returns complete report

GET /api/report/{report_id}/agent-log
  → Returns ReACT agent's reasoning steps (paginated by line number)

GET /api/report/{report_id}/console-log
  → Returns raw process stdout (paginated by line number)

POST /api/report/chat
  → Follow-up Q&A using the full report as context
```

### 11.3 Report Tools (Different from Campaign Agent)

| Tool | Purpose |
|---|---|
| `InsightForge` | Structured statistical analysis of the action log |
| `PanoramaSearch` | Semantic search over the knowledge graph |
| `TimelineAnalyser` | Per-round engagement breakdown and trend |
| `AgentProfiler` | Retrieves behavioural stats for specific agents |

### 11.4 Chat Feature

After a report is generated, users can ask follow-up questions. The full report text plus simulation context is included in the conversation as background, so the LLM can answer specific questions like:
- "Which agent had the highest influence?"
- "What was the sentiment in round 5?"
- "Why did engagement drop in round 7?"

---

## 12. Frontend Architecture (Vue 3)

### 12.1 Technology Stack

| Component | Library | Version | Notes |
|---|---|---|---|
| Framework | Vue.js | 3.5.x | Composition API with `<script setup>` |
| Build Tool | Vite | 7.x | Hot module replacement in dev |
| Routing | Vue Router | 4.x | `createWebHistory` (HTML5 mode) |
| HTTP Client | Axios | 1.14 | Custom `service` instance with retry logic |
| Graph Visualisation | D3.js | 7.9 | SVG force-directed graph |
| Internationalisation | Vue I18n | 11.x | English / Chinese |

### 12.2 Route Map

| URL Pattern | View | Purpose |
|---|---|---|
| `/` | `Home.vue` | Landing page: document upload, campaign goal |
| `/process/:projectId` | `MainView.vue` | Phase 1: KG build + live D3 graph |
| `/simulation/:simulationId` | `SimulationView.vue` | Phase 2 preparation: profiles + config |
| `/simulation/:simulationId/start` | `SimulationRunView.vue` | Phase 3 run: live action feed |
| `/report/:reportId` | `ReportView.vue` | Phase 4 report: sections + chat |
| `/interaction/:reportId` | `InteractionView.vue` | Phase 5: agent interview |
| `/campaign/:campaignId/report` | `CampaignReportView.vue` | A/B campaign: variant ranking + recommendation |

### 12.3 Step Components

| Component | Rendered In | Function |
|---|---|---|
| `Step1GraphBuild.vue` | MainView | Upload form, ontology preview, graph panel |
| `Step2EnvSetup.vue` | SimulationView | Entity type picker, profile preview cards, config viewer |
| `Step3Simulation.vue` | SimulationRunView | Start/stop/pause controls, round progress bar |
| `Step4Report.vue` | ReportView | Report sections renderer, ReACT log viewer, chat |
| `Step5Interaction.vue` | InteractionView | Agent selector, question input, response display |
| `Step5CampaignReport.vue` | CampaignReportView | Variant comparison table, score bars, recommendation card |
| `GraphPanel.vue` | MainView | D3 SVG canvas, node/edge click detail panel |
| `HistoryDatabase.vue` | Home | Simulation + campaign history browser |

### 12.4 API Module Split (`/src/api/`)

| File | Calls |
|---|---|
| `graph.js` | `generateOntology`, `buildGraph`, `getTaskStatus`, `getGraphData`, `getProject` |
| `simulation.js` | All simulation lifecycle: create, prepare, start, stop, status, profiles, config, actions, timeline, stats, interview, A/B test, campaign |
| `report.js` | `generateReport`, `getReportStatus`, `getReport`, `getAgentLog`, `getConsoleLog`, `chatWithReport` |
| `index.js` | Shared Axios instance + `requestWithRetry` (3 retries, 1 s delay, for mutating calls only) |

### 12.5 D3.js Knowledge Graph Visualisation

- Rendered as SVG using `d3.forceSimulation` with link/charge/centre forces
- Polls `GET /api/graph/project/{id}` and `GET /api/graph/data/{graph_id}` every **10 seconds**
- Re-renders only when node count changes (avoids redundant redraws)
- Each entity type gets a distinct colour from a fixed palette
- Node size scales with degree (number of connections)
- Clicking a node/edge opens a detail panel without page navigation
- Zoom + pan supported via `d3.zoom`

---

## 13. Backend Architecture (Flask)

### 13.1 Blueprint Structure

```
backend/app/api/
├── __init__.py          — Blueprint registration on Flask app
├── graph.py             — /api/graph/* (graph management, task status)
├── simulation.py        — /api/simulation/* (3,222 lines — all simulation logic)
└── report.py            — /api/report/* (report generation, chat)
```

### 13.2 Services Layer (`backend/app/services/`)

| File | Class | Role |
|---|---|---|
| `ontology_generator.py` | `OntologyGenerator` | LLM call: document → entity/edge type schema |
| `graph_builder.py` | `GraphBuilderService` | Text chunking → KGClient ingestion |
| `kg/client.py` | `KGClient` | Drop-in local KG API (mirrors Zep SDK namespaces) |
| `kg/store.py` | `SQLiteStore` | Thread-safe SQLite R/W for one graph |
| `kg/extractor.py` | — | LLM entity/relationship extraction per episode |
| `kg/embedder.py` | `Embedder` | Vector embedding generation (API + TF-IDF fallback) |
| `kg/search.py` | — | RRF-fused semantic + BM25 search |
| `kg/models.py` | `KGNode`, `KGEdge`, `KGEpisode`, `KGOntology` | Data classes |
| `zep_entity_reader.py` | `ZepEntityReader` | Reads and filters KG entities for persona use |
| `oasis_profile_generator.py` | `OasisProfileGenerator` | KG entities → OASIS persona profiles |
| `simulation_config_generator.py` | `SimulationConfigGenerator` | LLM → simulation_config.json |
| `simulation_manager.py` | `SimulationManager` | State machine: create → prepare → ready |
| `simulation_runner.py` | `SimulationRunner` | Subprocess launch, monitor thread, action log reader |
| `simulation_ipc.py` | `SimulationIPCClient` | IPC to running OASIS subprocess (interview, pause, stop) |
| `variant_runner.py` | `VariantRunner` | Launches N campaign variant subprocesses in parallel |
| `variant_scorer.py` | `VariantScorer` | Reads `actions.jsonl` → weighted engagement metrics |
| `campaign_report_agent.py` | `CampaignReportAgent` | ReACT loop → campaign recommendation report |
| `report_agent.py` | `ReportAgent` | ReACT loop → single-simulation analysis report |
| `campaign_tools.py` | Tool classes | Analytical tools used by `CampaignReportAgent` |
| `zep_graph_memory_updater.py` | `ZepGraphMemoryManager` | Background: feeds action logs back into KG |
| `text_processor.py` | `TextProcessor` | Document chunking (500 tokens, 50 overlap) |

### 13.3 Models Layer (`backend/app/models/`)

| File | Purpose |
|---|---|
| `project.py` | `ProjectManager` — CRUD for projects (JSON files in `uploads/projects/`) |
| `task.py` | `TaskManager` — tracks background task progress (in-memory + optional JSON) |
| `campaign.py` | `Campaign`, `CampaignVariant`, `CampaignContent` dataclasses |

### 13.4 Configuration (`backend/app/config.py`)

| Variable | Default | Purpose |
|---|---|---|
| `LLM_API_KEY` | _(required)_ | API key for LLM provider |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | LLM endpoint (any OpenAI-compatible URL) |
| `LLM_MODEL_NAME` | `gpt-4o-mini` | Model to use (e.g. `qwen-plus`, `gpt-4o-mini`) |
| `KG_BACKEND` | `local` | `"local"` = SQLite (default), `"zep"` = Zep Cloud |
| `KG_DATA_DIR` | `uploads/knowledge_graphs/` | Where `.db` graph files are stored |
| `ZEP_API_KEY` | _(optional)_ | Only needed when `KG_BACKEND=zep` |
| `OASIS_DEFAULT_MAX_ROUNDS` | `10` | Default simulation rounds |
| `REPORT_AGENT_MAX_TOOL_CALLS` | `5` | Max tool invocations per report |
| `REPORT_AGENT_TEMPERATURE` | `0.5` | LLM temperature for report generation |

---

## 14. Complete Data Models

### Project (JSON file)
```json
{
  "project_id": "proj_abc123",
  "name": "FreshBrew Campaign Study",
  "status": "graph_completed",
  "simulation_requirement": "Test campaign impact among health-conscious coffee drinkers",
  "ontology": {
    "entity_types": [{"name": "CustomerPersona", "description": "..."}],
    "edge_types": [{"name": "TARGETS", "description": "..."}]
  },
  "graph_id": "e3a8f24c...",
  "graph_build_task_id": "task_xyz789",
  "files": [{"filename": "brand-brief.pdf", "size": 42000}],
  "chunk_size": 500,
  "chunk_overlap": 50,
  "total_text_length": 15000,
  "analysis_summary": "...",
  "created_at": "2025-12-01T10:00:00",
  "updated_at": "2025-12-01T10:15:00"
}
```

**Project Status Enum**

| Value | Meaning |
|---|---|
| `created` | Project created, no docs processed |
| `ontology_generated` | LLM extracted entity/edge type schema |
| `graph_building` | Background KG build task running |
| `graph_completed` | Knowledge graph ready |
| `failed` | Error occurred |

### Task (in-memory + optional JSON)
```json
{
  "task_id": "task_xyz789",
  "task_type": "graph_build",
  "status": "processing",
  "progress": 65,
  "message": "Processing chunk 13/20...",
  "metadata": {"graph_name": "FreshBrew Graph", "text_length": 15000},
  "created_at": "2025-12-01T10:00:00",
  "updated_at": "2025-12-01T10:05:00"
}
```

**Task Status Enum:** `pending` → `processing` → `completed` / `failed`

### SimulationState (state.json)
```json
{
  "simulation_id": "sim_abc123ef4567",
  "project_id": "proj_abc123",
  "graph_id": "e3a8f24c...",
  "enable_twitter": true,
  "enable_reddit": false,
  "status": "ready",
  "entities_count": 45,
  "profiles_count": 43,
  "entity_types": ["CustomerPersona", "MarketingChannel"],
  "config_generated": true,
  "config_reasoning": "Selected 72-hour window...",
  "current_round": 0,
  "twitter_status": "not_started",
  "reddit_status": "not_started",
  "created_at": "2025-12-01T10:30:00",
  "updated_at": "2025-12-01T10:45:00",
  "error": null
}
```

### Scored Variant (from VariantScorer)
```json
{
  "variant_id": "variant_0",
  "variant_name": "VideoAd on Instagram — Millennials",
  "channel": "instagram",
  "content_format": "VideoAd",
  "target_segment": "MillennialProfessionals",
  "tone": "playful",
  "status": "scored",
  "total_agents": 30,
  "total_actions": 215,
  "positive_actions": 175,
  "negative_actions": 0,
  "engagement_score": 0.3567,
  "engagement_rate_pct": 35.67,
  "action_breakdown": {
    "DO_NOTHING": 40,
    "LIKE_POST": 85,
    "CREATE_POST": 42,
    "REPOST": 31,
    "QUOTE_POST": 12,
    "FOLLOW": 5
  },
  "per_round_engagement": [0.22, 0.28, 0.35, 0.38, 0.42],
  "per_agent_scores": {"1": 0.85, "2": 0.30, "3": 1.20},
  "trend": "improving"
}
```

---

## 15. Complete API Reference

### `/api/graph/` — Knowledge Graph Management

| Method | Path | Description |
|---|---|---|
| POST | `/ontology/generate` | Upload docs + campaign goal → generate ontology, create project |
| POST | `/build` | Start KG build from a project (returns task_id immediately) |
| GET | `/task/{task_id}` | Poll background task progress |
| GET | `/data/{graph_id}` | Get all nodes + edges for D3 visualisation |
| GET | `/project/{project_id}` | Get project state |
| GET | `/project/list` | List all projects |
| DELETE | `/project/{project_id}` | Delete project and its graph |
| POST | `/project/{project_id}/reset` | Reset project (clear graph, re-run from scratch) |

### `/api/simulation/` — Simulation Lifecycle

| Method | Path | Description |
|---|---|---|
| POST | `/create` | Create simulation linked to a project |
| POST | `/prepare` | Generate personas + config (background task, returns task_id) |
| POST | `/prepare/status` | Poll preparation task progress and real-time profile count |
| GET | `/{id}` | Get full simulation state |
| GET | `/list` | List all simulations |
| GET | `/history` | Enriched list for history dashboard (with run stats) |
| GET | `/{id}/profiles` | Get all persona profiles |
| GET | `/{id}/profiles/realtime` | Get live count + partial profiles during generation |
| GET | `/{id}/config` | Get simulation_config.json |
| GET | `/{id}/config/realtime` | Get config with generation stage info |
| POST | `/start` | Launch OASIS subprocess (twitter / reddit / parallel) |
| POST | `/stop` | Gracefully stop a running simulation |
| GET | `/{id}/run-status` | Poll live simulation progress (round, counts, platform status) |
| GET | `/{id}/run-status/detail` | Run status with full agent action arrays |
| GET | `/{id}/actions` | Paginated action log |
| GET | `/{id}/timeline` | Per-round action summary |
| GET | `/{id}/agent-stats` | Per-agent action count breakdown |
| GET | `/{id}/posts` | Posts from SQLite (twitter or reddit) |
| GET | `/{id}/comments` | Comments from Reddit SQLite |

### `/api/simulation/` — Agent Interview

| Method | Path | Description |
|---|---|---|
| POST | `/interview` | Send a question to a single specific agent |
| POST | `/interview/batch` | Send questions to multiple agents |
| POST | `/interview/all` | Send the same question to all agents (optionally filtered by platform) |
| POST | `/interview/history` | Retrieve past interview responses |
| POST | `/env-status` | Check if OASIS env is alive for interviews |
| POST | `/close-env` | Close the simulation environment |

### `/api/simulation/` — A/B Campaign Testing

| Method | Path | Description |
|---|---|---|
| POST | `/assign_segments` | Classify personas into named audience segments |
| POST | `/launch_variant` | Launch a single channel variant subprocess (internal use) |
| GET | `/variant_status/{variant_sim_id}` | Poll status of a single variant |
| POST | `/ab_test` | Launch full A/B campaign (all variants in parallel) |
| GET | `/ab_status/{campaign_id}` | Poll all variant statuses for a campaign |
| POST | `/campaign_recommendations` | Score variants + generate recommendation report (background) |
| GET | `/campaign_report/{campaign_id}` | Retrieve the generated report |
| GET | `/campaign_report/{campaign_id}?format=markdown` | Download report as Markdown file |
| GET | `/campaigns` | List all past A/B campaigns (sorted newest first) |

### `/api/report/` — Report Generation

| Method | Path | Description |
|---|---|---|
| POST | `/generate` | Start single-simulation report generation (returns report_id) |
| GET | `/generate/status` | Poll report generation progress |
| GET | `/{report_id}` | Get complete report |
| GET | `/{report_id}/agent-log` | Get ReACT agent step log (paginated by `from_line`) |
| GET | `/{report_id}/console-log` | Get raw process log (paginated by `from_line`) |
| POST | `/chat` | Ask a follow-up question about the report |

---

## 16. Key Design Decisions & Rationale

### Why Multi-Agent Simulation for Marketing Research?

Traditional predictive models treat customers as aggregate statistics. Multi-agent simulation treats them as autonomous individuals — each with their own profile, preferences, social connections, and context. This enables:

- **Emergent social behaviour**: An agent can see what another agent posted (repost chains, social proof effects), which a static statistical model cannot capture
- **Individual explainability**: You can interview each simulated persona and ask why they responded the way they did — impossible with any analytics model
- **Segment granularity**: Results break down by persona group, not just overall averages
- **Format and tone sensitivity**: Different content formats and tones produce measurably different per-persona reactions because each agent's persona guides its LLM decision

### Why Build a Local Knowledge Graph Instead of Using a Cloud Service?

An earlier version of the system used the Zep Cloud API. The current implementation replaces it with a fully local, self-hosted SQLite-based knowledge graph.

**Reasons for the change:**
- **No external API dependency**: The system works offline and does not require Zep API keys or a network connection to function
- **Cost**: Zep Cloud charges per node/query; local SQLite has no marginal cost
- **Data privacy**: Brand briefs and competitive intelligence never leave the server
- **Portability**: A single `.db` file per graph — copy it, delete it, back it up trivially
- **Control**: Full ability to customise the schema, add columns, or change the search algorithm

The `KGClient` class was designed as a drop-in replacement for the Zep SDK — it exposes the identical method namespace (`client.graph.node.get_by_graph_id`, `client.graph.edge.get_by_graph_id`, `client.graph.search`, etc.) and returns the same types (`KGNode`, `KGEdge`, `KGSearchResult`). This allowed migrating from Zep to local SQLite without changing a single line in any of the calling services.

### Why Subprocesses for Simulations?

OASIS simulations use Python's async event loop extensively. Running them in threads would interfere with Flask's threading model and create GIL contention with concurrent API requests. Subprocesses provide:

- Complete isolation — one crashed simulation cannot affect the Flask server
- True parallelism — N variants run simultaneously limited only by CPU
- Clean teardown — killing a subprocess is atomic and reliable
- Separate memory spaces — no risk of shared state corruption

### Why JSONL (Line-Delimited JSON) for Action Logs?

- **Append-only writes**: The simulation subprocess only ever appends to the file, which is safe on POSIX filesystems
- **Concurrent reads**: The Flask API reads from the same file while the simulation writes to it — with append-only semantics this is safe
- **No locking required**: JSONL avoids the need for any file-level mutex
- **Streamable**: The frontend can poll for "new lines since last poll" using byte offsets or line counts
- **Human readable**: Debugging is straightforward — open the file in any text editor

### Why ReACT for Report Generation?

A single LLM prompt asking "which variant is best?" over raw score numbers produces generic, unhelpful output. The ReACT pattern forces the agent to:

1. Use domain-specific analytical tools (comparison table, segment breakdown, channel analysis, format ranking) rather than reasoning from memory
2. Build up evidence before drawing conclusions
3. Produce a traceable reasoning trail (the tool call log is saved with the report)
4. Write specific, evidence-cited recommendations ("Variant 1 achieved 38.5% engagement vs 28.9% for Variant 2") rather than vague ones

### Why File-Based Persistence (JSON + JSONL) Instead of a Database?

- **Zero setup**: No database server to configure, migrate, or maintain
- **Restart resilience**: The server can be restarted at any time without losing any data — all state is in files
- **Debuggability**: Any simulation state can be inspected by opening a JSON file
- **Simplicity**: No ORM, no migrations, no query language to manage
- **History**: The history dashboard works by simply listing and reading JSON files in the `uploads/` directory

---

## 17. End-to-End Example Scenario

**Scenario:** FreshBrew Coffee — Cold Brew Concentrate, New Product Launch

### Input (Uploaded Brand Brief)

> Brand: FreshBrew Coffee
> Product: Cold Brew Concentrate, Zero Sugar
> Price: $9.99 / 250ml
> USP: Premium quality, ready in 30 seconds
> Target: Urban professionals, 25–40 years old
> Channels planned: Instagram, Email
> Budget: $50,000
> Key competitors: Starbucks RTD, La Colombe Draft Latte, Minor Figures

### Phase 1 Output — Knowledge Graph Entities

After processing the brand brief, the knowledge graph contains (approximately):

**Nodes (entities):**
- Brand: FreshBrew Coffee
- Product: Cold Brew Concentrate
- Customer Segments: Urban Professionals, Gym-Goers, Remote Workers, Busy Parents
- Channels: Instagram, Email
- Content Formats: VideoAd, CarouselPost, EmailNewsletter
- Competitors: Starbucks RTD, La Colombe, Minor Figures
- Values: Convenience, Health-consciousness, Premium quality

**Edges (relationships):**
- FreshBrew Coffee `TARGETS` Urban Professionals
- Campaign `DISTRIBUTED_ON` Instagram
- Urban Professionals `RESPONDS_TO` VideoAd
- FreshBrew Coffee `COMPETES_WITH` Starbucks RTD

### Phase 2 Output — Sample Generated Personas

The system generates 30–45 personas. Three examples:

| | Alex Chen | Sarah Mitchell | Mike Thompson |
|---|---|---|---|
| Age | 28 | 32 | 35 |
| Gender | Male | Female | Male |
| Profession | Marketing Manager | UX Designer | Software Engineer |
| MBTI | ENTJ | INFJ | INTJ |
| Location | London | NYC | Toronto |
| Profile | Daily commuter, coffee enthusiast, high Instagram engagement, values speed | Wellness-focused, email subscriber, values sustainability and quality | Convenience-driven, price-conscious, low social engagement |

### Phase 3 — Campaign Variants Defined

| | Variant 1 | Variant 2 | Variant 3 |
|---|---|---|---|
| **Name** | "Speed" VideoAd | "Lifestyle" Carousel | "Quality" Email |
| **Channel** | Instagram | Instagram | Email |
| **Format** | VideoAd | CarouselPost | EmailNewsletter |
| **Headline** | "Zero Sugar. Zero Wait." | "The coffee that matches your pace" | "Your mornings just got better" |
| **CTA** | "Try it — 20% off" | "Shop now" | "Get 20% off your first order" |
| **Tone** | Playful | Playful | Professional |
| **Segment** | Urban Professionals | All personas | All personas |
| **Rounds** | 10 | 10 | 10 |

All three launch in parallel subprocesses.

### Phase 4 — Simulation Results

| Variant | Engagement Rate | Trend |
|---|---|---|
| Variant 1 — Instagram VideoAd | **35.2%** | ↑ Improving |
| Variant 2 — Instagram Carousel | **28.9%** | → Flat |
| Variant 3 — Email Newsletter | **19.4%** | ↓ Declining |

### Phase 5 — Campaign Report Agent Recommendation

**Top Recommendation:** Launch Variant 1 — Instagram VideoAd targeting Urban Professionals

**Evidence:**
- 35.2% engagement rate vs. 28.9% (carousel) and 19.4% (email)
- Improving trend across 10 rounds — brand recall building over time
- Urban Professionals segment responded 1.4× more on Instagram than email for this product category
- VideoAd format generated 2.3× more reposts than CarouselPost
- Gym-Goers sub-segment showed 41% engagement with Variant 1 (highest of any segment/variant combination)

**Actionable Steps (from report):**
1. (**High confidence**) Allocate 70% of Instagram budget to VideoAd format targeting Urban Professionals and Gym-Goers
2. (**High confidence**) Run CarouselPost as a brand-awareness supporting creative (not primary)
3. (**Medium confidence**) Use Email as a re-engagement channel for existing subscribers only — not for new audience acquisition

---

## 18. Full Technology Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| Frontend Framework | Vue.js | 3.5.x | Single-Page Application |
| Frontend Build | Vite | 7.x | Build tooling, HMR |
| Frontend Router | Vue Router | 4.x | Client-side navigation |
| Frontend HTTP | Axios | 1.14 | API calls with retry logic |
| Frontend Visualisation | D3.js | 7.9 | Force-directed KG graph |
| Frontend i18n | Vue I18n | 11.x | English / Chinese UI |
| Backend Framework | Flask | 3.0+ | REST API server |
| Backend Language | Python | 3.11–3.12 | Server runtime |
| LLM SDK | OpenAI Python SDK | 1.0+ | LLM calls (any compatible endpoint) |
| Simulation Engine | CAMEL-AI OASIS | 0.2.5 | Multi-agent social simulation |
| Knowledge Graph | Local SQLite | — | Default KG backend (KG_BACKEND=local) |
| KG Embeddings | OpenAI-compatible API | — | `text-embedding-3-small` |
| KG Search | Custom RRF | — | Cosine + BM25 + RRF (no external library) |
| Document Parsing | PyMuPDF | 1.24+ | PDF text extraction |
| Data Validation | Pydantic | 2.0+ | Schema validation |
| Simulation DB | SQLite | — | OASIS trace tables (posts, comments) |
| CORS | flask-cors | 6.0+ | Cross-origin handling |
| Dependency Manager | uv | — | Fast Python dependency management |
| JS Package Manager | npm | — | Node dependency management |
| LLM Model (Primary) | Qwen-plus (Alibaba) | — | Via Bailian Platform API |
| LLM Model (Alt) | gpt-4o-mini / gpt-4o | — | OpenAI API |

---

## 19. Academic Research Context & Citations

### Primary Research Areas

**Artificial Intelligence & Multi-Agent Systems**
- Large Language Models (LLMs) as autonomous agents with persistent persona
- Multi-agent systems for social simulation and emergent behaviour
- ReACT (Reasoning + Acting) architecture for tool-augmented LLM agents
- Agent-based modelling (ABM) in social science contexts

**Marketing & Consumer Behaviour**
- Rogers' Diffusion of Innovations — how new products spread through social networks
- Customer segmentation and targeting strategies
- Social proof and peer influence in digital marketing decisions
- Cross-channel campaign attribution models
- A/B testing methodology, statistical validity, and minimum detectable effects

**Knowledge Representation & Retrieval**
- Graph databases vs. relational databases for AI applications
- GraphRAG — Retrieval-Augmented Generation with knowledge graphs
- Ontology engineering for domain-specific knowledge extraction
- Hybrid retrieval: dense (vector) + sparse (BM25) + Reciprocal Rank Fusion

**Simulation in Business Research**
- Digital twin technology for marketing and product design
- Synthetic data generation for pre-launch research
- Discrete event simulation vs. agent-based simulation for market research

### Recommended Citations

| Paper / Source | Authors | Year | Relevance |
|---|---|---|---|
| "OASIS: Open Agent Social Intelligence Simulation" | CAMEL-AI Team | 2024 | The simulation engine used directly in this system |
| "Generative Agents: Interactive Simulacra of Human Behavior" | Park et al. (Stanford) | 2023 | Foundational work on LLM personas in interactive environments |
| "Out of One, Many: Using Language Models to Simulate Human Samples" | Argyle et al. | 2023 | LLMs as proxies for human survey respondents |
| "Large Language Models as Simulated Economic Agents" | Horton | 2023 | LLMs making economic decisions like humans |
| "From Local to Global: A Graph RAG Approach to Query-Focused Summarization" | Edge et al. (Microsoft) | 2024 | GraphRAG methodology |
| "ReAct: Synergizing Reasoning and Acting in Language Models" | Yao et al. | 2022 | ReACT architecture used by the report agents |
| "Diffusion of Innovations" | Rogers | 1962 (5th ed. 2003) | Foundational marketing diffusion theory |
| "An Introduction to Agent-Based Modeling" | Wilensky & Rand | 2015 | ABM methodology reference |

---

## 20. Environment & Deployment Configuration

### Required Environment Variables

Create a `.env` file in the project root (`CampaignSim/.env`):

```env
# LLM Configuration (required)
LLM_API_KEY=sk-your-api-key-here
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1   # Qwen
# LLM_BASE_URL=https://api.openai.com/v1                          # OpenAI
LLM_MODEL_NAME=qwen-plus

# Knowledge Graph Backend (default: local)
KG_BACKEND=local

# Only required when KG_BACKEND=zep
# ZEP_API_KEY=

# Optional overrides
OASIS_DEFAULT_MAX_ROUNDS=10
REPORT_AGENT_MAX_TOOL_CALLS=5
REPORT_AGENT_TEMPERATURE=0.5
```

### Directory Structure That Gets Created at Runtime

```
CampaignSim/
└── uploads/
    ├── knowledge_graphs/       ← SQLite .db files, one per graph_id
    ├── projects/               ← Project JSON files (proj_*.json)
    ├── simulations/            ← Simulation directories (sim_*/...)
    ├── campaigns/              ← Campaign JSON files (camp_*.json)
    └── reports/                ← Report JSON files
```

### Deployment

The system is containerised with Docker Compose:
- **Frontend**: Node.js 18+, Vite dev server (port 5173) or static build
- **Backend**: Python 3.11+, Flask on port 5001
- **No internal database server**: SQLite and JSON file persistence only
- **External dependency (optional)**: LLM API (OpenAI-compatible SaaS)

---

## 21. Diagram Specifications for Visual Team

Use the descriptions below to create accurate diagrams. All details are verified against the codebase.

### Diagram 1 — Three-Tier System Architecture

**Type:** Layered box diagram

**Layers (top to bottom):**
1. **Web Browser** — Vue 3 + Vite frontend. Label with: 5-phase workflow UI, D3.js KG visualisation, real-time simulation feed, recommendation report viewer, agent interview panel
2. **Flask Backend** — REST API + Services layer. Label Blueprints: `graph.py`, `simulation.py`, `report.py`. Inside, show a Services box with: `OntologyGenerator`, `GraphBuilderService`, `OasisProfileGenerator`, `SimulationRunner`, `VariantRunner`, `VariantScorer`, `CampaignReportAgent`
3. **Storage & Computation** — Three parallel boxes:
   - **Local SQLite KG** (one `.db` per graph — nodes, edges, episodes, ontology)
   - **LLM API** (OpenAI-compatible — extraction, persona gen, config gen, report gen, embeddings)
   - **OASIS Subprocess** (four scripts: twitter, reddit, parallel, channel — outputs SQLite + JSONL)

**Connections:** Browser ↔ Flask: REST HTTP/JSON. Flask → SQLite KG: direct Python SQLite3. Flask → LLM: HTTP/JSON (OpenAI SDK). Flask → OASIS: subprocess.Popen; OASIS → Flask: writes JSON/JSONL files; Flask reads files.

---

### Diagram 2 — End-to-End User Workflow

**Type:** Vertical linear flowchart with 5 swim lanes

**Lane 1 — User Action:** Upload docs → Review KG → Review personas → Define variants → View report
**Lane 2 — Frontend:** File upload form → D3 graph (polls every 10s) → Profile cards → Variant builder → Recommendation card
**Lane 3 — Flask API:** `POST /ontology/generate` → `POST /build` → `POST /prepare` → `POST /ab_test` → `POST /campaign_recommendations`
**Lane 4 — LLM Calls:** Ontology extraction → Entity/edge extraction (per chunk) → Persona generation (async parallel) → Config generation → Report generation (ReACT)
**Lane 5 — Storage:** `project.json` → `{graph_id}.db` → `twitter_profiles.csv` + `simulation_config.json` → `actions.jsonl` (per variant) → `campaign_report` in `{campaign_id}.json`

---

### Diagram 3 — Knowledge Graph Entity-Relationship Map

**Type:** ER/Graph diagram

**Nodes (use colour coding by type):**
- Brand (blue)
- Product (blue)
- CustomerPersona (green — multiple instances)
- MarketingChannel (orange — Instagram, Email, etc.)
- ContentFormat (orange — VideoAd, Carousel, etc.)
- Competitor (red)
- Influencer (purple)

**Directed edges (labelled):**
- Brand → Product: `SELLS`
- Brand → Competitor: `COMPETES_WITH`
- CustomerPersona → MarketingChannel: `ACTIVE_ON`
- CustomerPersona → ContentFormat: `RESPONDS_TO`
- Influencer → CustomerPersona: `INFLUENCES`

---

### Diagram 4 — OASIS Simulation Round Loop

**Type:** Circular/iterative flow

**Elements:**
1. **Brand Agent (ID 0)** posts campaign content (text: headline + body + CTA) → Round 0
2. **Social Feed** distributed to all persona agents
3. **Each Persona Agent** (1..N) makes a decision: `DO_NOTHING` / `LIKE_POST` / `CREATE_POST` / `REPOST` / `QUOTE_POST` / `FOLLOW`
4. Decision guided by: agent's **persona text** + current **feed content** → **LLM call**
5. All actions appended to **`actions.jsonl`**
6. Agents see other agents' posts in subsequent rounds (emergent social spread)
7. Arrow back to step 3 → Repeat for N rounds (default: 10)
8. After final round → **`env_status.json`** written as `status: completed`

---

### Diagram 5 — Parallel A/B Variant Execution

**Type:** Horizontal parallel lanes (Gantt-style)

**Timeline:** Left = launch time, Right = completion

**Rows:**
- **Flask `/ab_test`** — Single thick bar: receives request, calls VariantRunner, returns campaign_id
- **Variant 1 subprocess** — Runs `run_channel_simulation.py`, writes `actions.jsonl`
- **Variant 2 subprocess** — Parallel, same duration
- **Variant 3 subprocess** — Parallel, same duration
- **`/ab_status` polling** — Small recurring bars (frontend polls every few seconds)
- **`/campaign_recommendations`** — Starts after all variants complete: VariantScorer → CampaignReportAgent
- **Final report available** — Arrow

**Key callout:** Show that Variants 1, 2, 3 run **simultaneously** — not sequentially.

---

### Diagram 6 — Engagement Scoring Formula

**Type:** Visual formula breakdown

**Top section:** Show the 6 action types as labelled blocks with their weights:
- `DO_NOTHING` → 0.0 (grey)
- `LIKE_POST` → 0.3 (light green)
- `CREATE_POST` → 0.35 (green)
- `FOLLOW` → 0.45 (teal)
- `QUOTE_POST` → 0.5 (blue)
- `REPOST` → 0.55 (dark blue)

**Middle section:** Formula box:
```
Engagement Score = Σ(agent_weighted_score) / (num_agents × num_rounds)
Engagement Rate % = Engagement Score × 100
```

**Bottom section:** Example bar chart showing three variants with different scores, labelled with their trend arrows (↑ ↓ →).

---

### Diagram 7 — ReACT Report Agent Loop

**Type:** Numbered flowchart

1. **Initialize** with scored variants + campaign context
2. **LLM Call** → receives `tool_calls` or `final_text`
3. **If `tool_calls`** → execute tool (one of: variant_comparison / segment_insights / channel_effectiveness / content_format_ranking / brand_context)
4. **Append tool result** to conversation as `role: "tool"` message
5. **Go to step 2** (loop, max 5 tool calls)
6. **If `final_text`** → report text generated
7. **Second LLM call** → extract structured `top_recommendation` JSON
8. **Save** report + recommendation + tool_calls_log to campaign JSON

Add a callout box showing the tool call log format: `{"tool": "variant_comparison", "output_preview": "| Variant | Score | ..."}`

---

### Diagram 8 — Data Flow (Input to Output)

**Type:** Horizontal pipeline with data format labels at each stage

```
[PDF / MD / TXT]
      ↓ TextProcessor (500-token chunks, 50 overlap)
[Text Chunks]
      ↓ OntologyGenerator (LLM) → entity_types + edge_types
      ↓ GraphBuilderService → KGClient → SQLiteStore
[knowledge_graphs/{graph_id}.db]
      ↓ ZepEntityReader → filter by type + enrich with edges
[EntityNode list]
      ↓ OasisProfileGenerator (async LLM × N personas)
[twitter_profiles.csv + reddit_profiles.json]
      ↓ SimulationConfigGenerator (LLM) 
[simulation_config.json]
      ↓ SimulationRunner.start_simulation() → subprocess
[OASIS subprocess: N rounds × M agents]
      ↓ append per action
[actions.jsonl]
      ↓ VariantScorer.score_variant()
[Scored Variant Dict (engagement_score, breakdown, trend)]
      ↓ CampaignReportAgent.generate() (ReACT loop)
[campaign_report: report_text + top_recommendation + tool_calls_log]
```

---

*This document was produced by reading the actual v3 codebase: `/campaignsim/frontend/src/` and `/campaignsim/backend/app/`. All technical details, data structures, API paths, config values, and architectural descriptions reflect the code as of June 2026. Discard any earlier documentation if it conflicts with this report.*

---

**Document prepared by:** Abed Mreyan (system author)
**For:** Thesis committee documentation and teammate handoff
**Date:** June 2026
