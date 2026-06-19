# CampaignSim — Implementation Overview

## Project Summary

CampaignSim is an AI-powered marketing campaign simulation and recommendation platform built as a bachelor's thesis in Computer Engineering. Users upload a campaign brief and brand/audience documents, the system builds a knowledge graph of the market landscape, generates realistic customer personas, simulates how those personas respond to different campaign variants across marketing channels, and produces a ranked recommendation of the best content × channel × audience segment combination.

Working project directory: `/Users/abedmreyan/Desktop/Graduation Project 2/campaignsim`

---

## Phase Status

| Phase | Name | Status |
|-------|------|--------|
| 1 | Core Domain Adaptation | ✅ Complete |
| 2 | Channel Simulation | 🔄 In Progress |
| 3 | Campaign Variables & A/B Testing | 🔄 In Progress |
| 4 | Recommendation Engine | 🔄 In Progress |
| 5 | UI Polish & Evaluation | 🔄 In Progress |

**Phase 1 completion includes:**
- Marketing ontology prompt (replaces generic social-opinion ontology)
- Customer persona generation (individual + brand account profiles)
- Marketing-domain UI strings (`locales/en.json`)
- Full English codebase (all Chinese text removed)
- CampaignSim branding throughout (all legacy branding removed)
- CLAUDE.md with phase completion enforcement checklist

---

## Architecture

| Layer | Technology |
|-------|-----------|
| Frontend | Vue 3 + Vite |
| Backend | Flask (Python 3.11+) |
| LLM | OpenAI-compatible API |
| Memory / Graph | Zep Cloud |
| Social Simulation | OASIS (camel-oasis) |
| Document Parsing | PyMuPDF |

---

## Core Concept Map

| CampaignSim Component | Purpose |
|-----------------------|---------|
| Campaign brief documents | Seed material (PDF/TXT uploaded by user) |
| Marketing ontology | Defines entity/relation types for the brand landscape |
| Zep knowledge graph | Stores extracted brand, persona, channel, competitor entities |
| Customer persona agents | Simulated consumers reacting to campaign content |
| Twitter / Reddit platforms | OASIS simulation substrate (channel framed via post content) |
| Channel simulation script | Runs OASIS with persona agents, exports action logs |
| Variant scorer | Reads action logs, computes engagement metrics per variant |
| Campaign ReportAgent | ReACT agent that queries the graph and produces ranked recommendations |

---

## Five Phases

| Phase | Name | Key Output |
|-------|------|------------|
| 1 ✅ | Core Domain Adaptation | Working platform with marketing-domain prompts; verified graph build from a brand brief |
| 2 | Channel Simulation | `run_channel_simulation.py`; personas react to campaign content via OASIS |
| 3 | Campaign Variables & A/B Testing | Multi-variant runner; content type × channel comparison |
| 4 | Recommendation Engine | Variant scorer, segment ranker, campaign recommendation report |
| 5 | UI Polish & Evaluation | Expert study or benchmark; thesis deliverables |

---

## Phase Completion Rules (MANDATORY)

Before marking any phase complete, run these two checks from the project root:

```bash
# 1. No Chinese characters anywhere
grep -rn -P "[\x{4e00}-\x{9fff}\x{ff01}-\x{ffee}]" \
  --include="*.py" --include="*.vue" --include="*.js" \
  --include="*.ts" --include="*.json" --include="*.md" \
  --exclude-dir=".git" --exclude-dir="__pycache__" \
  . 2>/dev/null | grep -v "locales/zh.json"
# Expected: no output

# 2. No legacy brand references
grep -rni "mirofish\|666ghj" \
  --include="*.py" --include="*.vue" --include="*.js" \
  --include="*.ts" --include="*.json" --include="*.md" \
  --include="*.yml" --include="*.toml" \
  --exclude-dir=".git" . 2>/dev/null
# Expected: no output
```

These checks are also in `campaignsim/CLAUDE.md`.

---

## Environment Setup

```env
LLM_API_KEY=<your-key>
LLM_BASE_URL=<openai-compatible-url>
LLM_MODEL_NAME=<model-name>   # e.g. gpt-4o-mini, claude-sonnet-4-6
ZEP_API_KEY=<zep-cloud-key>
FLASK_HOST=0.0.0.0
FLASK_PORT=5001
FLASK_DEBUG=True
```

---

## Cost & Risk Estimates

Approximate for a **single campaign test** (one brief, 2–3 variants, 30–50 personas, 10 rounds):

| Step | LLM Calls | Notes |
|------|-----------|-------|
| Ontology generation | 1 | One call per brief upload |
| Graph build (Zep) | ~0 | Zep handles embedding |
| Persona generation | 30–50 | One call per graph entity |
| Simulation rounds | ~900–1,500 | Most expensive — 3 variants × 50 agents × 10 rounds |
| Report agent (ReACT) | 10–20 | ReACT loop |
| **Total** | **~1,000–1,600** | |

At `gpt-4o-mini` pricing: **$0.50–$2.00** per run. Use `num_rounds = 3` and 5–10 personas during development.

---

## File Documents

- `01_phase1_core_fork.md` — ✅ Complete — marketing ontology, persona generator, UI strings
- `02_phase2_channel_simulation.md` — Channel simulation script (OASIS)
- `03_phase3_campaign_variables.md` — Multi-variant A/B simulation runner
- `04_phase4_recommendation_engine.md` — Scoring, ranking, recommendation report agent
- `05_phase5_ui_evaluation.md` — UI polish, expert evaluation, thesis deliverables
