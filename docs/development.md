# Development

## Requirements

- Linux or Windows.
- Python 3.14 for CI parity.
- `uv`.
- Node 22 and pnpm for frontend development.
- Docker or Podman-compatible Compose for lab and E2E.

## Local Commands

```bash
uv sync --all-extras
uv run pytest
uv run ruff check .
uv run mypy aegisforge
```

```bash
corepack enable
corepack pnpm --dir apps/web install
corepack pnpm --dir apps/web build
```

## Compose

```bash
docker compose --profile lab up --build
docker compose --profile lab down
docker compose --profile lab down -v
```
