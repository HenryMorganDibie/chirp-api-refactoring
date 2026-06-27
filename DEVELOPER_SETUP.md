# Developer Setup Guide

## Prerequisites

- Python 3.12+: `python3 --version`
- Node.js v22+: `node --version`
- pnpm: `npm install -g pnpm`
- moonrepo: `curl -fsSL https://moonrepo.dev/install/moon.sh | bash`
- uv: `pip install uv`

## Quick Start

```bash
git clone <repo-url> && cd <repo>
pnpm install
cd apps/api && uv sync && cd ../..
export GRPC_JWT_SECRET=$(openssl rand -hex 32)
cp .husky/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
pnpm db:seed
pnpm dev
```

## Required Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GRPC_JWT_SECRET` | Yes | JWT signing secret. Generate: `openssl rand -hex 32` |
| `DATABASE_URL` | No | Default: `sqlite:///./chirp.db` |
| `GRPC_PORT` | No | Default: `50051` |

## Running Tests

```bash
pnpm test
cd apps/api && GRPC_JWT_SECRET=any-test-secret uv run --with pytest pytest tests/ -q
```

## CI

GitHub Actions runs on every PR: lint -> typecheck -> test -> build.
Only changed packages and their dependents rebuild (`moon --affected`).

## Common Commands

```bash
pnpm build       # Build all packages
pnpm lint        # Lint all packages
pnpm typecheck   # Type-check all packages
pnpm db:seed     # Seed the database
```
