from __future__ import annotations

from .contracts import Evidence, Finding, ScanContext, Severity


class HttpBaselineScanner:
    id = "http.baseline"

    async def scan(self, context: ScanContext) -> list[Finding]:
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover - integration config issue
            raise RuntimeError("httpx is required for HTTP scanning") from exc

        context.check_url(context.target.base_url)
        async with httpx.AsyncClient(follow_redirects=False, timeout=10) as client:
            response = await client.get(context.target.base_url)

        evidence = Evidence(
            type="HTTP_RESPONSE",
            source=self.id,
            body=f"HTTP {response.status_code}\n{dict(response.headers)}",
            metadata={"url": str(response.url), "status_code": response.status_code},
        )
        findings = [
            Finding(
                title="Target responded to baseline HTTP probe",
                category="reachability",
                severity=Severity.INFO,
                confidence=1.0,
                evidence=[evidence],
            )
        ]
        if "strict-transport-security" not in response.headers and str(response.url).startswith("https://"):
            findings.append(
                Finding(
                    title="HTTPS response does not include HSTS",
                    category="transport_security",
                    severity=Severity.LOW,
                    confidence=0.7,
                    evidence=[evidence],
                    frameworks={"owasp_asvs": ["V14"]},
                )
            )
        if response.headers.get("access-control-allow-origin") == "*":
            findings.append(
                Finding(
                    title="CORS allows any origin",
                    category="cors",
                    severity=Severity.MEDIUM,
                    confidence=0.8,
                    evidence=[evidence],
                )
            )
        return findings

