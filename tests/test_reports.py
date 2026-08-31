import json

from aegisforge.reports import Finding, render_html, render_json, render_markdown, render_sarif


def test_report_serializers_use_plugin_id_for_sarif_rule():
    finding = Finding(
        id="F-1",
        title="Prompt injection",
        category="prompt_injection",
        severity="HIGH",
        plugin_id="llm.prompt.direct",
    )
    assert json.loads(render_json([finding]))["findings"][0]["title"] == "Prompt injection"
    assert "Prompt injection" in render_markdown([finding])
    assert "<!doctype html>" in render_html([finding])
    sarif = json.loads(render_sarif([finding]))
    assert sarif["runs"][0]["results"][0]["ruleId"] == "llm.prompt.direct"
