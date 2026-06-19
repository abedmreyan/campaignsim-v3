# CampaignSim

**CampaignSim** is an AI-powered marketing campaign simulation and recommendation platform. Upload your campaign briefs, build a knowledge graph from your documents, and run multi-agent social simulations to predict how your audience will respond — before your campaign ever launches.

## Overview

CampaignSim lets you:

- **Build a knowledge graph** from campaign documents, product briefs, and market research using Zep and LLM-based ontology extraction
- **Generate realistic customer personas** with independent personalities, goals, and behavioral tendencies
- **Run social simulations** across Twitter and Reddit environments where agents interact with your campaign content
- **Analyze results** with an AI report agent that queries the knowledge graph and surfaces insights about engagement, sentiment, and reach
- **Interview agents** directly to understand why they responded the way they did

## Architecture

| Layer | Technology |
|-------|-----------|
| Frontend | Vue 3, Vite, D3.js |
| Backend | Flask (Python 3.11+) |
| LLM | OpenAI-compatible API |
| Memory / Graph | Zep Cloud |
| Social Simulation | OASIS (camel-oasis) |

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (optional, for containerized deployment)

### Environment Variables

Copy `.env.example` to `.env` and fill in:

```env
OPENAI_API_KEY=...
OPENAI_BASE_URL=...
OPENAI_MODEL=...
ZEP_API_KEY=...
```

### Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
python run.py

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Docker

```bash
docker compose up --build
```

The frontend is served at `http://localhost:3000` and the backend API at `http://localhost:5001`.

## Project Structure

```
campaignsim/
├── backend/
│   └── app/
│       ├── api/          # Flask routes
│       ├── services/     # Core simulation logic
│       └── utils/        # Helpers
├── frontend/
│   └── src/
│       ├── views/        # Page-level components
│       ├── components/   # Reusable UI components
│       └── api/          # API client
└── locales/              # i18n language files
```

## Simulation Workflow

1. **Upload** — provide campaign documents (PDF, TXT, etc.) and a campaign goal
2. **Graph Build** — the system extracts an ontology and builds a Zep knowledge graph
3. **Environment Setup** — generate customer persona agents and simulation configuration
4. **Run Simulation** — agents interact on simulated social platforms
5. **Report** — AI agent analyzes the graph and generates a campaign performance report
6. **Interact** — directly interview individual agents about their behavior

## License

AGPL-3.0
