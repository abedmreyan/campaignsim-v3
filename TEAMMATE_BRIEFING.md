# CampaignSim — Complete Project Briefing
### For: Documentation, Literature Review, Proposal Writing & Visuals
---

## OVERVIEW

This document contains everything needed to write the project proposal, produce technical diagrams, conduct market research, and create the project's literature. It covers the full system concept, architecture, technical design, business case, and domain context.

---

## 1. PROJECT CONCEPT & VISION

### What Is This Project?

**CampaignSim** is an AI-powered marketing campaign simulation and recommendation platform. It allows marketers to test how real customers would react to campaign variants — before spending any budget on actual advertising.

The system creates a high-fidelity digital sandbox where thousands of realistic AI-driven customer personas autonomously interact with campaign content across different channels (Instagram, Email, TikTok, LinkedIn). It outputs ranked recommendations showing which combination of content format, marketing channel, and audience segment will perform best — and why.

### The Core Idea in One Sentence

> Upload a brand brief, get AI-generated customer personas, define campaign variants, run parallel simulations, and receive a ranked recommendation report — all before launching the real campaign.

### Problem Being Solved

Modern marketing teams face three deeply frustrating realities:

1. **Guesswork at scale**: Deciding between a video ad or a carousel post, Instagram or email, playful tone or professional — these decisions are typically made based on gut instinct, small focus groups, or limited past data. The wrong choice wastes thousands of dollars.

2. **A/B testing is expensive and slow**: Real-world A/B tests require actually launching ads, spending budget, and waiting days or weeks for statistically significant results. By then, the market moment may have passed.

3. **No way to understand the "why"**: Even when a campaign succeeds, marketers rarely understand which segment responded, on which channel, to which content element, and why. Traditional analytics show outcomes — not causes.

**CampaignSim solves all three**:
- Simulate thousands of customer reactions before launch
- Compare multiple variants in minutes for $1–2 per simulation
- Get detailed, explainable, AI-generated insight into which audiences respond to what and why

### Target Users

- Marketing managers at small-to-medium businesses launching new products
- Digital marketing agencies managing multi-channel campaigns for clients
- Brand strategists designing campaign playbooks
- Growth marketers running product launches
- Marketing students and educators in campaign strategy courses

### Vision Statement

To become the standard pre-launch testing tool for marketing teams — a simulation layer between campaign ideation and real-world spend, enabling data-driven decisions without requiring data from the market itself.

---

## 2. MARKET RESEARCH CONTEXT

### Market Landscape

The global digital advertising market was valued at approximately **$600 billion in 2024** and is projected to exceed **$870 billion by 2028**. Despite this scale, campaign failure rates remain high — industry research consistently shows that 60–80% of new product campaigns fail to meet their KPIs.

### Competitive Landscape

| Tool | What It Does | What It Lacks |
|------|-------------|----------------|
| **Google Optimize / Optimizely** | A/B testing on live traffic | Requires real audience and real spend |
| **HubSpot / Marketo** | Campaign management and analytics | Post-launch only; no predictive simulation |
| **Persado** | AI-generated copy variants | Does not simulate customer reactions |
| **Brandwatch / Sprout Social** | Social listening and sentiment analysis | Reactive, not predictive |
| **Nielsen Ad Intelligence** | Panel-based campaign testing | Expensive, slow, small panel sizes |
| **Synthetic focus groups (Qualitative AI tools)** | Interview AI personas | Not grounded in brand-specific knowledge graph |

**The gap CampaignSim fills**: No existing tool combines (1) brand-specific knowledge graph construction, (2) LLM-generated customer personas, (3) multi-agent behavioral simulation, and (4) cross-channel, cross-variant recommendation — all within a single low-cost, fast-turnaround workflow.

### Positioning

CampaignSim occupies the space between qualitative insight (focus groups, market research) and quantitative validation (A/B testing). It is:
- **Faster than A/B testing** (minutes vs. weeks)
- **Cheaper than focus groups** ($1–2 per simulation vs. $5,000+ for a focus group)
- **More explainable than predictive analytics models** (you can interview the personas)
- **More grounded than generic AI tools** (the system knows your brand, your product, your competitors)

---

## 3. SYSTEM ARCHITECTURE

### High-Level Architecture Overview

The system has three primary tiers:

```
┌─────────────────────────────────────────────┐
│              WEB FRONTEND (Vue 3)           │
│    5-step guided workflow interface         │
│    D3.js knowledge graph visualization     │
│    Real-time simulation progress display   │
│    Recommendation reports with charts      │
└─────────────────┬───────────────────────────┘
                  │ REST API (HTTP/JSON)
                  ▼
┌─────────────────────────────────────────────┐
│           FLASK BACKEND (Python)            │
│    API routing + business logic             │
│    Orchestration of AI services             │
│    Simulation subprocess management        │
│    Report generation via ReACT loop        │
└────────┬──────────────┬──────────┬──────────┘
         │              │          │
         ▼              ▼          ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│  ZEP CLOUD   │ │ LLM API  │ │  OASIS SIM   │
│ (Knowledge   │ │ (OpenAI/ │ │  ENGINE      │
│  Graph)      │ │  Qwen)   │ │  (Python     │
│              │ │          │ │   subprocess)│
│ - Entities   │ │ - Entity │ │ - Multi-agent│
│ - Relations  │ │   extract│ │   social sim │
│ - Embeddings │ │ - Persona│ │ - SQLite     │
│ - Graph RAG  │ │   gen    │ │   trace log  │
└──────────────┘ │ - Reports│ └──────────────┘
                 └──────────┘
```

### The 5-Step User Workflow

#### Step 1 — Upload Brand Brief & Extract Market Entities

The user uploads a PDF or plain-text brand brief. The system:
- Parses the document (PDF or text)
- Splits content into chunks (500 tokens with 50-token overlap)
- Sends chunks to an LLM to extract a **marketing ontology** — a structured list of entities (brands, products, personas, channels, competitors, formats) and the relationships between them
- Feeds this ontology into **Zep Cloud**, a knowledge graph service, which stores the entities as nodes and relationships as typed edges
- Returns an interactive D3.js graph visualization of the brand's marketing landscape

**Output**: A populated knowledge graph representing the brand's ecosystem.

#### Step 2 — Generate Customer Personas

The system queries the knowledge graph and uses an LLM to generate 30–50 detailed customer personas. Each persona is a full profile including:
- Name, age, gender, profession, location
- Personality type (MBTI), values, lifestyle
- Platform preferences and content engagement habits
- Price sensitivity, brand loyalty, ad response behavior
- A ~1,500-word narrative description of their buying behavior

These personas are stored as CSV-formatted agent profiles — the input format for the simulation engine.

**Output**: A set of AI-generated customer agent profiles representing realistic audience segments.

#### Step 3 — Define Campaign Variants & Run Simulations

The user defines 2–3 campaign variants. Each variant specifies:
- **Content format**: VideoAd, CarouselPost, EmailNewsletter, ShortFormVideo, SponsoredPost
- **Channel**: Instagram, Email, TikTok, LinkedIn
- **Content**: Headline, body copy, call-to-action, visual description, tone
- **Target segment**: A specific persona group (optional; defaults to all)
- **Simulation rounds**: Number of interaction cycles (default: 10)

The system launches all variants **in parallel**. For each variant:
1. A simulation configuration file is generated
2. A Python subprocess runs the OASIS multi-agent simulation engine
3. Agent 0 (the brand) posts the campaign content as a "ManualAction"
4. Agents 1–N (the customer personas) autonomously react over N rounds using LLM-driven decisions
5. Each agent's actions are logged: DO_NOTHING, LIKE_POST, CREATE_POST, FOLLOW, QUOTE_POST, REPOST
6. Results are exported as a structured action log (JSONL format)

**Output**: Parallel action logs per variant, recording every customer persona's response across all simulation rounds.

#### Step 4 — Score Variants & Generate Recommendations

The **Variant Scorer** reads each action log and computes engagement metrics:
- **Engagement score** (0.0–1.0 normalized)
- **Action breakdown** (how many liked, shared, followed, ignored)
- **Per-round trend** (engagement improving, declining, or flat)
- **Per-segment performance** (if segments were defined)
- **Per-channel effectiveness**

A **Campaign Report Agent** then uses a ReACT reasoning loop to:
1. Compare variants using a VariantComparisonTool
2. Analyze segment-level performance using a SegmentInsightTool
3. Evaluate channel effectiveness using a ChannelEffectivenessTool
4. Rank content formats using a ContentFormatRankTool
5. Synthesize findings into a structured recommendation report with rationale

**Output**: Ranked list of variants, engagement scores, segment breakdowns, channel comparisons, and strategic recommendations.

#### Step 5 — Deep Interaction & Export

The user can:
- **Interview personas**: Ask individual agent personas questions like "Why did you engage with Variant 1?" and receive in-character responses
- **Query the report agent**: Ask follow-up questions about the simulation findings
- **Export**: Download results as JSON, CSV, or PDF
- **Review history**: Access past simulation campaigns

---

## 4. DETAILED TECHNICAL DESIGN

### Frontend (Vue 3 SPA)

**Tech Stack**:
- Vue 3 (Composition API + Single File Components)
- Vite 7.x (build tooling)
- Vue Router 4.x (client-side routing)
- Axios 1.14 (HTTP client)
- D3.js 7.9 (interactive graph visualization)
- Vue I18n 11.x (English/Chinese localization)

**Key Views & Components**:

| Component | Role |
|-----------|------|
| `Home.vue` | Landing page, system health status, workflow overview |
| `MainView.vue` | Main app shell with step navigation |
| `Process.vue` | Core 5-step workflow orchestrator |
| `Step1GraphBuild.vue` | Document upload, ontology generation, graph visualization |
| `Step2EnvSetup.vue` | Persona generation UI, persona review cards |
| `Step3Simulation.vue` | Campaign variant builder, simulation launcher |
| `SimulationRunView.vue` | Real-time progress monitoring, per-variant status |
| `Step4Report.vue` / `ReportView.vue` | Ranked recommendations, charts, insights |
| `Step5Interaction.vue` / `InteractionView.vue` | Agent interview, deep query, export |
| `GraphPanel.vue` | Reusable D3.js knowledge graph panel |
| `HistoryDatabase.vue` | Campaign history browser |

**UI/UX Flow**:
- Progressive 5-step wizard
- Real-time streaming feedback during generation (Server-Sent Events or polling)
- Interactive D3.js graph with node coloring by entity type, size by graph degree, tooltips
- Per-variant progress bars during parallel simulation
- Radar charts, bar charts, heatmaps for report visualization

---

### Backend (Flask / Python)

**Tech Stack**:
- Flask 3.0+ (REST API framework)
- Python 3.11–3.12 (runtime)
- OpenAI SDK 1.0+ (LLM client, supports any OpenAI-compatible API)
- CAMEL-AI OASIS 0.2.5 (multi-agent simulation library)
- Zep Cloud SDK 3.13 (knowledge graph and memory)
- PyMuPDF 1.24+ (PDF parsing)
- Pydantic 2.0+ (data validation)
- SQLite (simulation trace storage)
- flask-cors (CORS handling)

**Backend Directory Structure**:

```
backend/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Config constants (action weights, prompts, env)
│   ├── api/
│   │   ├── graph.py             # Graph management API endpoints
│   │   ├── simulation.py        # Core simulation API (30+ endpoints)
│   │   └── report.py            # Report generation endpoints
│   ├── models/
│   │   ├── project.py           # ProjectManager (file-based persistence)
│   │   ├── task.py              # TaskManager (async task tracking)
│   │   └── campaign.py          # CampaignVariant data model
│   ├── services/
│   │   ├── ontology_generator.py         # LLM entity/relation extraction
│   │   ├── graph_builder.py              # Zep graph construction
│   │   ├── zep_entity_reader.py          # Zep graph querying
│   │   ├── oasis_profile_generator.py    # Persona generation
│   │   ├── simulation_runner.py          # OASIS subprocess management
│   │   ├── simulation_manager.py         # Simulation state tracking
│   │   ├── simulation_config_generator.py # Config file generation
│   │   ├── simulation_ipc.py             # Inter-process communication
│   │   ├── text_processor.py             # Document parsing & chunking
│   │   ├── variant_runner.py             # Parallel variant execution
│   │   ├── variant_scorer.py             # Action log scoring engine
│   │   ├── report_agent.py               # ReACT-pattern report agent
│   │   └── campaign_tools.py             # Report agent tool functions
│   └── utils/
│       ├── llm_client.py         # LLM API wrapper
│       ├── file_parser.py        # Document parsing
│       ├── logger.py             # Logging config
│       └── retry.py              # Retry logic
└── scripts/
    └── run_channel_simulation.py # OASIS simulation subprocess script
```

---

### Knowledge Graph Layer (Zep Cloud)

Zep Cloud is used as a **GraphRAG** (Graph Retrieval Augmented Generation) backend. It stores entities as nodes and typed relationships as edges, with vector embeddings for semantic search.

**Marketing Ontology — Entity Types**:

| Entity Type | Description | Key Attributes |
|------------|-------------|----------------|
| `CustomerPersona` | Audience segment with demographics/psychographics | persona_name, age_range, income_level, interests |
| `MarketingChannel` | Distribution channel (Instagram, Email, etc.) | channel_name, typical_audience, format_rules |
| `ContentFormat` | Content type (VideoAd, Carousel, etc.) | format_type, typical_length, engagement_potential |
| `Campaign` | Marketing campaign entity | campaign_name, budget, duration, KPIs |
| `Competitor` | Competing brand | competitor_name, market_position, differentiators |
| `Product` | Product being marketed | product_name, price_point, key_features |
| `Influencer` | Content creator or KOL | influencer_name, follower_count, audience_type |
| `Market` | Geographic or vertical market | market_name, size, growth_rate |
| `Brand` | The brand being analyzed | brand_name, category |

**Relationship Types**:

| Relationship | From → To | Meaning |
|-------------|-----------|---------|
| `TARGETS` | Campaign → CustomerPersona | Campaign aims at this persona segment |
| `DISTRIBUTED_ON` | Campaign → MarketingChannel | Campaign runs on this channel |
| `USES_FORMAT` | Campaign → ContentFormat | Campaign uses this content format |
| `COMPETES_WITH` | Brand → Competitor | Brand competes with this entity |
| `INFLUENCES` | Influencer → CustomerPersona | Influencer reaches this persona |
| `ACTIVE_ON` | CustomerPersona → MarketingChannel | Persona uses this channel |
| `RESPONDS_TO` | CustomerPersona → ContentFormat | Persona engages with this content type |

---

### Multi-Agent Simulation Engine (OASIS)

**OASIS** (Open-source Agent Social Intelligence Simulation) is a CAMEL-AI framework for simulating large-scale social media behavior using LLM-driven agents on a virtual social network platform.

In CampaignSim, OASIS is used to simulate how customer personas react to marketing content.

**How the simulation works**:

1. A simulation configuration file is generated for the variant:
   - Campaign content (headline, body, CTA, format, channel, tone)
   - Agent profile CSV (the generated personas)
   - Number of simulation rounds

2. A Python subprocess runs the simulation script

3. Inside the simulation:
   - A social network graph is constructed with agents as nodes
   - **Agent 0** (the brand) posts the campaign content as a `ManualAction`
   - **Agents 1–N** each receive the post in their "feed" and decide how to respond
   - Each agent's decision is made by an LLM that reasons from the persona's profile
   - Responses are one of: DO_NOTHING, LIKE_POST, CREATE_POST, FOLLOW, QUOTE_POST, REPOST
   - This repeats for N rounds (default 10), with agents also seeing what other agents post
   - All actions are stored in a SQLite trace table

4. After simulation completes, actions are exported to a JSONL file for scoring

**Agent Action Types and Marketing Meaning**:

| Action | Engagement Weight | Marketing Interpretation |
|--------|-----------------|--------------------------|
| `DO_NOTHING` | 0.0 | Saw the ad, scrolled past it |
| `LIKE_POST` | 0.3 | Positive reaction, low commitment |
| `CREATE_POST` | 0.35 | Commented, replied — active interest |
| `FOLLOW` | 0.45 | Followed the brand — purchase intent signal |
| `QUOTE_POST` | 0.5 | Shared with commentary — social amplification |
| `REPOST` | 0.55 | Pure share — strongest virality signal |

---

### Scoring & Recommendation Engine

**Variant Scorer**:

For each campaign variant, the scorer reads the action log and computes:

```
engagement_score = Σ(action_weight × occurrence) / (num_agents × num_rounds)
engagement_rate_pct = engagement_score × 100
```

Additional metrics:
- **Action breakdown**: How many of each action type occurred
- **Trend analysis**: Per-round engagement, classified as improving/declining/flat
- **Per-segment scores**: If personas were assigned to segments
- **Per-channel scores**: If multiple channels were tested

**Report Agent (ReACT Loop)**:

The Report Agent uses a **ReACT (Reasoning + Acting)** architecture:
1. The agent is given all scored variants
2. It reasons about which tools to call (Thought)
3. It calls tools one at a time (Action)
4. It reads tool results (Observation)
5. It repeats until it has enough information for a final report
6. It synthesizes a structured recommendation

**Report Agent Tools**:

| Tool | Purpose |
|------|---------|
| `VariantComparisonTool` | Ranks variants by engagement rate |
| `SegmentInsightTool` | Analyzes which segments prefer which variants |
| `ChannelEffectivenessTool` | Compares channel-level engagement aggregates |
| `ContentFormatRankTool` | Ranks content formats by engagement performance |

**Report Output Structure**:
```
1. Executive Summary (top recommendation with rationale)
2. Ranked Variant Table (all variants with engagement scores)
3. Segment Performance Matrix (segment × variant engagement heatmap)
4. Channel Effectiveness Summary (channel rankings)
5. Content Format Rankings (format performance comparison)
6. Trend Analysis (improving/declining/flat per variant)
7. Strategic Recommendations (actionable next steps)
```

---

## 5. DATA MODELS

### Campaign Variant Model

```
CampaignVariant:
  variant_id:        Unique identifier (UUID)
  variant_name:      Human-readable label
  channel:           instagram | email | tiktok | linkedin
  content:
    format:          VideoAd | CarouselPost | EmailNewsletter | ShortFormVideo | SponsoredPost
    headline:        Campaign headline text
    body:            Main body copy
    cta:             Call-to-action text
    visual_desc:     Description of visual elements
    email_subject:   Email subject line (email channel only)
    tone:            playful | professional | urgent | neutral
  target_segment:    Segment name (empty = all personas)
  max_rounds:        Number of simulation rounds (default: 10)
  status:            pending | running | completed | failed
  simulation_id:     Link to associated simulation run
  output_dir:        Path to action log files
```

### Customer Persona Profile

```
PersonaProfile:
  user_id:           Integer agent ID
  user_name:         Social handle (e.g. @alex_m)
  name:              Display name
  bio:               Short bio (1-2 sentences)
  persona:           Full ~1,500-word behavioral narrative
  age:               Integer age
  gender:            male | female | non-binary
  mbti:              MBTI type (ENTJ, INFJ, etc.)
  country:           ISO country code
  profession:        Job title
  interested_topics: List of interest categories
  karma:             Social influence score (0-100)
  friend_count:      Network connections
  follower_count:    Follower count
  segment:           Assigned market segment label
```

### Simulation Action Log (JSONL, one action per line)

```json
{
  "variant_id": "v1",
  "channel": "instagram",
  "agent_id": 1,
  "action_type": "LIKE_POST",
  "info": {},
  "timestamp": "2026-05-07T10:23:01"
}
```

### Scored Variant Output

```json
{
  "variant_id": "v1",
  "variant_name": "VideoAd on Instagram — Millennials",
  "channel": "instagram",
  "content_format": "VideoAd",
  "target_segment": "MillennialProfessionals",
  "tone": "playful",
  "total_agents": 30,
  "total_actions": 85,
  "engagement_score": 0.3567,
  "engagement_rate_pct": 35.67,
  "action_breakdown": {
    "DO_NOTHING": 40,
    "LIKE_POST": 25,
    "CREATE_POST": 10,
    "REPOST": 7,
    "QUOTE_POST": 2,
    "FOLLOW": 1
  },
  "per_round_engagement": [0.25, 0.28, 0.32, 0.35, 0.38],
  "trend": "improving"
}
```

---

## 6. API ENDPOINTS REFERENCE

### Graph Management `/api/graph/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload brand brief document |
| GET | `/<graph_id>` | Get graph metadata |
| GET | `/<graph_id>/relations` | Get all relationships in graph |
| GET | `/<graph_id>/search` | Semantic search graph nodes |
| POST | `/<graph_id>/update-from-sim` | Update graph post-simulation |

### Simulation Core `/api/simulation/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/create` | Create a new simulation project |
| POST | `/prepare` | Trigger ontology + graph build |
| POST | `/prepare/status` | Poll preparation progress |
| GET | `/list` | List all simulation projects |
| GET | `/<simulation_id>` | Get simulation details |
| GET | `/history` | Get simulation history |

### Persona Management `/api/simulation/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/generate-profiles` | Generate customer personas |
| GET | `/<simulation_id>/profiles` | Get all agent profiles |
| GET | `/<simulation_id>/profiles/realtime` | Stream profile generation progress |

### Simulation Execution `/api/simulation/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/start` | Launch simulation run |
| POST | `/ab_test` | Launch multi-variant A/B test |
| POST | `/stop` | Stop a running simulation |
| GET | `/<simulation_id>/run-status` | Poll simulation progress |
| POST | `/assign_segments` | Assign personas to named segments |
| GET | `/<variant_id>/results` | Retrieve variant action log |

### Report & Analysis `/api/report/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/generate` | Generate full recommendation report |
| GET | `/<report_id>` | Retrieve a generated report |
| POST | `/interview` | Interview a specific persona agent |

---

## 7. SYSTEM DIAGRAMS TO CREATE

The following diagrams are recommended for documentation, reports, and presentations. Use the details in this document to build each one accurately.

### 7.1 System Architecture Diagram
A layered architecture diagram showing:
- **Top layer**: Vue 3 Frontend (browser)
- **Middle layer**: Flask Backend (API + Services)
- **Bottom layer**: Three external services: Zep Cloud, LLM API (OpenAI/Qwen), OASIS Engine
- Annotate each layer with its technology stack and key responsibilities
- Show REST API connections between frontend and backend
- Show service calls from backend to external services

### 7.2 User Workflow / Process Diagram
A 5-step vertical flowchart:
1. Upload Brand Brief → PDF parsing → Ontology Generation
2. Knowledge Graph Build → Zep Cloud → D3.js Visualization
3. Persona Generation → 30–50 AI Customer Profiles → CSV
4. Campaign Variant Definition → Parallel Simulation Launch → Action Logs
5. Scoring → Report Agent (ReACT) → Ranked Recommendations

### 7.3 Knowledge Graph Entity-Relationship Diagram
A visual ER diagram with:
- Nodes: CustomerPersona, MarketingChannel, ContentFormat, Campaign, Competitor, Product, Influencer, Market, Brand
- Edges: TARGETS, DISTRIBUTED_ON, USES_FORMAT, COMPETES_WITH, INFLUENCES, ACTIVE_ON, RESPONDS_TO
- Use different colors for entity types; show direction of relationships with arrows

### 7.4 Simulation Mechanics Diagram
A diagram of the OASIS simulation loop:
- Brand Agent (Agent 0) posts campaign content
- Customer Agents (1..N) receive the post in their feed
- Each agent decides: DO_NOTHING / LIKE / POST / FOLLOW / SHARE
- Actions are logged to SQLite trace
- Repeat for N rounds
- Action log exported to JSONL

### 7.5 Parallel Variant Execution Diagram
A concurrency diagram showing:
- User defines Variant 1, Variant 2, Variant 3
- All three variants launch simultaneously (ThreadPoolExecutor)
- Each variant runs its own OASIS subprocess
- Each variant writes its own action log
- Variant Scorer collects and scores all logs
- Report Agent synthesizes final recommendations

### 7.6 Engagement Scoring Formula Diagram
A visual explanation of the scoring model:
- Show the 6 action types with their weights (0.0 to 0.55)
- Show the engagement rate formula
- Show per-round trend line example
- Show how per-segment scores break down from the full score

### 7.7 ReACT Report Agent Loop
A flowchart of the reasoning loop:
1. Initialize with scored variants
2. Thought: "I should compare variant engagement rates"
3. Action: Call VariantComparisonTool
4. Observation: Ranking with scores
5. Thought: "I should check segment performance"
6. Action: Call SegmentInsightTool
7. ...continue until report complete...
8. Final Answer: Structured recommendation report

### 7.8 Data Flow Diagram
An end-to-end data flow from:
- **Input**: PDF brand brief
- → Text chunks → LLM → Ontology JSON → Zep Graph
- → Graph query → LLM → Persona CSV
- → Persona CSV + Campaign config → OASIS subprocess → SQLite trace → JSONL
- → JSONL → VariantScorer → Scored variants JSON
- → Scored variants + tools → ReACT agent → Report JSON
- **Output**: Ranked recommendation report + visualization

---

## 8. FULL TECHNOLOGY STACK SUMMARY

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Frontend Framework | Vue.js | 3.5.x | SPA web interface |
| Frontend Build | Vite | 7.x | Build tooling and dev server |
| Frontend Router | Vue Router | 4.x | Client-side routing |
| Frontend HTTP | Axios | 1.14 | API calls |
| Frontend Visualization | D3.js | 7.9 | Interactive graph visualization |
| Frontend i18n | Vue I18n | 11.x | English/Chinese UI |
| Backend Framework | Flask | 3.0+ | REST API server |
| Backend Language | Python | 3.11–3.12 | Backend runtime |
| LLM SDK | OpenAI SDK | 1.0+ | OpenAI-compatible LLM calls |
| Multi-Agent Simulation | CAMEL-AI OASIS | 0.2.5 | Social behavior simulation |
| Knowledge Graph | Zep Cloud SDK | 3.13 | GraphRAG entity/relation store |
| Document Parsing | PyMuPDF | 1.24+ | PDF text extraction |
| Data Validation | Pydantic | 2.0+ | Schema validation |
| Database | SQLite | — | Simulation trace storage |
| CORS | flask-cors | 6.0+ | Cross-origin handling |
| Containerization | Docker + Compose | — | Deployment |
| Python Package Manager | uv | — | Fast Python dependency management |
| JS Package Manager | npm | — | Node dependency management |
| LLM Model (Primary) | Qwen-plus (Alibaba) | — | Via Bailian Platform |
| LLM Model (Alt) | gpt-4o-mini / gpt-4o | — | OpenAI |

---

## 9. KEY DESIGN DECISIONS & RATIONALE

### Why Multi-Agent Simulation for Marketing?

Traditional predictive models treat customers as aggregate statistics. Multi-agent simulation treats them as autonomous individuals — each with their own profile, preferences, and social context. This enables:
- **Emergent behavior**: Some agents influence others (repost chains, social proof)
- **Explainability**: You can ask each agent why they responded as they did
- **Segment granularity**: Results break down by persona group, not just averages
- **Format sensitivity**: Different content formats produce measurably different agent behaviors

### Why a Knowledge Graph (Zep) Instead of a Vector Database?

A vector database stores embeddings for semantic search. A knowledge graph stores **structured relationships** between named entities. For marketing simulation, the graph is more powerful because:
- It explicitly models who targets whom (Campaign → CustomerPersona)
- It captures competitive dynamics (Brand → Competitor)
- It encodes distribution logic (Campaign → Channel)
- These structured relationships can be used to ground persona generation and constrain LLM output

### Why Run Variants in Parallel?

Marketing campaigns involve trade-offs between variables (channel, format, tone, segment). Running variants sequentially would take too long and lose the comparative value. Parallel execution via `concurrent.futures.ThreadPoolExecutor` allows all variants to complete in the same time as a single run, making the system viable for real-time use.

### Why ReACT for the Report Agent?

A single-shot LLM prompt asking "which variant is best?" would produce generic analysis. ReACT forces the agent to use purpose-built analytical tools (comparison, segment analysis, channel analysis, format ranking) and reason step-by-step before synthesizing a recommendation. This produces more accurate, traceable, and defensible output.

### Why OASIS for the Simulation Engine?

OASIS is purpose-built for LLM-driven social network simulation. It provides:
- Agent graph construction from profile CSVs
- Built-in action type schema (DO_NOTHING, LIKE, REPOST, etc.)
- Multi-round simulation with agent-to-agent interactions
- SQLite trace table for full audit log

Adapting OASIS to marketing channels avoids building a simulation engine from scratch while leveraging its proven agent interaction model.

---

## 10. EXAMPLE END-TO-END SCENARIO

**Scenario**: FreshBrew Cold Brew Coffee — New Product Launch

### Input Brief (Uploaded PDF Summary):
- Brand: FreshBrew Coffee
- Product: Cold Brew Concentrate, Zero Sugar
- Price Point: $9.99 / 250ml
- USP: Premium quality, ready in 30 seconds
- Target Markets: Urban professionals, 25–40 years old
- Planned Channels: Instagram, Email
- Budget: $50,000
- Competitors: Starbucks RTD, La Colombe Draft Latte, Minor Figures

### Step 1 Output — Knowledge Graph Entities:
- **Brand**: FreshBrew Coffee
- **Product**: Cold Brew Concentrate
- **Personas**: Urban Professionals, Gym-Goers, Remote Workers
- **Channels**: Instagram, Email
- **Formats**: VideoAd, CarouselPost, EmailNewsletter
- **Competitors**: Starbucks RTD, La Colombe, Minor Figures
- **Edges**: FreshBrew TARGETS Urban Professionals; Campaign DISTRIBUTED_ON Instagram...

### Step 2 Output — Sample Generated Personas:
- **Alex, 28M**: Marketing Manager, ENTJ, London — daily commuter, coffee enthusiast, high Instagram engagement
- **Sarah, 32F**: UX Designer, INFJ, NYC — wellness-focused, email subscriber, values sustainability
- **Mike, 35M**: Software Engineer, INTJ, Toronto — convenience-driven, price-conscious, low social engagement

(System generates 30–40 full personas like these)

### Step 3 — Campaign Variants Defined:

| | Variant 1 | Variant 2 | Variant 3 |
|--|-----------|-----------|-----------|
| **Name** | "Speed" VideoAd | "Lifestyle" Carousel | "Quality" Email |
| **Channel** | Instagram | Instagram | Email |
| **Format** | VideoAd | CarouselPost | EmailNewsletter |
| **Headline** | "Zero Sugar. Zero Wait." | "The coffee that matches your pace" | "Your mornings just got better" |
| **CTA** | "Try it — 20% off" | "Shop now" | "Get 20% off your first order" |
| **Tone** | Playful | Playful | Professional |
| **Target** | Urban Professionals | All | All |

### Step 4 — Simulation Results:

| Variant | Engagement Rate | Trend |
|---------|----------------|-------|
| Variant 1 (Instagram VideoAd) | **35.2%** | Improving |
| Variant 2 (Instagram Carousel) | **28.9%** | Flat |
| Variant 3 (Email Newsletter) | **19.4%** | Declining |

### Step 5 — Report Agent Recommendation:

**Top Recommendation**: Launch Variant 1 — Instagram VideoAd targeting Urban Professionals
- 35.2% engagement rate vs. 28.9% (carousel) and 19.4% (email)
- Improving trend over 10 rounds suggests brand recall building
- Urban Professionals engage 1.4x more on Instagram than Email for this product category
- VideoAd format outperforms CarouselPost: likely due to fast visual storytelling matching commuter scroll behavior
- Action: Allocate 70% of Instagram budget to VideoAd format for Urban Professional targeting; run email as supporting re-engagement channel only

---

## 11. DEVELOPMENT PHASES & STATUS

| Phase | Name | Key Deliverables | Status |
|-------|------|-----------------|--------|
| 1 | Core Domain Adaptation | Ontology engine, persona generator, knowledge graph integration, D3.js visualization | Complete |
| 2 | Channel Simulation | OASIS-based multi-channel simulation script, action log export pipeline | In Progress |
| 3 | Campaign Variables & A/B Testing | Variant data model, parallel runner, multi-variant UI, segment assignment | Designed |
| 4 | Recommendation Engine | Variant scorer, report agent tools, engagement metrics, recommendation report | Designed |
| 5 | UI Polish & Evaluation | Charts/heatmaps, onboarding modal, campaign history, expert evaluation study | Designed |

---

## 12. ACADEMIC CONTEXT & RESEARCH ANGLES

The following research areas and topics are relevant for the literature review and theoretical background:

### AI & Multi-Agent Systems
- Large Language Models (LLMs) for autonomous agent behavior
- Multi-agent systems for social simulation
- Emergent behavior in agent-based models
- ReACT reasoning architecture for LLM agents

### Marketing & Consumer Behavior
- Diffusion of innovations (Rogers)
- Customer segmentation and targeting
- Social proof and influence in digital marketing
- Cross-channel campaign attribution models
- A/B testing methodology and statistical validity

### Knowledge Representation
- Graph databases vs. relational databases for AI applications
- GraphRAG: Retrieval-augmented generation with knowledge graphs
- Ontology engineering for domain-specific knowledge extraction
- Entity-relationship modeling for business domains

### Simulation in Business
- Agent-based modeling (ABM) in social science
- Digital twin technology for marketing
- Synthetic data generation for training and simulation
- Discrete event simulation vs. agent-based simulation

### Related Prior Work (Recommended Citations)
- OASIS: Open Agent Social Intelligence Simulation (CAMEL-AI, 2024)
- Park et al., "Generative Agents: Interactive Simulacra of Human Behavior" (Stanford, 2023)
- Argyle et al., "Out of One, Many: Using Language Models to Simulate Human Samples" (2023)
- Horton, "Large Language Models as Simulated Economic Agents" (2023)
- GraphRAG: Microsoft Research (2024)
- Zep: GraphRAG for production AI applications

---

## APPENDIX A: ENVIRONMENT CONFIGURATION

Required environment variables:

```
OPENAI_API_KEY=          # LLM API key (OpenAI or compatible)
OPENAI_API_BASE=         # LLM API base URL (default: https://api.openai.com/v1)
OPENAI_MODEL=            # Model name (e.g. qwen-plus, gpt-4o-mini)
ZEP_API_KEY=             # Zep Cloud API key
```

---

## APPENDIX B: DEPLOYMENT CONFIGURATION

The system is containerized with Docker Compose:
- **Frontend container**: Node.js 18+, Vite dev server or static build
- **Backend container**: Python 3.11+, Flask on port 5001
- **No internal database server needed**: SQLite and JSON file persistence only
- **External dependencies**: Zep Cloud API (SaaS), LLM API (SaaS)

---

*This document was compiled from the full project codebase and implementation documentation. It is accurate as of May 2026.*
