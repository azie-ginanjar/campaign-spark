# CampaignSpark — Technical Requirements Document (TRD)

> **Status:** Reflects implemented codebase as of May 2026.

---

## 1. Architecture Overview

CampaignSpark follows a lightweight **Domain-Driven Design (DDD)** architecture with strict separation between Routes, Services, and Repositories. All stateful dependencies (Redis, CrewService) are injected via FastAPI's `Depends()`.

### Data Flow

```
Browser (SPA)
  │  POST /api/v1/generate  { notes, session_id }
  ▼
FastAPI Router (generate.py)
  │  Depends(get_redis_repo) → RedisRepository
  │  Depends(get_crew_service) → CrewService
  │
  ├─► Redis: check cache (SHA-256 of notes)   ← cache hit → return early
  ├─► Redis: check rate limit (session_id)    ← 403 if limit reached
  ├─► CrewAI: kickoff 3-agent pipeline        ← ~15–30s Gemini call
  ├─► Redis: increment_usage(session_id)
  ├─► Redis: set_cache(notes_hash, result)
  └─► Response: { angles: [...], generations_remaining: N }
```

---

## 2. API Contracts

All endpoints are strictly typed with **Pydantic V2** and served by **FastAPI**.

### 2.1 `POST /api/v1/generate`

Orchestrates the 3-agent CrewAI pipeline.

**Request:**
```python
class GenerateRequest(BaseModel):
    notes: str = Field(..., min_length=10, max_length=5000)
    session_id: str = Field(..., min_length=1)  # Client-generated UUID (localStorage)
```

**Response:**
```python
class AngleOutput(BaseModel):
    angle_type: str  # "Benefit-Driven" | "Problem/Solution" | "FOMO/Urgency"
    content: str

class GenerateResponse(BaseModel):
    angles: List[AngleOutput]
    generations_remaining: int
```

**Behaviour:**
- `403 Forbidden` when `generations_remaining <= 0`
- Cache check first (SHA-256 hash of `notes`); cache hit bypasses LLM call
- Usage incremented **after** a successful LLM call

---

### 2.2 `POST /api/v1/refine`

Single-agent inline refinement of a generated angle.

**Request:**
```python
class RefineRequest(BaseModel):
    original_text: str = Field(..., min_length=5)
    refinement_type: Literal['shorter', 'casual']
    session_id: str = Field(..., min_length=1)
```

**Response:**
```python
class RefineResponse(BaseModel):
    refined_text: str
```

> **Note:** Refinement does **not** consume a free generation. Rate limiting applies to `/generate` only.

---

### 2.3 `POST /api/v1/webhooks/lemonsqueezy`

Receives LemonSqueezy `order_created` webhook events.

**Security:** HMAC-SHA256 validation using `x-signature` header and `LEMON_SQUEEZY_WEBHOOK_SECRET`.

**Email extraction priority:**
1. `payload.meta.custom_data.email`
2. `payload.data.attributes.user_email`

**Effect:** `repo.set_premium(email)` → sets `user:{email}:premium = "1"` in Redis (no TTL — permanent).

---

### 2.4 `POST /api/v1/auth/request-magic-link`

**Request body:** `{ "email": "user@example.com" }`

**Behaviour:**
- Validates premium status (`is_premium(email)`); returns `403` if not premium
- Generates a `secrets.token_urlsafe(32)` token, stores `token:{token} → email` with 15-minute TTL
- **Dev mode:** Magic link is printed to stdout (no email transport configured)
- **Production:** Email transport to be wired (SMTP/SendGrid)

---

### 2.5 `GET /api/v1/auth/verify?token={token}`

**Behaviour:**
- Atomically retrieves and deletes the token (single-use via Redis pipeline)
- `401 Unauthorized` if token not found or expired
- On success: encodes a 30-day HS256 JWT `{ sub: email, exp: ..., premium: true }`
- Sets `HttpOnly`, `SameSite=lax`, `Secure=False` (dev) cookie `session_token`

> **⚠️ Production note:** Set `secure=True` on the cookie when serving over HTTPS.

---

## 3. Redis Data Schema

Redis (v7, AOF persistence, mounted Docker volume) is the sole persistence layer.

| Key Pattern | Type | Value | TTL |
|---|---|---|---|
| `session:{session_id}:generations` | String (int) | Usage count (0–3) | 30 days |
| `user:{email}:premium` | String | `"1"` | None (permanent) |
| `token:{token}` | String | `email` | 15 minutes |
| `cache:{sha256_of_notes}` | String (JSON) | `{ "angles": [...] }` | 24 hours |

---

## 4. AI Orchestration (CrewAI + Gemini)

### LLM Configuration

```python
gemini_llm = LLM(
    model="gemini/gemini-3.1-flash-lite",  # LiteLLM syntax
    api_key=settings.gemini_api_key.get_secret_value()
)
```

The `LLM` wrapper from `crewai` uses LiteLLM under the hood, making the `GEMINI_API_KEY` env var the only required credential.

> **Legacy note:** `OPENAI_API_KEY` is present in `core/config.py` for backwards compatibility but is unused.

### Agent Definitions

| Agent | Role | Goal |
|---|---|---|
| **Strategist** | Expert Marketing Strategist | Extract value prop, target audience, key features from raw notes |
| **Copywriter** | Direct Response Copywriter | Write 3 punchy one-liners using Benefit-Driven, Problem/Solution, FOMO/Urgency frameworks |
| **Editor** | Strict QA Editor | Cross-reference copy vs. original notes (hallucination guard); output strict JSON |

### Task Chain

```
task_extract (Strategist)
    → task_write (Copywriter, context from task_extract)
        → task_edit (Editor, context from task_write, output_pydantic=CrewOutput)
```

The final task uses `output_pydantic=CrewOutput` so CrewAI maps the result to:
```python
class CrewOutput(BaseModel):
    angles: List[AngleOutput]
```

**Fallback:** If `result.pydantic` is not a `CrewOutput` instance, the service falls back to `json.loads(result.raw)` → `CrewOutput.model_validate(data)`.

### Refinement Agent

A single-shot `Copy Editor` agent handles `/refine` calls:
- **`shorter`** → "Make the copy significantly more concise. Cut fluff. Keep the punchline."
- **`casual`** → "Make the tone more conversational, relaxed, and approachable."

Returns `result.raw.strip(' "\'')` — quotes and whitespace stripped.

---

## 5. Directory Structure (Actual)

```
one-liner/
├── .env                             # Root-level env file (read by docker-compose & pydantic-settings)
├── docker-compose.yml
├── frontend/
│   ├── index.html                   # SPA shell (Tailwind CDN, Inter font)
│   ├── app.js                       # All frontend logic (state, fetch, rendering, scroll UX)
│   └── styles.css                   # Custom CSS (skeleton, progress bar, spinner, card animations)
└── backend/
    ├── Dockerfile                   # python:3.11-slim, non-root appuser
    ├── requirements.txt
    ├── main.py                      # FastAPI app, CORS, TrustedHost, router includes, static mount
    ├── core/
    │   ├── config.py                # BaseSettings: redis_url, gemini_api_key, lemonsqueezy_webhook_secret
    │   └── dependencies.py          # get_redis_client(), get_redis_repo(), get_crew_service()
    ├── api/
    │   └── routes/
    │       ├── generate.py          # /generate + /refine endpoints
    │       ├── auth.py              # /auth/request-magic-link + /auth/verify endpoints
    │       └── monetization.py      # /webhooks/lemonsqueezy endpoint
    ├── domain/
    │   └── schemas/
    │       ├── models.py            # Public API Pydantic models
    │       └── ai_schemas.py        # CrewOutput (internal CrewAI structured output)
    ├── services/
    │   └── crew_service.py          # CrewService.generate_angles() + .refine_angle()
    ├── repositories/
    │   └── redis_repo.py            # RedisRepository (rate limit, cache, premium, magic link)
    └── tests/                       # Pytest suite (fakeredis for unit tests)
```

---

## 6. Security Model

| Control | Implementation |
|---|---|
| Redis isolation | No host port exposed in `docker-compose.yml` |
| Non-root container | `appuser` created in Dockerfile; `USER appuser` set |
| CORS | Restricted to `localhost:8000`, `127.0.0.1:8000` |
| Trusted hosts | `TrustedHostMiddleware` blocks other `Host` headers |
| Webhook auth | HMAC-SHA256 `hmac.compare_digest()` before payload processing |
| Magic link | `secrets.token_urlsafe(32)`, single-use, 15-min TTL |
| Session cookie | `HttpOnly=True`, `SameSite=lax`, HS256 JWT (secret = webhook secret) |

---

## 7. Dependency Injection Pattern

```python
# core/dependencies.py
def get_redis_client() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=False)

def get_redis_repo(client: Redis = Depends(get_redis_client)) -> RedisRepository:
    return RedisRepository(client)

def get_crew_service() -> CrewService:
    return CrewService()

# Usage in route
@router.post("/generate", response_model=GenerateResponse)
def generate_angles(
    request: GenerateRequest,
    repo: RedisRepository = Depends(get_redis_repo),
    crew_service: CrewService = Depends(get_crew_service)
):
    ...
```

---

## 8. Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | ✅ Yes | `default_gemini_key` | Google Gemini API key |
| `LEMON_SQUEEZY_WEBHOOK_SECRET` | ✅ Yes | `default_secret` | Used for HMAC validation AND as JWT signing secret |
| `REDIS_URL` | ✅ Yes (Docker) | `redis://localhost:6379/0` | Overridden to `redis://redis:6379/0` by docker-compose |
| `ENVIRONMENT` | No | `development` | `production` enables stricter settings |
| `OPENAI_API_KEY` | ❌ Unused | `default_openai_key` | Legacy — not used by any active service |
