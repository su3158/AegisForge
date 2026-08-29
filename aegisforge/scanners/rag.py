from __future__ import annotations

from .contracts import Evidence, Finding, ScanContext, Severity


class RagBaselineScanner:
    id = "rag.baseline"

    async def scan(self, context: ScanContext) -> list[Finding]:
        evidence = Evidence(
            type="CONFIGURATION",
            source=self.id,
            body="RAG baseline expects an allowlisted retrieval endpoint and Qdrant-backed lab fixture.",
            metadata={"target": context.target.name},
        )
        return [Finding("RAG baseline probe skeleton ready", "rag", Severity.INFO, evidence=[evidence])]

