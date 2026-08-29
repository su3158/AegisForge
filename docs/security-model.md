# Security Model

AegisForge assumes target interaction is risky.

Default posture:

- Deny by default.
- Explicit host and port allowlists.
- No arbitrary external callback targets.
- Redacted evidence by default.
- No usage telemetry by default.
- Harmful datasets disabled unless explicitly imported and enabled.

Scope Guard applies to HTTP, browser, LLM, Agent, MCP, and callback actions.
