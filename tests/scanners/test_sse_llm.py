from aegisforge.integrations.sse import parse_sse
from aegisforge.scanners.llm import _text_from_json


def test_sse_json_event() -> None:
    assert parse_sse(["event: message\n", 'data: {"x": 1}\n', "\n"]) == [
        {"event": "message", "data": {"x": 1}}
    ]


def test_llm_text_shapes() -> None:
    assert _text_from_json({"choices": [{"message": {"content": "chat"}}]}) == "chat"
    assert _text_from_json({"output_text": "responses"}) == "responses"
