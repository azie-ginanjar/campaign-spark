# CampaignSpark — Product Requirements Document (PRD)

> **Status:** MVP Complete (Phases 1–5 delivered). Phase 6 (E2E testing & production deployment) in progress.

---

## 1. Executive Summary

CampaignSpark is a lightweight, AI-powered Single Page Application that converts unstructured product notes into polished, high-converting marketing one-liners. It targets digital marketing agencies, solo founders, and indie developers who need strong copy fast — without hiring a copywriter.

---

## 2. Problem Statement

Marketers and founders struggle to distill complex, unstructured product notes into concise, compelling marketing angles. The result is weak copy and low conversion rates.

---

## 3. User Journey

1. User arrives at the clean, single-column layout landing page.
2. A sticky header shows the **CampaignSpark** logo, a live "Free Plan: X/3 Generations Remaining" badge (green → red as limit approaches), and an "Already Paid? Log in" button.
3. User pastes messy product notes into the textarea (min 10 chars, max 5,000 chars).
4. User clicks **"Generate Angles"**.
5. The page **auto-scrolls** to reveal a multi-stage progress tracker:
   - A progress bar animates through 0% → 12% → 48% → 82% → 100%.
   - Three agent stages show inline spinners: **Strategist** → **Copywriter** → **Editor**, each ✅-ing as they complete.
   - Three skeleton ghost cards pulse below the tracker while generation runs.
6. On completion, the page **auto-scrolls** to the results section where three distinct cards appear with a staggered reveal animation.
7. Each card displays the angle type badge, the copy, and three action buttons: **[Make Shorter]**, **[More Casual]**, **[Copy]**.
8. Refinement (`[Make Shorter]` / `[More Casual]`) triggers a single-agent Gemini call in-place; the card pulses while refining.
9. On reaching the 3-generation limit, the generate button returns a `403` and the **Paywall Modal** appears:
   - **"Get Lifetime Access"** → redirects to LemonSqueezy checkout.
   - **"Restore Purchase"** → opens the Magic Link login modal.
   - **"Already Paid? Log in"** → same magic link modal.
10. **Post-Payment**: LemonSqueezy fires a webhook → backend marks the email as premium in Redis. User requests a magic link → token emailed (currently logged to stdout in dev) → clicking the link sets a 30-day HttpOnly JWT cookie granting unlimited access.

---

## 4. Functional Requirements

| # | Requirement | Status |
|---|---|---|
| F-01 | Lightweight SPA (HTML/JS + Tailwind CSS v3) with single-column layout | ✅ Done |
| F-02 | FastAPI backend with strict Pydantic V2 typing | ✅ Done |
| F-03 | 3-agent CrewAI workflow (Strategist → Copywriter → Editor) via Gemini | ✅ Done |
| F-04 | Redis session tracking, rate-limiting (3 free generations), 30-day TTL | ✅ Done |
| F-05 | SHA-256 request caching (24-hour TTL for identical notes) | ✅ Done |
| F-06 | `[Make Shorter]` and `[More Casual]` inline refinement | ✅ Done |
| F-07 | LemonSqueezy webhook with HMAC-SHA256 signature verification | ✅ Done |
| F-08 | Passwordless Magic Link authentication (single-use, 15-min TTL) | ✅ Done |
| F-09 | HttpOnly JWT cookie (30-day, HS256) for premium session persistence | ✅ Done |
| F-10 | Auto-scroll UX: focus on progress bar during loading, results after | ✅ Done |
| F-11 | Paywall modal with upgrade CTA and restore access flow | ✅ Done |
| F-12 | E2E API testing (Pytest + fakeredis) | 🔄 In Progress |
| F-13 | Cross-browser UI validation | 🔄 In Progress |
| F-14 | Production Docker deployment | 🔄 In Progress |

---

## 5. Out of Scope

- Relational databases (e.g., PostgreSQL) or vector databases.
- Complex OAuth / username-password authentication.
- Persisted history of past generation sessions.
- Email delivery infrastructure in development (magic links are logged to stdout).

---

## 6. Monetisation Model

| Tier | Generations | Price |
|---|---|---|
| Free | 3 (per browser session, 30-day reset) | $0 |
| Lifetime Access | Unlimited | $29 one-time |

Payment processed via **LemonSqueezy**. Access granted via email-based magic link.
