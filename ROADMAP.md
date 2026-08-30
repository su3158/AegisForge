# Roadmap

This roadmap is a planning document, not a guarantee.

## 0.1.0-alpha

- Repository skeleton, package metadata, CLI entrypoints, FastAPI app, React/Vite UI shell.
- Local Lite start/stop, detached start/stop, embedded worker, SQLite, local evidence files.
- Full/Postgres Compose path and worker command.
- Deny-by-default Scope Guard for HTTP, browser, LLM, Agent, MCP, and callbacks.
- Evidence hashing, redaction defaults, report exporters for JSON, Markdown, HTML, and SARIF.
- Baseline scanner contracts for HTTP, LLM API, browser UI flow, RAG, Agent, and MCP.
- Deterministic demo lab with Qdrant-backed RAG.
- Linux and Windows GitHub CI.

## 0.2.0-alpha

- Typed Local Lite data model for core assessment records.
- Local API workflow for project, target, scope, scan, finding, evidence, secret, coverage, and attack-chain reads/writes.
- In-process scan runner with timeout, cancel, redacted evidence, standard-probe consent, and Scope Guard validation.
- Browser-flow YAML validation for UI-driven LLM and Agent interactions.
- React console workflow for targets, scan wizard, evidence, raw reveal UX, settings, coverage, attack chains, language switch, and dark mode.
- README screenshots generated from the real Playwright-tested UI.
- GitHub CI remains the primary Linux/Windows verification path.

## v1.0

- Project, target, scan, finding, evidence, report, and framework coverage workflows.
- ASVS 5.0 L2 inventory with automated, semi-automated, and manual classifications.
- OWASP GenAI LLM Top 10 and OWASP Agentic Top 10 mappings.
- Browser-driven LLM and Agent assessment using saved Playwright flows.
- Safe scanner regression fixtures with no real internet targets.
- HTML, Markdown, JSON, and SARIF reports.
- Docker/Compose deployment docs and OSS contribution/security process.

## v1.1

- Adaptive AI planner.
- Advanced attack chain correlation.
- AIBOM and model provenance.
- OIDC.
- External secret managers.
- DNS callback sink.
- Advanced browser scanning.
- Richer Promptfoo, garak, and PyRIT integrations.

## v2

- Distributed scanning.
- Multi-user RBAC.
- Continuous AI security assessment.
- Runtime agent monitoring.
- Model drift and security regression analytics.
- Enterprise SSO.
- Policy as code.
- Custom framework builder.

## Deferred

- macOS as an official support target.
- PDF export.
- Redis queue and MinIO/S3 object storage.
- Full SIEM integration.
- Production-grade distributed scheduling.
