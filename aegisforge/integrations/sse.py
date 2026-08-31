from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any


def parse_sse(lines: Iterable[str]) -> list[dict[str, Any]]:
    # Shared by LLM and MCP adapters so streaming evidence is parsed consistently.
    events: list[dict[str, Any]] = []
    event: str | None = None
    data: list[str] = []
    for raw in lines:
        line = raw.rstrip("\r\n")
        if not line:
            if data:
                events.append(_event(event, data))
            event, data = None, []
            continue
        if line.startswith(":"):
            continue
        field, _, value = line.partition(":")
        value = value.removeprefix(" ")
        if field == "event":
            event = value
        elif field == "data":
            data.append(value)
    if data:
        events.append(_event(event, data))
    return events


def _event(event: str | None, data: list[str]) -> dict[str, Any]:
    text = "\n".join(data)
    try:
        payload: Any = json.loads(text)
    except json.JSONDecodeError:
        payload = text
    return {"event": event or "message", "data": payload}


if __name__ == "__main__":
    assert parse_sse(["event: x\n", 'data: {"ok": true}\n', "\n"]) == [
        {"event": "x", "data": {"ok": True}}
    ]
