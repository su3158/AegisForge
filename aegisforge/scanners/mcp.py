from __future__ import annotations

from .contracts import Evidence, Finding, ScanContext, Severity


class McpBaselineScanner:
    id = "mcp.baseline"

    async def scan(self, context: ScanContext) -> list[Finding]:
        evidence = Evidence(
            type="TOOL_RESULT",
            source=self.id,
            body="MCP baseline checks tool enumeration and read-only allowlist boundaries.",
            metadata={"target": context.target.name},
        )
        return [Finding("MCP baseline probe skeleton ready", "mcp", Severity.INFO, evidence=[evidence])]

