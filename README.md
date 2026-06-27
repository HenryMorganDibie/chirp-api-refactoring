# Chirp - Social Media Platform

A Twitter-like social media platform built as a polyglot monorepo with TanStack Start, React 19, Python gRPC, StyleX, and SQLite.

> NOTE: Task details are documented in TASK.md

## Prerequisites

- **Node.js** >= 20.19 (Vite 7 requirement)
- **pnpm** >= 9 (`npm install -g pnpm`)
- **Python** >= 3.12
- **moon** >= 2.0 (`curl -fsSL https://moonrepo.dev/install/moon.sh | bash`)

## Architecture

```
apps/
  api/              Python gRPC API (grpcio, SQLAlchemy, PyJWT)
  client-user/      Consumer web app (TanStack Start, React 19)
  client-admin/     Admin dashboard (TanStack Start, React 19)
packages/
  proto/            Protocol Buffer definitions (.proto files)
  grpc-client/      TypeScript gRPC client (used by web apps)
  shared-types/     Shared TypeScript types
  ui/               React component library (StyleX)
```

The monorepo is managed by [moonrepo](https://moonrepo.dev/), which orchestrates both JavaScript/TypeScript and Python projects in a unified task graph. Configuration lives in `.moon/`.

## Quick Start

### 1. Install JavaScript dependencies

```bash
pnpm install
```

### 2. Set up the Python API

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Proto stubs are pre-generated in `chirp_api/generated/`. If you need to regenerate them:

```bash
# From apps/api/ with venv active
python -m grpc_tools.protoc \
  --proto_path=../../packages/proto/protos \
  --python_out=./chirp_api/generated \
  --grpc_python_out=./chirp_api/generated \
  ../../packages/proto/protos/*.proto
```

### 3. Seed the database

```bash
# From apps/api/ with venv active
python -m chirp_api.db.seed
```

### 4. Start services

```bash
# Terminal 1 — API (from apps/api/ with venv active)
python -m chirp_api.main

# Terminal 2 — User app (from project root)
pnpm --filter @chirp/client-user dev

# Terminal 3 — Admin app (from project root)
pnpm --filter @chirp/client-admin dev
```

Or using moonrepo from the project root:

```bash
moon run api:dev       # Python API on :50051 + health on :3001
moon run client-user:dev   # User app on :3000
moon run client-admin:dev  # Admin app on :3002
```

## Service URLs

| Service | URL |
|---|---|
| User App | http://localhost:3000 |
| Admin App | http://localhost:3002 |
| API Health | http://localhost:3001/health |
| gRPC API | localhost:50051 |

## Test Accounts

| Email | Username | Password | Role |
|---|---|---|---|
| alice@test.com | alice | password123 | user |
| bob@test.com | bob | password123 | user |
| charlie@test.com | charlie | password123 | user |
| diana@test.com | diana | password123 | user |
| admin@chirp.test | admin | admin123 | admin |
| moderator@chirp.test | moderator | mod123 | moderator |

## Running Tests

```bash
# Python API unit tests (from apps/api/ with venv active)
python -m pytest tests/ -v

# JavaScript package tests (from project root)
moon run :test

# E2E tests (requires API + client-user running)
moon run client-user:test-e2e
```

## Tech Stack

| Layer | Technology |
|---|---|
| Monorepo | moonrepo |
| JS Package Manager | pnpm 9 |
| API | Python 3.12, grpcio, SQLAlchemy 2.0, PyJWT |
| Client Apps | TanStack Start, React 19, StyleX |
| Protocol | gRPC (Protocol Buffers) |
| Database | SQLite |
| JS Testing | Vitest, Playwright |
| Python Testing | pytest |
| JS Linting | Biome |
| Python Linting | ruff |
