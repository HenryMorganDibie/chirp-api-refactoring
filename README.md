# Chirp API — Production Refactoring

A security and performance refactoring of Chirp, a Twitter-like social media platform built as a polyglot monorepo. This project was a technical assessment where I audited an existing codebase, diagnosed critical vulnerabilities and performance issues, and delivered production-grade fixes across 5 task areas.

## What I Fixed

### Issue 1 — Credential Security (Critical)
The platform was storing passwords using SHA-256 with a hardcoded static salt — a fast general-purpose hash with no per-password randomness. An attacker with database access could crack all passwords in minutes using precomputed rainbow tables.

- Replaced with **bcrypt (rounds=12)** with per-password random salts
- Implemented **transparent on-login migration**: existing users log in normally and their hashes are silently upgraded to bcrypt on first successful login — no forced reset, no plaintext password required
- JWT secret previously fell back to a hardcoded string in source code, enabling token forgery by anyone with code access. Fixed to **fail fast at startup** if `GRPC_JWT_SECRET` env var is not set
- 15 new tests proving the vulnerability existed and is now resolved

### Issue 2 — N+1 Query Elimination
Every list endpoint (feed, bookmarks, user posts) was issuing 3–4 separate SQL queries **per post** to compute like counts, comment counts, and like status. A 10-post feed triggered 31 queries. Bookmarks triggered 41.

| Operation | Before | After |
|-----------|--------|-------|
| Home feed (10 posts) | 31 queries | 3 queries |
| User profile posts | 3N+1 queries | 3 queries |
| Bookmarks (10 posts) | 41 queries | 4 queries |

- Replaced per-row scalar subqueries with bulk `GROUP BY` aggregation in `query_helpers.py`
- Introduced `bulk_get_post_stats()` as a reusable pattern to prevent future regressions
- 6 new tests with SQLAlchemy event listeners counting actual DB round trips

### Issue 3 — Error Handling & Observability
No request tracing, inconsistent error handling across handlers (some used `context.abort()`, some returned empty responses, some let raw exceptions propagate).

- Added **UUID trace IDs** per gRPC call via `contextvars.ContextVar` (thread-safe)
- Unified error taxonomy: `classify_error()` maps exception messages to correct gRPC status codes
- Structured logging with trace ID, method name, and timing on every request

### Issue 4 — Test Infrastructure
- Fixed global counter state in test helpers leaking across tests
- Added 21 new tests covering credential security and query performance

### Issue 5 — Build Pipeline & Developer Experience
- CI pipeline (`.github/workflows/ci.yml`): lint → typecheck → test → build, running in parallel after install. Uses `moonrepo/setup-toolchain` and fails fast
- Pre-commit hook (`.husky/pre-commit`): lints staged changes in ~2–5s
- Fixed moonrepo config issues: missing Python toolchain declaration, Node version mismatch, `uv.lock` missing from task inputs, `GRPC_JWT_SECRET` not propagated to test tasks

## Architecture

```
apps/
  api/              Python gRPC API (grpcio, SQLAlchemy, PyJWT, bcrypt)
  client-user/      Consumer web app (TanStack Start, React 19)
  client-admin/     Admin dashboard (TanStack Start, React 19)
packages/
  proto/            Protocol Buffer definitions
  grpc-client/      TypeScript gRPC client
  shared-types/     Shared TypeScript types
  ui/               React component library (StyleX)
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Monorepo | moonrepo |
| API | Python 3.12, grpcio, SQLAlchemy 2.0, bcrypt, PyJWT |
| Client Apps | TanStack Start, React 19, StyleX |
| Protocol | gRPC (Protocol Buffers) |
| Database | SQLite |
| Testing | pytest, Vitest, Playwright |
| Linting | ruff, Biome |
| CI | GitHub Actions |

## Quick Start

```bash
git clone <repo> && cd <repo>

# Install dependencies
pnpm install
cd apps/api && pip install uv && uv sync && cd ../..

# Set required env var
export GRPC_JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Seed database and start
pnpm db:seed
moon run api:dev
```

See `DEVELOPER_SETUP.md` for the full setup guide and `AUDIT.md` for the complete technical write-up of every issue found and fixed.

## Running Tests

```bash
# Python tests
cd apps/api
GRPC_JWT_SECRET=any-test-secret python -m pytest tests/ -v

# All packages via moon
pnpm test
```
