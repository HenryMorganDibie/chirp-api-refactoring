# Chirp API — Production Audit & Stabilization

Conducted a rapid production audit of a polyglot monorepo (Python gRPC + React + moonrepo) focusing on security hardening, database performance, and observability. Delivered targeted fixes and measurable query optimization improvements across an unfamiliar codebase.

## System Context

Chirp is a Twitter-like social platform built as a production-grade monorepo — Python gRPC backend with SQLAlchemy ORM, two TypeScript/React frontends (user-facing and admin), and a shared component and proto layer orchestrated via moonrepo. The backend serves feed, bookmarks, posts, auth, follows, likes, comments, and notifications over gRPC with SQLite persistence.

The audit focused on five areas: credential security, query performance, observability, test coverage, and CI/CD pipeline integrity.

---

## Security Hardening

**Problem:** Passwords were stored using SHA-256 with a hardcoded static salt — a fast general-purpose hash with no per-password randomness. Identical passwords produced identical hashes across all users, making the entire password database vulnerable to a single precomputed rainbow table attack. Additionally, the JWT signing secret fell back to a hardcoded string in source code, meaning anyone with code access could forge valid session tokens for any user including admins.

**Risk removed:** credential replay attack surface eliminated; authentication bypass via known JWT secret closed.

**Changes:**
- Replaced SHA-256 with **bcrypt (cost factor 12)** and per-password random salts
- Designed a **zero-downtime migration path**: on login, legacy hashes are detected by format, verified against the old scheme, and silently rehashed to bcrypt in the same transaction — no forced password reset, no plaintext exposure
- JWT secret now raises `RuntimeError` at server startup if `GRPC_JWT_SECRET` is not set in the environment — no hardcoded fallback possible
- 15 tests covering the full migration path, bcrypt properties, and token forgery rejection

---

## Performance Engineering

**Problem:** Every list endpoint — home feed, bookmarks, user profile — issued 3–4 scalar subqueries **per post** inside a loop to compute like counts, comment counts, and viewer like status. This is the classic N+1 anti-pattern.

**Impact at scale:**

| Operation | Before | After | Reduction |
|-----------|--------|-------|-----------|
| Home feed (10 posts) | 31 queries | 3 queries | ~90% |
| User profile posts | 3N+1 queries | 3 queries | ~90% |
| Bookmarks (10 posts) | 41 queries | 4 queries | ~90% |

At 30-post feeds the old approach would have issued 91+ queries per request. The fix keeps query count flat regardless of result set size — O(1) round trips instead of O(N).

**Changes:**
- Introduced `bulk_get_post_stats()` in `query_helpers.py` — a single `GROUP BY` aggregation across the full result set replacing all per-row scalar subqueries
- `attach_post_stats()` merges results in Python with no additional DB round trips
- All list operations (feed, posts, bookmarks) migrated to the bulk pattern
- 6 regression tests using SQLAlchemy event listeners to count actual DB round trips — any future N+1 regression will fail CI

---

## Observability & Reliability

**Problem:** No request correlation — log lines had no shared identifier, making it impossible to reconstruct a single failing request from production logs. Error handling was inconsistent across handlers: some called `context.abort()` correctly, some returned empty responses silently, some let raw Python exceptions propagate as gRPC UNKNOWN status.

**Changes:**
- UUID trace IDs generated per gRPC call, stored in `contextvars.ContextVar` (thread-safe, zero overhead under concurrent load)
- `classify_error()` maps exception message patterns to correct gRPC status codes via a priority-ordered lookup — NOT_FOUND, ALREADY_EXISTS, UNAUTHENTICATED, PERMISSION_DENIED, INVALID_ARGUMENT, INTERNAL
- Structured log output includes trace ID, method name, user ID, and elapsed time on every request start and completion
- `handle_grpc_error()` provides a single call site for consistent error logging and abort across all handlers

---

## Test Infrastructure

- Fixed global counter state in test helpers leaking across tests in non-deterministic order
- Added 21 new tests (15 security, 6 performance) bringing total to **82 tests**
- Performance tests use SQLAlchemy `before_cursor_execute` event listeners to count actual round trips — not mocked, not estimated

---

## CI/CD & Developer Experience

**Problems found in monorepo config:**
- Python toolchain undeclared in `toolchains.yml` — moon couldn't manage Python version
- Node version declared as 20 despite project requiring 22+
- `uv.lock` missing from Python task inputs — stale venvs could pass CI silently
- `GRPC_JWT_SECRET` not propagated to test tasks — tests would fail at import after the security fix

**Changes:**
- `.github/workflows/ci.yml`: lint → typecheck → test → build pipeline; lint/typecheck/test run in parallel after install; build gates on all three passing
- Pre-commit hook runs `moon run :lint --affected` on staged files only — fast enough (~2–5s) to be practical
- All moonrepo config issues corrected; `GRPC_JWT_SECRET` propagated to test environments

---

## Stack

| Layer | Technology |
|-------|------------|
| Monorepo | moonrepo |
| API | Python 3.12, gRPC, SQLAlchemy 2.0, bcrypt, PyJWT |
| Frontends | TanStack Start, React 19, StyleX |
| Protocol | Protocol Buffers |
| Testing | pytest (82 tests), Vitest, Playwright |
| Linting | ruff, Biome |
| CI | GitHub Actions |

---

## Quick Start

```bash
git clone https://github.com/HenryMorganDibie/chirp-api-refactoring.git
cd chirp-api-refactoring

pnpm install
cd apps/api && pip install uv && uv sync && cd ../..

export GRPC_JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")

pnpm db:seed
moon run api:dev
```

```bash
# Run tests
cd apps/api
GRPC_JWT_SECRET=any-test-secret python -m pytest tests/ -v
# 82 passed
```

See `AUDIT.md` for the full technical write-up and `DEVELOPER_SETUP.md` for the complete setup guide.
