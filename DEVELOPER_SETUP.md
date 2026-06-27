# Developer Setup Guide

## Prerequisites

- Python 3.12+: `python3 --version`
- Node.js v22+: `node --version`
- pnpm: `npm install -g pnpm`
- moonrepo: `curl -fsSL https://moonrepo.dev/install/moon.sh | bash`

## Quick Start

```bash
# Clone
git clone <repo-url> && cd <repo>

# Python API
cd apps/api
uv sync                          # install dependencies
cp .env.example .env             # set GRPC_JWT_SECRET (required)
uv run python -m chirp_api.db.seed  # seed database
uv run python -m chirp_api.main     # start gRPC server (port 50051)

# Frontend (separate terminal)
pnpm install
pnpm dev
```

## Required Environment Variables

| Variable | Description |
|----------|-------------|
| `GRPC_JWT_SECRET` | **Required.** Strong random secret for JWT signing. Generate: `openssl rand -hex 32` |
| `DATABASE_URL` | SQLite path. Default: `sqlite:///./chirp.db` |
| `GRPC_PORT` | gRPC port. Default: `50051` |

## Running Tests

```bash
cd apps/api
GRPC_JWT_SECRET=any-test-secret uv run --with pytest pytest tests/ -q
```

## Pre-commit Hook

```bash
cat > .git/hooks/pre-commit << 'HOOK'
#!/bin/sh
cd apps/api && GRPC_JWT_SECRET=test-secret uv run --with pytest pytest tests/ -q --tb=short
HOOK
chmod +x .git/hooks/pre-commit
```
