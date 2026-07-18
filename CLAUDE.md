# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**Companio** is an AI companion platform. Users create a profile, select an AI agent persona (Best Friend, Girlfriend, Boyfriend), and chat with it. The platform uses RAG-based agentic memory so agents can remember users across sessions.

The repo is a monorepo with **three independent sub-projects**:

- `companio-main-backend/` — Django REST API, the user-facing "product" backend (MySQL)
- `ai-agent-platform-backend/` — **agent-core**, the AI reasoning engine (LangGraph + RAG + LLM providers)
- `react-frontend/` — React + Vite + Tailwind CSS frontend

### Service topology

```
react-frontend  ──JWT──▶  companio-main-backend  ──HTTP──▶  ai-agent-platform-backend (agent-core)
                          (MySQL, business logic)            │  (LangGraph pipeline, LLMs)
                                    ▲                         │
                                    └──── GET /api/agents/{id}/ (agent-core reads persona config)
```

The two backends have a **bidirectional runtime dependency**: the main backend forwards chat turns to agent-core, and agent-core calls back to the main backend to load agent/persona config. They use separate databases (main = MySQL, agent-core = local SQLite + ChromaDB vector store).

> **Integration status:** agent-core is **not yet wired into the production chat flow**. The real chat path (`apps/chats`) still calls the legacy "Agent Platform" contract via `apps/agent_gateway/services.py` (mock mode on by default). agent-core is currently reachable only through the thin, auth-less testing endpoint `POST /api/v1/chat/` (`apps/agent_gateway/agent_client.py` + `views.py`). Wiring agent-core into `apps/chats` is the pending integration step.

---

## Backend (`companio-main-backend/`)

### Setup

```bash
cd companio-main-backend
cp .env.example .env          # fill in real values
python -m venv venv
venv\Scripts\activate         # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Key commands

```bash
python manage.py runserver                        # start dev server (port 8000)
python manage.py migrate                          # apply migrations
python manage.py makemigrations <app>             # create migration for an app
python manage.py test apps.<app_name>             # run tests for one app
python manage.py test                             # run all tests
python manage.py createsuperuser
```

### Environment variables (`.env`)

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django secret key (required) |
| `DEBUG` | Enable debug mode |
| `DB_NAME/USER/PASSWORD/HOST/PORT` | MySQL connection |
| `AGENT_PLATFORM_BASE_URL` | Legacy "Agent Platform" runtime URL (used by the real chat flow) |
| `AGENT_PLATFORM_SERVICE_KEY` | Service-to-service auth key for the legacy runtime |
| `AGENT_PLATFORM_USE_MOCK` | Set `True` in dev to skip real agent calls (default `True`) |
| `AGENT_CORE_URL` | agent-core base URL for the `/api/v1/chat/` testing gateway (default `http://localhost:8001`) |
| `AGENT_CORE_TIMEOUT_SECONDS` | Request timeout when calling agent-core (default `30`) |
| `FREE_DAILY_MESSAGE_LIMIT` | Default daily message cap for free users |

The database is **MySQL only** — do not use SQLite.

### App structure

Each Django app in `apps/` follows the standard layout (`models.py`, `serializers.py`, `views.py`, `urls.py`, `services.py`, `tests.py`).

| App | Responsibility |
|---|---|
| `accounts` | Custom `User` model (email-primary, role field), JWT auth via SimpleJWT |
| `profiles` | Extended user profile (avatar, bio, language, timezone) |
| `agents` | `Agent` catalog + `UserAgentSelection` (which agent a user has picked) |
| `agent_gateway` | HTTP bridge to the AI. **Two clients:** `services.py` → legacy Agent Platform (`AGENT_PLATFORM_BASE_URL`, mock mode via `AGENT_PLATFORM_USE_MOCK=True`), used by the `chats` flow; `agent_client.py` → agent-core (`AGENT_CORE_URL`), exposed at `POST /api/v1/chat/` for manual/Postman testing |
| `admin_api` | `/api/admin/` REST endpoints backing the admin console (users, plans, agents, usage, safety, LLM providers) |
| `chats` | `ChatSession` and `ChatMessage` models; orchestrates user message → agent response flow |
| `usage` | `DailyUsage` tracks per-user daily message counts against plan limits |
| `subscriptions` | `Plan` catalog + `UserSubscription`; supports Stripe, Google Play, Apple IAP, PayHere |
| `safety` | Safety reports submitted by users against agent responses |
| `notifications` | User notification records |
| `app_config` | Runtime configuration key-value store for the app |
| `audit_logs` | Audit trail for admin/staff actions |
| `common` | Shared base model (`TimeStampedModel`) and health-check endpoint |

### API base paths

```
/api/health/
/api/auth/          # register, login, token refresh, me
/api/profile/
/api/agents/
/api/chats/
/api/usage/
/api/safety-reports/
/api/subscriptions/
/api/notifications/
/api/app-config/
/api/admin/         # admin console REST API (admin-role only)
/api/v1/chat/       # thin forwarding gateway to agent-core (AllowAny, testing only)
```

All endpoints use **JWT Bearer** authentication. The `REST_FRAMEWORK` default requires authentication on every view unless explicitly overridden.

### Auth model

- Custom `AUTH_USER_MODEL = 'accounts.User'` — always import `get_user_model()` instead of Django's built-in `User`.
- JWT access token lifetime: 30 min (configurable via `JWT_ACCESS_TOKEN_MINUTES`).
- JWT refresh token lifetime: 7 days (configurable via `JWT_REFRESH_TOKEN_DAYS`).

### Agent gateway mock mode

When `AGENT_PLATFORM_USE_MOCK=True`, `apps/agent_gateway/services.py` returns a hardcoded mock response without hitting the external runtime. Use this during local development when the agent runtime is not running. This only affects the legacy path used by the `chats` flow — the `/api/v1/chat/` gateway always calls agent-core for real.

---

## agent-core (`ai-agent-platform-backend/`)

The AI reasoning engine — a **separate Django project** that runs the full agentic RAG pipeline. It exposes essentially one endpoint and has no user-facing auth; it's an internal service called by the main backend.

### Setup

```bash
cd ai-agent-platform-backend
cp .env.example .env          # fill in LLM keys + MAIN_BACKEND_BASE_URL
python -m venv venv
venv\Scripts\activate         # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8001   # run on 8001 so it doesn't clash with the main backend (8000)
```

### Endpoints

```
GET  /health/
POST /chat/     # {user_id, agent_id, session_id, message} -> {response, emotion, intent}
```

`POST /chat/` is `AllowAny` and runs one chat turn through the full pipeline. Errors never leak internals — the view returns a generic 503 on any pipeline failure.

### Environment variables (`.env`)

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` | Django core |
| `LOG_LEVEL` | Logging level (default `INFO`) |
| `CHROMA_DB_PATH` | Local ChromaDB persistence path |
| `CANONICAL_DB_PATH` | Local SQLite path for the structured canonical-fact store (default `./canonical_facts.sqlite3`) |
| `MAIN_BACKEND_BASE_URL` | Main backend URL — agent-core calls `GET {base}/api/agents/{agent_id}/` for persona config |
| `MAIN_BACKEND_SERVICE_KEY` / `MAIN_BACKEND_TIMEOUT` | Auth + timeout for the config call |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | OpenAI provider (default model `gpt-4o-mini`) |
| `GEMINI_API_KEY` / `GEMINI_MODEL` | Gemini provider (default model `gemini-1.5-flash`) |

agent-core stores its own Django metadata in a local **SQLite** `db.sqlite3`; long-term memory lives in **ChromaDB** (`CHROMA_DB_PATH`). Exact, single-valued **canonical facts** (name, location, occupation) also live in a small separate **SQLite** store (`CANONICAL_DB_PATH`, `memory/structured/`) — vectors for fuzzy recall, a table for precise lookups, kept in sync by write-back. No MySQL here.

### The reasoning pipeline (LangGraph)

`graph/workflow.py` compiles a single linear graph. `services/chat_service.py::process_chat` is the entry point; each node reads shared `AgentState` (`graph/state.py`) and returns a partial update. Every external call degrades gracefully (sets a `safety_flag`, never crashes the graph):

```
input → intent → emotion → agent_loader → memory_retriever →
context_builder → prompt_builder → llm → safety → response_finalizer → writeback
```

### Subsystems

| Module | Responsibility |
|---|---|
| `services/agent_loader.py` | Builds an `AgentProfile` by merging main-backend agent config (`GET /api/agents/{id}/`) with a local `agents/{agent_id}/behavior.txt` persona file. Config-driven — no hard-coded agents. |
| `services/classifiers/` | `intent_classifier` (flags `crisis`) and `emotion_detector` |
| `memory/` | RAG over **ChromaDB**. Four collections: `user_memory`, `conversation_memory`, `emotional_memory`, `agent_behavior_memory`. `memory_service.py` is the only public interface (`save_*`, `get_relevant_memories`, `get_canonical_facts`). `memory/structured/` is a SQLite store of exact canonical facts (precise lookups) complementing the vectors |
| `memory/writeback/` | Learns from each exchange: `fact_extractor`, `memory_classifier`, `summarizer`, `writeback_engine`. Runs as the final pipeline node |
| `llm/llm_router.py` | Provider orchestrator with automatic fallback. OpenAI ↔ Gemini, chosen by quality/cost; `crisis` intent forces the highest-quality provider. Safe fallback text when all providers fail |
| `safety/engine.py` | Deterministic, stateless, keyword-based **post-LLM** gatekeeper. Detects crisis/self-harm, emotional dependency, manipulation, isolation, and false "I'm a real human" claims; scores responses and rewrites unsafe ones with a grounding statement. Never relies on an LLM to be safe |

### Persona files

Each agent has a `agents/{agent_id}/behavior.txt` (currently `best_friend`, `boyfriend`, `girlfriend`). The `agent_id` sent to `/chat/` must match both a directory here and an `Agent.key` in the main backend.

---

## Frontend (`react-frontend/`)

### Setup

```bash
cd react-frontend
cp .env.example .env          # set VITE_API_BASE_URL if needed
npm install
npm run dev                   # starts Vite dev server (default port 5173)
```

### Key commands

```bash
npm run dev        # development server
npm run build      # production build to dist/
npm run lint       # ESLint
npm run preview    # preview production build
```

### Architecture

- **React 19** + **React Router 7** + **Tailwind CSS 4** + **Axios**
- State management is local/context-only — no Redux or Zustand.

#### Context layer (`src/context/`)

- `AuthContext` — manages `user`, `status` (`guest` | `loading` | `authenticated`), `login()`, `register()`, `logout()`. Session is restored from `localStorage` tokens on mount. The `companio:unauthorized` window event triggers automatic logout.
- `ProductContext` — app-level product/config state.
- `ThemeContext` — dark/light theme toggle (persisted).

All three are composed in `src/app/providers.jsx` and wrap the entire app inside `BrowserRouter`.

#### API layer (`src/services/`)

- `apiClient.js` — Axios instance pointing at `VITE_API_BASE_URL`. Attaches `Authorization: Bearer <token>` on every request. On 401, silently refreshes the token once via `/auth/token/refresh/` (deduped with a shared promise), then retries. On refresh failure, clears tokens and fires `companio:unauthorized`.
- One service file per domain: `authService`, `agentService`, `chatService`, `profileService`, `safetyService`, `subscriptionService`, `usageService`, `settingsService`, `appConfigService`, `adminService`.
- `getApiErrorMessage(error)` in `apiClient.js` is the canonical helper for extracting a human-readable error string from DRF responses.

#### Routing (`src/routes/`)

- `ProtectedRoute.jsx` — redirects unauthenticated users to login.
- `AdminRoute.jsx` — further restricts routes to admin-role users.

#### Feature pages (`src/features/`)

Organized by domain: `auth`, `dashboard`, `agents`, `chat`, `profile`, `safety`, `settings`, `subscriptions`, `testing`, `usage`, `landing`, `admin`.
