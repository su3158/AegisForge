from __future__ import annotations

from .contracts import Evidence, Finding, ScanContext, Severity


class AgentBaselineScanner:
    id = "agent.baseline"

    async def scan(self, context: ScanContext) -> list[Finding]:
        evidence = Evidence(
            type="AGENT_TRACE",
            source=self.id,
            body="SAFE profile agent checks only enumerate read-only allowlisted tools.",
            metadata={"target": context.target.name},
        )
        return [Finding("Agent baseline probe skeleton ready", "agent", Severity.INFO, evidence=[evidence])]

