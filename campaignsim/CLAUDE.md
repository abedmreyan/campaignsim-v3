# CampaignSim — Claude Code Instructions

## Language Enforcement (CRITICAL)

**All code, comments, strings, and documentation must be in English only.**

Before completing any task that adds or modifies code:
1. Run a Chinese character scan: `grep -rn -P "[\x{4e00}-\x{9fff}]" --include="*.py" --include="*.vue" --include="*.js" --include="*.ts" --include="*.json" --include="*.md" . 2>/dev/null`
2. If any output appears, fix those files before declaring done.

Do not introduce Chinese characters in:
- Python docstrings, comments, or string literals
- Vue/JS template text, comments, or string literals
- JSON locale files (only `locales/zh.json` is permitted to have Chinese — it is the Chinese locale file)
- Markdown documentation
- Configuration files

## Branding (CRITICAL)

This project is called **CampaignSim**. Do NOT use:
- `MiroFish` or `mirofish` in any context
- `666ghj` (original GitHub repo owner)
- Any reference to the original MiroFish project

Logger names use `campaignsim.*` namespace (e.g., `campaignsim.api.simulation`).
Secret keys use `campaignsim-*` prefix.
Graph IDs use `campaignsim_*` prefix.

## Phase Completion Checklist

After implementing any feature or fix, verify:

### 1. Chinese Clean Check
```bash
grep -rn -P "[\x{4e00}-\x{9fff}\x{ff01}-\x{ffee}]" \
  --include="*.py" --include="*.vue" --include="*.js" --include="*.ts" \
  --include="*.json" --include="*.md" \
  --exclude-dir=".git" --exclude-dir="__pycache__" \
  . 2>/dev/null | grep -v "locales/zh.json"
```
Expected output: empty (no results).

### 2. Brand Clean Check
```bash
grep -rni "mirofish\|666ghj" \
  --include="*.py" --include="*.vue" --include="*.js" --include="*.ts" \
  --include="*.json" --include="*.md" --include="*.yml" --include="*.toml" \
  --exclude-dir=".git" . 2>/dev/null
```
Expected output: empty (no results).

### 3. Python Syntax Check
After modifying any Python file:
```bash
python3 -m py_compile <file>
```

### 4. Logger Naming
New loggers must use: `get_logger('campaignsim.<module_name>')`

## Project Architecture

- **Frontend**: Vue 3 + Vite (`frontend/src/`)
- **Backend**: Flask (`backend/app/`)
  - `api/` — HTTP route handlers
  - `services/` — business logic (graph build, simulation, report)
  - `utils/` — shared utilities (logger, retry, zep helpers)
- **Locales**: `locales/` — i18n files (`en.json`, `zh.json`, etc.)

## Key Files

| File | Purpose |
|------|---------|
| `backend/app/services/report_agent.py` | AI report generation using ReACT agent |
| `backend/app/services/simulation_manager.py` | OASIS simulation orchestration |
| `backend/app/services/graph_builder.py` | Zep knowledge graph construction |
| `backend/app/services/zep_graph_memory_updater.py` | Agent action → Zep memory |
| `frontend/src/components/Step4Report.vue` | Report display + parsing |
| `locales/en.json` | English UI strings |

## Development Notes

- The simulation backend uses OASIS (camel-oasis) for multi-agent social simulation
- Zep Cloud is the knowledge graph / memory backend
- Report agent prompts are in `report_agent.py` constants — keep them in English
- Regex patterns in `Step4Report.vue` parse LLM-generated tool output — update them if the tool output format changes
