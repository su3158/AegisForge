from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aegisforge.integrations.sse import parse_sse

from .contracts import Evidence, Finding, ScanContext, Severity


@dataclass(frozen=True)
class LlmResponse:
    text: str
    raw: dict[str, Any] | list[dict[str, Any]]
    streamed: bool = False


class OpenAICompatibleAdapter:
    def __init__(self, base_url: str, api_key: str | None = None, mode: str = "chat_completions"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.mode = mode

    async def complete(self, model: str, prompt: str, stream: bool = False) -> LlmResponse:
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover - integration config issue
            raise RuntimeError("httpx is required for LLM API scanning") from exc

        headers = {"authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        path, payload = self._request(model, prompt, stream)
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(f"{self.base_url}{path}", json=payload, headers=headers)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if stream or "text/event-stream" in content_type:
            events = parse_sse(response.text.splitlines())
            return LlmResponse(text=_text_from_events(events), raw=events, streamed=True)
        raw = response.json()
        return LlmResponse(text=_text_from_json(raw), raw=raw)

    def _request(self, model: str, prompt: str, stream: bool) -> tuple[str, dict[str, Any]]:
        if self.mode == "responses":
            return "/v1/responses", {"model": model, "input": prompt, "stream": stream}
        return "/v1/chat/completions", {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": stream,
        }


class LlmBaselineScanner:
    id = "llm.baseline"

    async def scan(self, context: ScanContext) -> list[Finding]:
        adapter = OpenAICompatibleAdapter(
            context.target.base_url,
            api_key=context.options.get("api_key"),
            mode=context.options.get("mode", "chat_completions"),
        )
        prompt = "Reply with exactly: AEGISFORGE_OK"
        result = await adapter.complete(context.options.get("model", "demo"), prompt)
        evidence = Evidence(
            type="COMPLETION",
            source=self.id,
            body=result.text,
            metadata={"mode": adapter.mode, "streamed": result.streamed},
        )
        return [
            Finding(
                title="LLM endpoint completed baseline probe",
                category="llm_reachability",
                severity=Severity.INFO,
                confidence=1.0 if "AEGISFORGE_OK" in result.text else 0.5,
                evidence=[evidence],
            )
        ]


def _text_from_json(raw: dict[str, Any]) -> str:
    if "output_text" in raw:
        return str(raw["output_text"])
    if raw.get("choices"):
        return str(raw["choices"][0].get("message", {}).get("content", ""))
    output = raw.get("output") or []
    texts = [
        part.get("text", "")
        for item in output
        for part in item.get("content", [])
        if part.get("type") in {"output_text", "text"}
    ]
    return "\n".join(texts)


def _text_from_events(events: list[dict[str, Any]]) -> str:
    chunks: list[str] = []
    for event in events:
        data = event["data"]
        if data == "[DONE]":
            continue
        if isinstance(data, dict):
            chunks.append(_text_from_json(data))
        else:
            chunks.append(str(data))
    return "".join(chunks)


if __name__ == "__main__":
    assert _text_from_json({"choices": [{"message": {"content": "ok"}}]}) == "ok"
    assert _text_from_json({"output_text": "ok"}) == "ok"
