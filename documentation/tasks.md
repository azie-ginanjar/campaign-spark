# CampaignSpark — Implementation Task Tracker

> Last updated: May 2026. Phases 1–5 complete. Phase 6 in progress.

| Task Description | Status | Notes |
| :--- | :---: | :--- |
| **Phase 1: Infrastructure & Scaffolding** | | |
| Initialize project directory structure (DDD layout) | [x] | `backend/`, `frontend/`, `documentation/` |
| Create `docker-compose.yml` for FastAPI and Redis | [x] | `api` + `redis:7-alpine` services |
| Setup `requirements.txt` / Python 3.11 environment | [x] | crewai, fastapi, redis, pyjwt, fakeredis, etc. |
| Scaffold Vanilla JS SPA (`index.html`, `app.js`, `styles.css`) | [x] | Tailwind v3 CDN, Inter font |
| **Phase 1.5: Security Hardening** | | |
| Remove exposed Redis port from `docker-compose.yml` | [x] | Redis internal only, no host port mapping |
| Add non-root `appuser` execution to `backend/Dockerfile` | [x] | `useradd appuser`, `USER appuser` |
| Implement CORS and TrustedHost Middleware in `backend/main.py` | [x] | Restricted to `localhost:8000` |
| **Phase 2: Core Domain & Data Layer** | | |
| Define Pydantic models in `domain/schemas/models.py` | [x] | GenerateRequest, GenerateResponse, RefineRequest, RefineResponse, AngleOutput |
| Define internal AI schema in `domain/schemas/ai_schemas.py` | [x] | CrewOutput wrapping `List[AngleOutput]` |
| Configure `core/config.py` (BaseSettings) | [x] | redis_url, gemini_api_key, lemonsqueezy_webhook_secret |
| Implement `core/dependencies.py` (DI providers) | [x] | get_redis_client, get_redis_repo, get_crew_service |
| Implement `repositories/redis_repo.py` | [x] | rate limit, cache (SHA-256), premium status, magic link tokens |
| **Phase 3: AI Orchestration (CrewAI + Gemini)** | | |
| Switch LLM from OpenAI to Google Gemini Free Tier | [x] | `gemini/gemini-3.1-flash-lite` via LiteLLM wrapper |
| Implement Agent 1: Strategist (Input Cleaner) | [x] | Extracts value prop, audience, features from raw notes |
| Implement Agent 2: Copywriter (Angle Generator) | [x] | Writes 3 one-liners (Benefit-Driven, Problem/Solution, FOMO/Urgency) |
| Implement Agent 3: Editor (Output Formatter) | [x] | Hallucination check + strict JSON via `output_pydantic=CrewOutput` |
| Orchestrate sequential workflow in `services/crew_service.py` | [x] | `Process.sequential`, pydantic fallback to `json.loads(result.raw)` |
| Implement `refine_angle()` single-agent method | [x] | `shorter` and `casual` refinement types |
| **Phase 4: API Endpoints (FastAPI)** | | |
| Implement `POST /api/v1/generate` | [x] | Cache → rate-limit → crew → increment → cache write |
| Implement `POST /api/v1/refine` | [x] | Single-agent refinement, no generation counter impact |
| Implement `POST /api/v1/webhooks/lemonsqueezy` | [x] | HMAC-SHA256 validation, dual email extraction fallback |
| Implement `POST /api/v1/auth/request-magic-link` | [x] | Premium check → single-use token → stdout log (dev) |
| Implement `GET /api/v1/auth/verify` | [x] | Token verify → 30-day HttpOnly JWT cookie |
| **Phase 5: Frontend Integration** | | |
| Build UI layout (single-column, textarea, submit button) | [x] | Sticky header with live generation badge |
| Multi-stage agent progress tracker (progress bar + stage rows) | [x] | Strategist → Copywriter → Editor with spinners/checkmarks |
| Skeleton ghost cards during loading | [x] | 3 pulsing skeleton cards below stage tracker |
| Auto-scroll to loading bar on generate click | [x] | `scrollIntoView({ behavior: 'smooth', block: 'start' })` after 50ms |
| Auto-scroll to results after generation completes | [x] | `requestAnimationFrame` scroll after 800ms reveal delay |
| Render result cards with staggered animation | [x] | 120ms delay between cards, `card-reveal` CSS animation |
| Wire up `[Copy]`, `[Make Shorter]`, `[More Casual]` buttons | [x] | Event delegation on `cardsContainer` |
| Implement 3-generation lock and paywall modal | [x] | `403` response triggers paywall modal |
| Implement Magic Link authentication flow in UI | [x] | Login modal → email input → magic link sent → `?token=` URL verify |
| Inline error state with retry button | [x] | `loaderError` panel with `loaderRetryBtn` |
| **Phase 6: Testing & Deployment** | | |
| Unit tests for `RedisRepository` (fakeredis) | [ ] | |
| Integration tests for `/generate`, `/refine` endpoints | [ ] | |
| Integration tests for webhook and auth flow | [ ] | |
| UI cross-browser validation (Chrome, Firefox, Safari) | [ ] | |
| Configure `secure=True` cookie for HTTPS production | [ ] | Currently `secure=False` in `auth.py` |
| Wire up real email transport for magic links (SMTP/SendGrid) | [ ] | Currently stdout-only in dev |
| Build and deploy Docker containers to production VM | [ ] | |
