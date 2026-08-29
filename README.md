# AegisForge

Open-source AI Application Security Assessment and Red Team Orchestration Platform.

AegisForge is planned as an evidence-first security assessment platform for applications that combine Web, API, RAG, LLM, Agent, MCP/tool, and downstream system behavior. It is not intended to be only a prompt injection scanner.

Status: `0.1.0-alpha` skeleton in progress. This repository is not v1-complete yet.

## Scope

The alpha foundation targets:

- Local Lite: FastAPI, React UI, embedded worker, SQLite, local filesystem evidence.
- Full/Postgres mode: FastAPI, worker command, PostgreSQL, filesystem evidence volume.
- CLI: `aegisforge init`, `serve`, `stop`, `worker`, `scan`, `report`, `frameworks sync`, and diagnostics.
- Scanners: HTTP, LLM API, browser/UI flows, RAG, Agent, MCP, and optional external scanner enrichment.
- Safety: deny-by-default Scope Guard, redacted evidence, explicit dataset import, no usage telemetry.

## License

AegisForge is licensed under Apache-2.0. Third-party framework or dataset material is not treated as AegisForge-owned code.

## Runtime Support

Official alpha targets:

- Linux
- Windows

Docker or Podman-compatible Compose is required for lab and E2E environments. macOS support is expected later but is not an alpha support target.

## Local Lite

Start:

```bash
uv sync
uv run aegisforge init
uv run aegisforge serve
```

Stop a foreground server with `Ctrl+C`.

Detached start:

```bash
uv run aegisforge serve --detach
```

Stop a detached local server:

```bash
uv run aegisforge stop
```

## Development UI

The production UI is served by FastAPI after it is built. Frontend development uses Node 22 and pnpm.

```bash
corepack enable
corepack pnpm --dir apps/web install
corepack pnpm --dir apps/web dev
```

## Worker

Local Lite embeds a single worker. Full mode can run an explicit worker:

```bash
uv run aegisforge worker
```

## Compose

Lab mode with deterministic local targets and Qdrant:

```bash
docker compose --profile lab up --build
docker compose --profile lab down
```

Full/Postgres mode:

```bash
docker compose --profile full up --build
docker compose --profile full down
```

Destructive data cleanup:

```bash
docker compose --profile lab --profile full down -v
```

Local Lite cleanup removes the project data directory:

```bash
rm -rf .aegisforge
```

On Windows PowerShell:

```powershell
Remove-Item -Recurse -Force .aegisforge
```

## Framework Data

Framework control data is synced explicitly. AegisForge does not silently bundle or update third-party framework material.

```bash
uv run aegisforge frameworks sync --accept-license
```

Each scan records the framework versions used.

## Datasets

The core distribution should only include minimal safe probes. External attack datasets require explicit import, pinned revision, license metadata, hashes, and a dataset lock file.

Harmful datasets require isolated opt-in and must not be enabled by default.

## Telemetry

AegisForge does not send usage telemetry to project maintainers by default. Local logs, metrics, and traces may be generated for debugging and must avoid leaking raw secrets.

## Non-goals

AegisForge is not a full SAST, full DAST, malware analysis system, SIEM, cloud CSPM, Kubernetes scanner, or unrestricted autonomous exploitation platform.
