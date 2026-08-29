from __future__ import annotations

import json
from pathlib import Path

import pytest

from aegisforge import __version__
from aegisforge.api import create_app
from aegisforge.config import Settings
from aegisforge.errors import AegisForgeError, ErrorCode
from aegisforge.evidence import redact, write_evidence
from aegisforge.reports import Finding, render_json, render_sarif
from aegisforge.scope import ScopePolicy, assert_url_allowed


def test_version_is_alpha() -> None:
    assert __version__ == "0.1.0-alpha"


def test_scope_denies_unlisted_host() -> None:
    with pytest.raises(AegisForgeError) as exc:
        assert_url_allowed("https://example.com", ScopePolicy())
    assert exc.value.code == ErrorCode.scope_violation


def test_scope_requires_private_network_opt_in() -> None:
    policy = ScopePolicy(allowed_hosts={"127.0.0.1"}, allowed_ports={80})
    with pytest.raises(AegisForgeError):
        assert_url_allowed("http://127.0.0.1", policy)


def test_evidence_redacts_and_hashes_stored_text(tmp_path: Path) -> None:
    record = write_evidence(tmp_path, "HTTP_REQUEST", "Authorization: Bearer secret")
    stored = Path(record.path).read_text(encoding="utf-8")
    assert "secret" not in stored
    assert record.sha256


def test_redact_api_keys() -> None:
    assert "secret" not in redact('{"api_key": "secret"}')


def test_sarif_uses_category_as_rule_id() -> None:
    sarif = json.loads(render_sarif([Finding("F-1", "Title", "llm.prompt_injection.direct")]))
    assert sarif["runs"][0]["results"][0]["ruleId"] == "llm.prompt_injection.direct"


def test_json_report_shape() -> None:
    report = json.loads(render_json([Finding("F-1", "Title", "api.baseline")]))
    assert report["findings"][0]["id"] == "F-1"


def test_settings_endpoint_does_not_echo_database_url(tmp_path: Path) -> None:
    from fastapi.testclient import TestClient

    app = create_app(
        Settings(
            data_dir=tmp_path / ".aegisforge",
            database_url=f"sqlite:///{tmp_path / 'secret-project.db'}",
        )
    )

    body = TestClient(app).get("/api/v1/settings").json()

    assert body == {"database": "sqlite", "offline": False}
    assert "secret-project.db" not in str(body)
