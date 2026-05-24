# CampaignSpark

CampaignSpark is a lightweight, AI-powered Single Page Application that helps digital marketing agencies, solo founders, and indie developers convert unstructured product notes into polished, high-converting marketing one-liners — instantly.

## 🚀 Features

- **Multi-Agent Orchestration**: A 3-agent CrewAI pipeline (Strategist → Copywriter → Editor) produces structured, hallucination-checked marketing angles via Google Gemini.
- **Three Distinct Angles**: Automatically generates **Benefit-Driven**, **Problem/Solution**, and **FOMO/Urgency** marketing hooks.
- **Iterative Refinement**: One-click `[Make Shorter]` and `[More Casual]` refinement on every card, powered by a dedicated Gemini agent.
- **Smooth Generation UX**: Progress bar + agent stage tracker with animated skeleton cards; page auto-scrolls to the loading area on generate and to results on completion.
- **Redis-backed Rate Limiting**: Free-tier sessions are tracked by a client-generated UUID (30-day TTL, max 3 generations). Duplicate identical requests are served from a 24-hour cache.
- **Monetization Integration**: LemonSqueezy webhook integration with HMAC-SHA256 signature verification. Paid users receive a passwordless Magic Link emailed to them; clicking it issues a 30-day HttpOnly JWT cookie for premium access.

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Vanilla JS, HTML5, Tailwind CSS v3 (CDN) |
| **Backend** | Python 3.11, FastAPI, Pydantic V2, Uvicorn |
| **AI Framework** | CrewAI with LiteLLM (`gemini/gemini-3.1-flash-lite`) |
| **LLM Provider** | Google Gemini (Free Tier via `GEMINI_API_KEY`) |
| **Caching & State** | Redis 7 (AOF persistence, Docker volume) |
| **Auth** | PyJWT (HttpOnly cookie, HS256) |
| **Infrastructure** | Docker & Docker Compose (single-VM optimised) |

## 📁 Project Structure

```
one-liner/
├── .env                         # Environment variables (not committed)
├── docker-compose.yml           # Defines `api` and `redis` services
├── frontend/                    # Vanilla JS SPA (served via FastAPI static mount)
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── documentation/               # Product & technical docs
│   ├── PRD.md
│   ├── TRD.md
│   ├── tasks.md
│   └── mockup.html
└── backend/
    ├── Dockerfile
    ├── requirements.txt
    ├── main.py                  # App entrypoint, middleware, router wiring, SPA mount
    ├── core/
    │   ├── config.py            # Pydantic BaseSettings (reads .env)
    │   └── dependencies.py      # FastAPI Depends() providers (Redis, CrewService)
    ├── api/
    │   └── routes/
    │       ├── generate.py      # POST /generate, POST /refine
    │       ├── auth.py          # POST /auth/request-magic-link, GET /auth/verify
    │       └── monetization.py  # POST /webhooks/lemonsqueezy
    ├── domain/
    │   └── schemas/
    │       ├── models.py        # GenerateRequest/Response, RefineRequest/Response
    │       └── ai_schemas.py    # CrewOutput (internal CrewAI output schema)
    ├── services/
    │   └── crew_service.py      # CrewAI 3-agent orchestration + refine_angle
    ├── repositories/
    │   └── redis_repo.py        # All Redis operations (rate limit, cache, auth)
    └── tests/                   # Pytest test suite (fakeredis)
```

## ⚙️ Quickstart

CampaignSpark is fully containerised. You only need **Docker** and **Docker Compose**.

### 1. Configure Environment Variables

Create a `.env` file in the project **root** (`one-liner/.env`):

```env
GEMINI_API_KEY=your_google_gemini_api_key_here
LEMON_SQUEEZY_WEBHOOK_SECRET=your_lemonsqueezy_signing_secret_here
REDIS_URL=redis://redis:6379/0
ENVIRONMENT=production
```

> **Note:** `OPENAI_API_KEY` is present in `core/config.py` for legacy compatibility but is **not used**. The active LLM is Google Gemini via `GEMINI_API_KEY`.

### 2. Build and Run

```bash
docker-compose up --build -d
```

### 3. Access the Application

| Service | URL |
|---|---|
| Frontend UI | `http://localhost:8000/` |
| Swagger API Docs | `http://localhost:8000/docs` |

## 🧩 API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/generate` | Run 3-agent pipeline; returns 3 angles + `generations_remaining` |
| `POST` | `/api/v1/refine` | Refine a single angle (`shorter` or `casual`) |
| `POST` | `/api/v1/webhooks/lemonsqueezy` | Receive payment webhook; set premium status in Redis |
| `POST` | `/api/v1/auth/request-magic-link` | Send magic link to a verified premium email |
| `GET`  | `/api/v1/auth/verify` | Verify token; set 30-day HttpOnly JWT session cookie |

## 🧪 Development (without Docker)

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Start a local Redis instance (port 6379)

# 4. Run the development server
uvicorn backend.main:app --reload
```

## 🔒 Security Notes

- Redis is **not** exposed externally (no host port mapping in `docker-compose.yml`).
- The backend container runs as a **non-root user** (`appuser`).
- CORS is restricted to `localhost:8000` and `127.0.0.1:8000`.
- `TrustedHostMiddleware` is active in production.
- LemonSqueezy webhooks are validated with HMAC-SHA256 before any payload is processed.
- Magic link tokens are single-use (atomically deleted on first verification) with a 15-minute TTL.
