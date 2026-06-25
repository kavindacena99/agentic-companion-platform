# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**Companio** is an AI companion platform. Users create a profile, select an AI agent persona (friend, romantic, mentor, etc.), and chat with it. The platform uses RAG-based agentic memory so agents can remember users across sessions.

The repo has two independent sub-projects:

- `companio-main-backend/` — Django REST API (Python)
- `react-frontend/` — React + Vite + Tailwind CSS frontend

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
| `AGENT_PLATFORM_BASE_URL` | External agent runtime URL |
| `AGENT_PLATFORM_SERVICE_KEY` | Service-to-service auth key |
| `AGENT_PLATFORM_USE_MOCK` | Set `True` in dev to skip real agent calls |
| `FREE_DAILY_MESSAGE_LIMIT` | Default daily message cap for free users |

The database is **MySQL only** — do not use SQLite.

### App structure

Each Django app in `apps/` follows the standard layout (`models.py`, `serializers.py`, `views.py`, `urls.py`, `services.py`, `tests.py`).

| App | Responsibility |
|---|---|
| `accounts` | Custom `User` model (email-primary, role field), JWT auth via SimpleJWT |
| `profiles` | Extended user profile (avatar, bio, language, timezone) |
| `agents` | `Agent` catalog + `UserAgentSelection` (which agent a user has picked) |
| `agent_gateway` | HTTP proxy to the external agent runtime; mock mode available via `AGENT_PLATFORM_USE_MOCK=True` |
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
```

All endpoints use **JWT Bearer** authentication. The `REST_FRAMEWORK` default requires authentication on every view unless explicitly overridden.

### Auth model

- Custom `AUTH_USER_MODEL = 'accounts.User'` — always import `get_user_model()` instead of Django's built-in `User`.
- JWT access token lifetime: 30 min (configurable via `JWT_ACCESS_TOKEN_MINUTES`).
- JWT refresh token lifetime: 7 days (configurable via `JWT_REFRESH_TOKEN_DAYS`).

### Agent gateway mock mode

When `AGENT_PLATFORM_USE_MOCK=True`, `apps/agent_gateway/services.py` returns a hardcoded mock response without hitting the external runtime. Use this during local development when the agent runtime is not running.

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

Both are composed in `src/app/providers.jsx` and wrap the entire app inside `BrowserRouter`.

#### API layer (`src/services/`)

- `apiClient.js` — Axios instance pointing at `VITE_API_BASE_URL`. Attaches `Authorization: Bearer <token>` on every request. On 401, silently refreshes the token once via `/auth/token/refresh/` (deduped with a shared promise), then retries. On refresh failure, clears tokens and fires `companio:unauthorized`.
- One service file per domain: `authService`, `agentService`, `chatService`, `profileService`, `safetyService`, `subscriptionService`, `usageService`, `settingsService`, `appConfigService`, `adminService`.
- `getApiErrorMessage(error)` in `apiClient.js` is the canonical helper for extracting a human-readable error string from DRF responses.

#### Routing (`src/routes/`)

- `ProtectedRoute.jsx` — redirects unauthenticated users to login.
- `AdminRoute.jsx` — further restricts routes to admin-role users.

#### Feature pages (`src/features/`)

Organized by domain: `auth`, `dashboard`, `agents`, `chat`, `profile`, `safety`, `settings`, `subscriptions`, `testing`, `usage`, `landing`, `admin`.
