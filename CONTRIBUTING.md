# Contributing

AegisForge is currently an alpha skeleton. Keep changes small and evidence-driven.

## Development

Backend:

```bash
uv sync --all-extras
uv run pytest
uv run ruff check .
uv run mypy aegisforge
```

Frontend:

```bash
corepack enable
corepack pnpm --dir apps/web install
corepack pnpm --dir apps/web build
```

## Rules

- Do not add scanners that can touch out-of-scope targets.
- Route HTTP, browser, LLM, Agent, MCP, and callback actions through Scope Guard.
- Do not store raw secrets in plaintext.
- Do not bundle third-party framework data without license review.
- Do not enable harmful datasets by default.
- Keep optional integrations optional.

## Pull Requests

Include:

- What changed.
- How it was tested.
- Any security or scope impact.
- Any new dependency and why it is needed.
