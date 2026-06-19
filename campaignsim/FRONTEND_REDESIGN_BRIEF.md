# CampaignSim — Frontend UI/UX Redesign Brief & Handover Document

**Project**: CampaignSim — AI Marketing Campaign Simulation & Recommendation Platform  
**Live URL**: https://campaignsim.aethersystems.co  
**GitHub**: https://github.com/abedmreyan/campaignsim  
**Document purpose**: Full context handover for a frontend redesign contractor

---

## 1. What CampaignSim Is

CampaignSim is a web application that lets marketing professionals test campaigns before spending budget. The workflow:

1. Upload brand briefs and research documents
2. The system builds a knowledge graph from those documents (entities, relationships)
3. AI agent personas are generated from the knowledge graph (simulated consumers, competitors, influencers)
4. A multi-agent social simulation runs — agents interact on simulated Twitter/Reddit-style platforms, reacting to campaign content
5. An AI analyst generates a structured recommendation report from the simulation results
6. The user can then chat with the AI analyst or interview individual simulated personas

There is also an **A/B campaign testing** flow where users define 2–3 campaign variants (channel, content format, tone, headline, CTA, target segment), launch them in parallel, and get a ranked recommendation report.

The product is a **graduation thesis project** — the demo audience is an academic panel plus potential industry reviewers. It is not a commercial product.

---

## 2. The Redesign Goal

The current frontend is entirely custom-built from scratch — no component library, raw scoped CSS per component, heavy on monospace type. It is functional but visually inconsistent, hard to navigate on first use, and under-communicates the sophistication of what's happening in the backend.

**The redesign should achieve**:
- A polished, professional SaaS-grade UI that reads as a credible research tool
- Clear visual communication of system state (what is running, what is waiting, what is done)
- Better information hierarchy — the current UI surfaces too many technical IDs and internal values that the end user does not need
- Consistent spacing, color, and type system across all 6 workflow steps
- The D3 knowledge graph visualization should remain — it is a key differentiator

**What must NOT change**:
- The Vue 3 component architecture and routing (do not restructure pages)
- The API integration layer (`src/api/`) — all endpoints are working
- The D3 graph panel (GraphPanel.vue) — can be restyled but not re-engineered
- The 6-step workflow sequence — the flow is correct, only the presentation needs work

---

## 3. Tech Stack (Do Not Change)

| Layer | Technology |
|---|---|
| Framework | Vue 3 (Composition API) |
| Router | Vue Router 4 |
| i18n | Vue i18n 11 |
| HTTP | Axios (pre-configured in `src/api/index.js`) |
| Graph viz | D3 v7 |
| Build | Vite 7 |
| Fonts | Space Grotesk, JetBrains Mono, Inter (Google Fonts, already loaded) |
| CSS | Scoped CSS per component (no Tailwind, no Bootstrap) |

You may introduce a component library (e.g., Radix Vue, shadcn-vue, or similar headless primitives) but keep it additive — do not remove the API integration or router logic.

---

## 4. Current Design Language

The current design is a minimal black-and-white system with an orange accent:

```
--black:      #000000
--white:      #FFFFFF
--orange:     #FF4500   ← primary accent (brand color, keep or evolve)
--gray-light: #F5F5F5
--gray-text:  #666666
--border:     #E5E5E5

Primary font:  Space Grotesk (body, UI)
Monospace font: JetBrains Mono (IDs, code, metrics)
```

Status colors currently used inline (not tokenized):
- Processing / active: `#FF5722`
- Success / complete: `#4CAF50`
- Error: `#F44336`
- Pending: `#9E9E9E`

The redesign can evolve this palette but should preserve the high-contrast, data-forward character. This is not a colorful consumer app — it should feel like a serious analytical tool.

---

## 5. Application Structure

### Routes

| Path | View | Step | Description |
|---|---|---|---|
| `/` | Home.vue | — | Landing, file upload, history |
| `/process/:projectId` | MainView.vue | 1 + 2 | Graph build + sim setup |
| `/simulation/:simulationId` | SimulationView.vue | 2 alt | Sim preparation alternate entry |
| `/simulation/:simulationId/start` | SimulationRunView.vue | 3 | Live simulation run |
| `/report/:reportId` | ReportView.vue | 4 | AI report generation |
| `/interaction/:reportId` | InteractionView.vue | 5 | Chat with agents/analyst |
| `/campaign/:campaignId/report` | CampaignReportView.vue | — | A/B test results |

### Components (in priority order for redesign)

| Component | Lines | Priority | Description |
|---|---|---|---|
| Home.vue | ~700 | P0 | First impression — landing + upload |
| Step2EnvSetup.vue | 3,049 | P0 | Most complex — persona generation, sim config |
| Step4Report.vue | 5,162 | P0 | Report viewer + agent workflow timeline |
| Step3Simulation.vue | 1,266 | P1 | Live simulation timeline feed |
| Step5Interaction.vue | 2,584 | P1 | Chat + survey interface |
| Step1GraphBuild.vue | 700 | P1 | Ontology + graph build progress |
| GraphPanel.vue | 1,451 | P2 | D3 graph (restyle only, no re-engineer) |
| HistoryDatabase.vue | 1,342 | P2 | History card grid |
| MainView.vue | ~400 | P2 | Split-panel shell (graph + step) |
| Step5CampaignReport.vue | 608 | P3 | A/B results display |
| LanguageSwitcher.vue | 124 | P3 | Locale toggle |

---

## 6. Screen-by-Screen Design Notes

### Screen 1: Home (`/`)

**Current state**: Hero section with large black type, a console-style upload box on the right, and a history grid below. Orange accent button. Monospace tagline.

**Problems**:
- The upload area looks like a terminal — intimidating for non-technical users
- History cards are too small and information-dense
- The workflow explanation (5 steps) is buried below the fold

**Redesign goals**:
- Upload area should feel welcoming — clear drop zone, file type hints, progress feedback
- The simulation requirement textarea needs a stronger prompt — users don't know what to write
- History section should be more visual — show simulation status clearly, make navigation obvious
- The 5-step how-it-works should be prominent and scannable

**Key interactions**:
- File drag-and-drop (multiple files: PDF, MD, TXT)
- Textarea for simulation goal/requirement
- "Start Engine" CTA button
- History card click → modal with navigation options (go to Step 1 / Step 2 / Step 4)

---

### Screen 2: Graph Build + Environment Setup (`/process/:projectId`)

**Current state**: Split-panel layout. Left = D3 graph, Right = step component. A mode switcher (Graph / Split / Workbench) toggles between full-graph, 50/50 split, and full-step views.

**This is the most technically dense screen** — it shows:

**Phase A — Graph Build (Step1GraphBuild.vue)**:
- Progress bar (0–100%) while the knowledge graph builds from the uploaded documents
- Generated entity type tags (CustomerPersona, MarketingChannel, Competitor, etc.) — clickable to see attributes
- Generated relationship type tags (TARGETS, INFLUENCES, COMPETES_WITH, etc.) — clickable to see source/target types
- After completion: node count, edge count, entity type count

**Phase B — Simulation Setup (Step2EnvSetup.vue)** — Three sub-cards:
1. **Simulation Instance**: Shows Project ID, Graph ID, Simulation ID (monospace IDs — currently over-prominent)
2. **Agent Persona Generation**: 
   - Progress counter (e.g., "12 / 40 agents generated")
   - Agent profile cards: username, profession, bio snippet, topic tags
   - Click to expand full profile
3. **Platform Config**: Simulation time config (duration, round count, agents/hour), time-of-day activity multipliers (peak/work/morning/off-peak hours)

**Redesign goals**:
- The mode switcher is confusing — the split layout should be the default and the toggle should be more discoverable
- IDs should be visible but not dominant — small monospace text, not large headers
- Entity/relation tags should be more visual — icon + label, color-coded by category
- Agent persona cards need more personality — the bio text is the interesting part, not the username
- Progress states need clearer visual communication (generating... / done / error)
- The platform config time-buckets are confusing — needs better visual treatment (maybe a 24h timeline bar)

---

### Screen 3: Live Simulation (`/simulation/:simulationId/start`)

**Current state**: Dual-platform timeline feed. Two status bars (Twitter-like "Info Plaza" and Reddit-like "Topic Community") showing round progress, elapsed time, action count. Below: a chronological feed of agent actions (post, comment, like, repost, follow).

**Key data displayed per action card**:
- Agent avatar (letter placeholder)
- Agent name + platform icon
- Action type (CREATE_POST, CREATE_COMMENT, LIKE, REPOST, FOLLOW, QUOTE_POST)
- Content (the post/comment text)
- Round number + timestamp

**Redesign goals**:
- The dual-platform status needs a cleaner visual — progress bars + metrics should be glanceable
- Action cards look like a raw JSON dump — they need to feel like a social feed
- Different action types should have distinct visual treatments (post vs. like vs. follow)
- Live state indication: something that communicates "simulation is actively running" (animations, pulsing, etc.)
- The action content (LLM-generated social posts) is actually interesting — give it more space

---

### Screen 4: Report Generation (`/report/:reportId`)

**Current state**: Side-by-side split. Left = Report document (markdown sections), Right = Agent workflow timeline (live log stream of what the AI analyst is doing).

**Left panel (Report)**:
- Report title + executive summary at top
- Numbered sections in a collapsible list
- Loading spinner on the section currently being written
- Completed sections render full markdown
- The report has ~7–10 sections covering: segment analysis, channel effectiveness, variant comparison, recommendations, risks

**Right panel (Workflow)**:
- Metrics bar: sections done, elapsed time, tool calls made, status pill
- Workflow steps list (each step can be: pending / active / completed)
- Log stream: timestamped events showing tool calls, tool results, thinking steps
- Tool call cards: show tool name, input params, output preview

**Redesign goals**:
- This is the most information-rich screen and needs the most work
- The report document should feel like a proper formatted document — clear heading hierarchy, readable body text, proper spacing
- The workflow panel is interesting but currently feels like raw logs — tool calls should be visually distinct, results should be collapsible
- The two panels compete visually — needs clearer hierarchy (report = primary, workflow = secondary)
- Section generation progress should have better visual metaphors (section list with status icons, not just spinners)
- Print/export-friendly styling consideration for the report

---

### Screen 5: Interaction (`/interaction/:reportId`)

**Current state**: Same left panel as Screen 4 (full report). Right panel has three tabs:
1. Chat with Report Agent — conversational interface with the AI analyst
2. Chat with Agent — dropdown to select a simulated persona, then chat with them
3. Send Survey — form to send structured questions to all agents

**Redesign goals**:
- Chat interfaces need proper message bubble styling (user vs. AI)
- Agent selector dropdown should show avatar + name + profession — make personas feel real
- Survey form needs proper input components
- The tab navigation should be clearer — these are three distinct modes

---

### Screen 6: Campaign A/B Report (`/campaign/:campaignId/report`)

**Current state**: Polling view that waits for parallel campaign simulations to complete, then shows a recommendation report with variant comparisons.

**Key data displayed**:
- Variant results ranked by engagement rate
- Best channel recommendation
- Best content format recommendation
- Best target segment
- Top 3 recommendations with confidence scores (High/Medium/Low)
- Risks and limitations

**Redesign goals**:
- Make this feel like a campaign analytics dashboard
- Variant comparison should be a visual table/chart, not a text list
- Confidence scores should have visual indicators
- The recommendations should be the most prominent element

---

## 7. Global Layout Patterns

### The Main Shell (MainView.vue)

All step screens after Home use a two-panel layout:

```
┌─────────────────────────────────────────────┐
│ HEADER: Logo | Mode toggle | Step | Status  │
├──────────────────────┬──────────────────────┤
│                      │                      │
│   D3 Knowledge       │   Step Component     │
│   Graph Panel        │   (changes per step) │
│   (GraphPanel.vue)   │                      │
│                      │                      │
└──────────────────────┴──────────────────────┘
```

Mode switcher toggles between:
- **Graph** — graph takes 100%, step hidden
- **Split** — 50/50 (default)
- **Workbench** — step takes 100%, graph hidden

The step component is always a right-hand panel. The graph always left.

### Navigation Between Steps

There is **no persistent navigation bar**. Users move forward via buttons inside each step component (e.g., "Proceed to Simulation", "Generate Report", "Go to Interaction"). Back navigation is through the History database on the home screen.

This is intentional for the thesis demo — the system guides users linearly. The redesign should preserve this but make the step position clearer (e.g., a persistent step indicator in the header).

---

## 8. State & Data Flow

- **No global state store** (no Vuex/Pinia). A simple `pendingUpload.js` module passes file + requirement from Home → MainView.
- Router params carry IDs between steps: `projectId → simulationId → reportId`
- **Polling is everywhere**: graph build, agent generation, simulation run, report generation all use `setInterval` polling (2–5 second intervals). The redesign must accommodate loading/polling states gracefully.
- **Long-running operations**: Some steps take 1–10+ minutes (graph build, simulation run). The UI must communicate progress without feeling frozen.

---

## 9. Async Operation States (Design for all of these)

Every major operation has these states:

| State | Current treatment | Redesign should |
|---|---|---|
| `idle` | Empty/blank | Clear CTA, instructions |
| `submitting` | Spinner | Animated indicator, disable inputs |
| `processing` | Progress bar + text | Progress %,  elapsed time, step description |
| `polling` | Repeated status text | Non-intrusive refresh, "checking..." |
| `success` | Green badge | Smooth transition, stats summary |
| `error` | Red text + error message | Clear error, retry option |

The simulation run adds a special state: `running_live` — the simulation is actively executing and the feed is updating in real time. This needs distinct visual treatment from "loading".

---

## 10. API Integration (Do Not Modify)

All API calls are in `/src/api/`. The redesign should only call existing functions — do not write new API calls or modify the request/response handling.

Key API modules:
- `simulation.js` — all simulation lifecycle calls
- `graph.js` — graph build and data fetch
- `report.js` — report generation and chat
- `index.js` — axios instance (baseURL, timeouts, interceptors)

All responses follow the shape: `{ success: boolean, data: any, error?: string }`

---

## 11. i18n Considerations

The app uses Vue i18n. All user-facing strings should use `$t('key')` — do not hardcode English strings in templates. The current translation file is at `/locales/en.json`. If you add new strings, add them to `en.json` with sensible English values.

The language switcher (LanguageSwitcher.vue) is a small toggle in the header — keep it accessible.

---

## 12. Files to Focus On

```
frontend/
├── src/
│   ├── views/
│   │   ├── Home.vue                    ← P0: Landing page
│   │   ├── MainView.vue                ← P2: Split-panel shell
│   │   ├── SimulationView.vue          ← P2: Sim prep entry point
│   │   ├── SimulationRunView.vue       ← P1: Simulation run wrapper
│   │   ├── ReportView.vue              ← P1: Report wrapper
│   │   ├── InteractionView.vue         ← P1: Interaction wrapper
│   │   └── CampaignReportView.vue      ← P3: A/B report wrapper
│   ├── components/
│   │   ├── Step1GraphBuild.vue         ← P1: Graph build progress
│   │   ├── Step2EnvSetup.vue           ← P0: Agent gen + sim config
│   │   ├── Step3Simulation.vue         ← P1: Live simulation feed
│   │   ├── Step4Report.vue             ← P0: Report document + workflow
│   │   ├── Step5Interaction.vue        ← P1: Chat + survey
│   │   ├── Step5CampaignReport.vue     ← P3: A/B results
│   │   ├── GraphPanel.vue              ← P2: D3 graph (restyle only)
│   │   ├── HistoryDatabase.vue         ← P2: History cards
│   │   └── LanguageSwitcher.vue        ← P3: Locale toggle
│   ├── api/                            ← DO NOT MODIFY
│   ├── router/index.js                 ← DO NOT MODIFY
│   ├── i18n/index.js                   ← DO NOT MODIFY
│   └── App.vue                         ← Global CSS reset, scrollbar
├── package.json
└── vite.config.js
```

---

## 13. What a Good Redesign Looks Like

**Reference points** (aesthetic direction only, not literal copies):
- Linear.app — tight information density, confident monochrome, precise type
- Vercel dashboard — status communication, subtle animations, developer-facing clarity
- Notion AI / Perplexity — conversational AI UI patterns for chat interfaces
- Observable / Hex — data-forward layout, graph + prose split panels

**Specific improvements that would have the most impact**:

1. **A persistent step progress indicator** in the header — users lose track of where they are
2. **Better empty states** — every waiting/loading moment should have helpful copy, not just a spinner
3. **Agent persona cards** should feel like real people — avatar (generated initials + color), name, role, 1-line bio
4. **The report document** should be print-quality — strong heading hierarchy, readable at 60-70 chars/line
5. **The simulation feed** should feel like a real social platform — post cards, reactions, content previews
6. **Reduce ID exposure** — `sim_abc123def456` should not be in H2 tags; move to small secondary text
7. **Consistent card system** — every major item (profile, action, recommendation) should use the same card component pattern
8. **Responsive polish** — currently breaks below ~1024px; should degrade gracefully to tablet

---

## 14. Setup Instructions

```bash
# Clone the repo
git clone https://github.com/abedmreyan/campaignsim.git
cd campaignsim

# Install all dependencies
npm run setup:all

# Create .env in the root
# (get API keys from project owner)
cp .env.example .env

# Start both frontend and backend
npm run dev

# Frontend: http://localhost:3002
# Backend:  http://localhost:5001
```

The live deployment is at https://campaignsim.aethersystems.co — you can use it to walk through all 6 screens with real data.

---

## 15. Contact & Questions

For questions about:
- **API behavior / backend** — read the Flask routes in `backend/app/api/`
- **What data looks like** — use the live site and inspect network responses
- **Design direction decisions** — ask the project owner before implementing
- **Adding new strings** — add to `locales/en.json`, use `$t()` in templates

The backend is fully functional. The frontend redesign is purely visual — no API changes needed.
