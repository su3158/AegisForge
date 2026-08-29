# Architecture

AegisForge is planned around one assessment flow:

Web -> API -> RAG -> LLM -> Agent -> MCP/Tool -> External System

Core components:

- Control API.
- Embedded or external worker.
- Scope Guard.
- Target adapters.
- Scanner contracts.
- Result normalizer.
- Evidence store.
- Findings and reports.

All active actions must pass through Scope Guard before execution.
