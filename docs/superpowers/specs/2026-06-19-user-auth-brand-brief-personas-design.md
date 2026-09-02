# CampaignSim — User Auth, Brand Brief & Persona Management
**Design Spec · 2026-06-19**

---

## 1. Problem & Scope

CampaignSim currently has no concept of a user. All data (knowledge graphs, personas, simulations) is stored in a flat global `uploads/` directory. Anyone who opens the app shares the same state.

This phase adds:
- **User accounts** — email + password signup/login with JWT auth
- **Brand brief management** — upload a PDF/text file *or* write/edit brief text directly in the UI; stored once, reusable across campaigns
- **Persona management** — generated personas are persisted to the database; users can add more, delete individual ones, or regenerate from scratch
- **User-scoped data isolation** — every file path and database row is scoped to `user_id`
- **S3-ready storage abstraction** — local disk now, swappable to S3/R2 later without touching service code

**Out of scope for this phase:** teams/workspaces, billing, email verification, OAuth (Google/GitHub), campaign history browsing UI (table exists, UI deferred).

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│  Vue 3 Frontend (campaignsim-v3/frontend)           │
│  + authStore (Pinia)                                │
│  + axios interceptor (attaches access token cookie) │
│  + LoginView, SignupView, BrandBriefView            │
│  + router guards (require auth for all app routes)  │
└────────────────────┬────────────────────────────────┘
                     │ HTTPS / Cloudflare Tunnel
┌────────────────────▼────────────────────────────────┐
│  Flask API (campaignsim container, port 5001)       │
│  + /api/auth/*  (new)                               │
│  + @require_auth decorator on all existing routes   │
│  + g.current_user injected per request              │
│  + StorageBackend abstraction                       │
└──────────┬──────────────────────┬───────────────────┘
           │ SQLAlchemy           │ file I/O
┌──────────▼──────────┐  ┌───────▼──────────────────┐
│  PostgreSQL          │  │  uploads/{user_id}/       │
│  (new container)     │  │    knowledge_graphs/      │
│  port 5432           │  │    simulations/           │
└─────────────────────┘  │  (PDFs stored here too)   │
                          └──────────────────────────┘
```

### What changes vs. what stays the same

| Component | Change |
|-----------|--------|
| `OasisProfileGenerator` | `user_id` threaded in; file paths via `StorageBackend` |
| `SimulationManager` | `user_id` threaded in; paths via `StorageBackend` |
| `graph_builder`, KG services | `user_id` threaded in; base path scoped |
| Campaign dataclasses | Unchanged (pure data objects) |
| OASIS simulation runner | Unchanged |
| Report agent | `user_id` threaded in for output paths |

---

## 3. Database Schema

### PostgreSQL via SQLAlchemy + Alembic migrations

```sql
-- Users
CREATE TABLE users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email         VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  display_name  VARCHAR(100),
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Refresh tokens (for secure revocation on logout/password change)
CREATE TABLE refresh_tokens (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash  VARCHAR(255) NOT NULL,  -- SHA-256 of the raw token
  expires_at  TIMESTAMPTZ NOT NULL,
  revoked     BOOLEAN DEFAULT FALSE,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash);
CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);

-- Brand briefs
CREATE TABLE brand_briefs (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name         VARCHAR(255) NOT NULL,             -- user-given name, e.g. "Airbnb 2026"
  content      TEXT,                              -- editable text (inline editor)
  file_path    VARCHAR(500),                      -- relative path to uploaded PDF/file (nullable)
  graph_id     VARCHAR(255),                      -- pointer to file-based KG directory (nullable)
  graph_status VARCHAR(20) DEFAULT 'pending',     -- pending | building | ready | failed
  created_at   TIMESTAMPTZ DEFAULT NOW(),
  updated_at   TIMESTAMPTZ DEFAULT NOW()
);
-- Note: content is the canonical source of truth for the brief text.
-- When a file is uploaded, its text is extracted and written to content.
-- Editing content directly updates this column; no re-upload needed.

-- Personas
CREATE TABLE personas (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  brand_brief_id  UUID NOT NULL REFERENCES brand_briefs(id) ON DELETE CASCADE,
  external_id     VARCHAR(100),        -- OASIS user_id (e.g. "user_042")
  segment         VARCHAR(255),
  data            JSONB NOT NULL,      -- full OASIS profile object
  created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_personas_user_brief ON personas(user_id, brand_brief_id);

-- Campaigns (top-level, holds variants)
-- NOTE: Schema created in this phase for future use; rows are NOT populated in this phase.
-- Campaign and variant data continues to live in in-memory Pinia state and dataclasses.
-- Population is deferred to the SaaS/history phase.
CREATE TABLE campaigns (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  brand_brief_id  UUID REFERENCES brand_briefs(id),
  brand_name      VARCHAR(255),
  campaign_goal   TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Campaign variants
-- NOTE: Same as campaigns — schema only, no writes in this phase.
CREATE TABLE campaign_variants (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id  UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  variant_name VARCHAR(255),
  channel      VARCHAR(50),
  content      JSONB,               -- serialized CampaignContent
  target_segment VARCHAR(255),
  status       VARCHAR(20) DEFAULT 'pending',
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Simulations
CREATE TABLE simulations (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  campaign_id     UUID REFERENCES campaigns(id),
  brand_brief_id  UUID REFERENCES brand_briefs(id),
  status          VARCHAR(20) DEFAULT 'pending',  -- pending | running | completed | failed
  result_path     VARCHAR(500),                   -- path to simulation output dir
  created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 4. Auth Flow

### Token strategy
- **Access token**: JWT, 15-minute TTL, stored in an **httpOnly cookie** (`cs_access`). Short TTL limits exposure if stolen.
- **Refresh token**: opaque random string (256-bit), 30-day TTL, stored in an **httpOnly cookie** (`cs_refresh`). Its SHA-256 hash is stored in `refresh_tokens` table so it can be revoked on logout or password change.
- No localStorage token storage — httpOnly cookies are not accessible to JS, protecting against XSS.

### Cookie & CORS configuration

The frontend (port 3006) and backend (port 5001) are different origins, so cookies must be configured carefully or they will silently fail.

**Flask (backend):**
```python
# Set on every auth response
response.set_cookie(
    'cs_access',
    value=access_token,
    httponly=True,
    secure=True,           # Always True — both local Cloudflare Tunnel and prod use HTTPS
    samesite='None',       # Cross-origin cookie required; None requires Secure=True
    max_age=JWT_ACCESS_TTL_MINUTES * 60,
    domain=None,           # Let the browser infer; don't pin domain in dev
)
# Same pattern for cs_refresh

# Flask-CORS — must allow credentials explicitly
CORS(app,
     origins=["http://localhost:3006", "https://campaignsim-v3.aethersystems.co"],
     supports_credentials=True)
```

**Axios (frontend):**
```js
// api.js — apply once globally
import axios from 'axios'
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,   // http://localhost:5001 or tunnel URL
  withCredentials: true,                    // Send cookies on every request
})
export default api
```

**Local development note:** Local dev runs over HTTP on port 5001, but `SameSite=None` requires `Secure=True`. In practice, the backend should be reached through the Cloudflare Tunnel (`campaignsim-v3.aethersystems.co`) even during local testing, or a local HTTPS proxy should be used. Alternatively, set `samesite='Lax'` during local development and `samesite='None'` in production — controlled by `FLASK_ENV`.

### JWT algorithm
Always specify the signing algorithm explicitly to prevent algorithm-confusion attacks (`alg: none`):
```python
# Encode
jwt.encode(payload, JWT_SECRET, algorithm='HS256')
# Decode — pass an explicit allowlist
jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
```

### Rate limiting (in-scope)
`flask-limiter` is applied to auth routes to prevent brute-force attacks.

**Important — Cloudflare proxy awareness:** All traffic passes through the Cloudflare Tunnel, so `request.remote_addr` is always Cloudflare's egress IP. Using it as the rate-limit key means every user shares one bucket. Use the `CF-Connecting-IP` header instead, which Cloudflare always injects with the real client IP:

```python
def get_real_ip():
    # CF-Connecting-IP is injected by Cloudflare on every request.
    # Fallback to remote_addr only for local non-tunnel testing.
    return request.headers.get('CF-Connecting-IP') or request.remote_addr

limiter = Limiter(app, key_func=get_real_ip)

@limiter.limit("10/minute")
@auth_bp.route('/login', methods=['POST'])
def login(): ...

@limiter.limit("5/minute")
@auth_bp.route('/signup', methods=['POST'])
def signup(): ...
```
`flask-limiter` is added to `requirements.txt`.

### New API routes

```
POST /api/auth/signup         { email, password, display_name }
                              → sets cs_access + cs_refresh cookies
                              → returns { user: { id, email, display_name } }

POST /api/auth/login          { email, password }
                              → same as signup response

POST /api/auth/logout         (cookie auth)
                              → revokes refresh token in DB
                              → clears both cookies

POST /api/auth/refresh        (uses cs_refresh cookie)
                              → validates token against DB, issues new cs_access

GET  /api/auth/me             (cookie auth)
                              → returns current user object
```

### Flask middleware

```python
# app/utils/auth.py
def require_auth(f):
    """Decorator: validates cs_access JWT, injects g.current_user."""
    ...

# Applied to ALL existing routes:
# /api/graph/*, /api/simulation/*, /api/report/*, /api/evaluation/*
```

On the frontend, the `authStore` calls `/api/auth/me` on app boot. If it fails with 401, the user is redirected to `/login`. No manual token handling needed — the browser sends cookies automatically.

---

## 5. Storage Abstraction

```python
# app/services/storage.py

class StorageBackend:
    """Interface. Covers: uploaded files, KG directories, simulation output."""
    def save_file(self, user_id: str, key: str, data: bytes) -> str: ...
    def load_file(self, user_id: str, key: str) -> bytes: ...
    def delete_file(self, user_id: str, key: str): ...
    def exists(self, user_id: str, key: str) -> bool: ...
    def user_path(self, user_id: str, *parts) -> str: ...

class LocalStorage(StorageBackend):
    """Stores files at {base}/{user_id}/{key}."""
    def __init__(self, base: str):  # base = uploads/
        self.base = base
    def user_path(self, user_id, *parts):
        return os.path.join(self.base, user_id, *parts)
    # ... implementations

# S3Storage will implement the same interface when needed.
# Registered as app-level singleton: current_app.storage
```

**What goes through StorageBackend (files on disk):**
- Uploaded PDFs and text files
- Knowledge graph SQLite databases (in `knowledge_graphs/{graph_id}/`)
- Simulation output directories (in `simulations/{simulation_id}/`)

**What does NOT go through StorageBackend (database rows):**
- User records
- Persona JSONB data (read/write via SQLAlchemy, not files)
- Campaign/variant/simulation metadata

---

## 6. API Changes (Existing Routes)

All existing routes get `@require_auth` and receive `g.current_user`. File paths are constructed via `storage.user_path(g.current_user.id, ...)`.

### Key signature changes

```python
# graph.py
POST /api/graph/upload          # saves file to storage.user_path(uid, 'briefs', filename)
                                # creates brand_brief row in DB
POST /api/graph/build           # scopes KG to storage.user_path(uid, 'knowledge_graphs', graph_id)
                                # updates brand_brief.graph_id + graph_status

# simulation.py
POST /api/simulation/generate_profiles
                                # reads graph from user-scoped path
                                # saves personas to DB (personas table) instead of JSON file
                                # returns { items: [...], task_id }

GET  /api/simulation/personas   # NEW: list user's personas for a brand_brief_id
DELETE /api/simulation/persona/<id>  # NEW: delete a single persona row
POST /api/simulation/personas/clear  # NEW: delete all personas for a brand_brief_id

# Brand brief routes (new)
GET    /api/briefs              # list user's brand briefs
POST   /api/briefs              # create (text-only, no file)
GET    /api/briefs/<id>         # get single brief
PUT    /api/briefs/<id>         # update name or content (in-place edit)
DELETE /api/briefs/<id>         # delete brief + cascade personas
POST   /api/briefs/<id>/upload  # attach / replace the uploaded file
POST   /api/briefs/<id>/rebuild-graph  # trigger KG rebuild from current content
                                      # Implementation: writes brand_briefs.content to a
                                      # temp file under uploads/{user_id}/briefs/,
                                      # then passes that path to graph_builder (unchanged).
                                      # Temp file is overwritten on each rebuild; no extra
                                      # cleanup needed. This avoids refactoring graph_builder.
```

---

## 7. Frontend Changes

### New views
- `LoginView.vue` — email + password form, redirects to `/briefs` on success; route `/login`
- `SignupView.vue` — same fields + display_name; route `/signup`
- `BrandBriefView.vue` — route `/briefs`; this is the **post-login landing page** and pre-workflow dashboard. The user picks or creates a brand brief here before entering the campaign workflow. Once a brief is selected, the router redirects to `/process` with `brandBriefId` set in Pinia state.

**Navigation flow:**
```
/login  →  /briefs  →  /process  →  /graph  →  ...
           (select brief)  (Step 1 — campaign variants)
```
`/` (Home) remains a public marketing page. All workflow routes (`/process`, `/graph`, `/simulation/*`, `/report/*`, `/interaction/*`, `/history`) require auth and a selected `brandBriefId`; the router guard redirects to `/briefs` if either is missing.

### New store: `authStore.js`
```js
// stores/authStore.js
state: { user: null, loading: false, error: null }
actions:
  login(email, password)   → POST /api/auth/login
  signup(...)              → POST /api/auth/signup
  logout()                 → POST /api/auth/logout, clears user, redirects /login
  fetchMe()                → GET /api/auth/me (called on app boot)
```

### Axios interceptor — automatic token refresh
When the 15-minute `cs_access` cookie expires, requests return 401. An axios response interceptor catches this, calls the refresh endpoint (which uses the `cs_refresh` cookie), and retries the original request transparently. This lives in `frontend/src/api.js`:

```js
api.interceptors.response.use(null, async (err) => {
  if (err.response?.status === 401 && !err.config._retried) {
    err.config._retried = true
    try {
      await api.post('/api/auth/refresh')  // issues new cs_access cookie
      return api(err.config)              // retry original request
    } catch {
      // Refresh itself failed (expired/revoked) — send to login
      useAuthStore().user = null
      router.push('/login')
    }
  }
  return Promise.reject(err)
})
```

### Router changes
```js
// Public routes: home, login, signup
const PUBLIC_ROUTES = ['home', 'login', 'signup']

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (PUBLIC_ROUTES.includes(to.name)) return true
  if (!auth.user) {
    await auth.fetchMe()           // attempt cookie-based restore
    if (!auth.user) return '/login'
  }
})
```

### `brandBriefId` persistence across page refresh

Pinia state is in-memory only — a page refresh wipes `brandBriefId`, causing the router guard to redirect the user back to `/briefs` mid-workflow. Fix: persist the active brief ID to `sessionStorage` and rehydrate on app boot.

```js
// In campaignStore.js
const BRIEF_KEY = 'cs_active_brief_id'

// When user selects a brief in BrandBriefView:
function selectBrief(id) {
  state.brandBriefId = id
  sessionStorage.setItem(BRIEF_KEY, id)
}

// On app boot (called after authStore.fetchMe() resolves):
function rehydrateBrief() {
  const saved = sessionStorage.getItem(BRIEF_KEY)
  if (saved) state.brandBriefId = saved
}

// On logout:
function clearBrief() {
  state.brandBriefId = null
  sessionStorage.removeItem(BRIEF_KEY)
}
```

`sessionStorage` is scoped to the browser tab and cleared when the tab closes — appropriate for a workflow session. `localStorage` would persist across browser restarts (more friction for switching briefs).

### `campaignStore.js` changes
- `generatePersonas()` POSTs to backend as before, but on completion reads from DB via `GET /api/simulation/personas?brief_id=...`
- New actions: `deletePersona(id)`, `clearPersonas(briefId)`, `loadPersonas(briefId)`
- `graphId` and `simulationId` are scoped — loaded from the active `brandBriefId` in state

### Persona management UX additions in `Step2Personas.vue`
- On mount: loads existing personas from DB (no need to regenerate)
- Delete button on each `PersonaCard` → `deletePersona(id)` → removes row
- "Regenerate all" button → `clearPersonas()` then `generatePersonas(count)`
- "Generate more" button → `generatePersonas(count)` appends to existing

---

## 8. Infrastructure Changes

### `docker-compose.yml`
```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: campaignsim
      POSTGRES_USER: cs_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U cs_user -d campaignsim"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://cs_user:${POSTGRES_PASSWORD}@postgres:5432/campaignsim
      JWT_SECRET: ${JWT_SECRET}
      # ... existing env vars

volumes:
  pgdata:
```

### New Python dependencies
```
flask-sqlalchemy>=3.1
flask-migrate>=4.0
psycopg2-binary>=2.9
bcrypt>=4.0
pyjwt>=2.8
flask-limiter>=3.5
```

### New `.env` variables
```
DATABASE_URL=postgresql://cs_user:secret@localhost:5432/campaignsim
JWT_SECRET=<random 64-char hex>
POSTGRES_PASSWORD=<random password>
JWT_ACCESS_TTL_MINUTES=15
JWT_REFRESH_TTL_DAYS=30
```

---

## 9. Migration Strategy

Existing data in `uploads/` (before auth existed) is orphaned — no user owns it. Strategy:

1. On first deploy, the new schema is applied via Alembic (`flask db upgrade`).
2. Existing flat `uploads/` content is left in place but not accessible through the new user-scoped API. It can be manually cleaned up post-deploy.
3. No automated data migration — existing sessions were anonymous; there is no user to assign them to.

---

## 10. Open Questions / Deferred Decisions

| Question | Decision |
|----------|----------|
| Email verification on signup? | Deferred — skip for now, add later |
| Password reset flow? | Deferred — out of scope this phase |
| Google/GitHub OAuth? | Deferred — SaaS phase 2 |
| Team/workspace support? | Deferred — SaaS phase 3 |
| S3 migration? | Deferred — implement `S3Storage` class when self-hosting limits scale |
| Rate limiting on auth routes? | **In scope** — see Section 4 (Cookie & CORS configuration). Flask-Limiter applied to `/api/auth/login` (10/min) and `/api/auth/signup` (5/min). |
