from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from aegisforge.api import create_app
from aegisforge.config import Settings


def settings(tmp_path: Path, *, auth: bool = False, secret_key: str = "test-secret-key") -> Settings:
    return Settings(
        data_dir=tmp_path / ".aegisforge",
        database_url=f"sqlite:///{tmp_path / 'aegisforge.db'}",
        admin_password="admin-password" if auth else None,
        secret_key=secret_key if auth else None,
    )


def login(client: TestClient) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"password": "admin-password"})
    assert response.status_code == 200
    token = response.json()["csrf_token"]
    return {"X-CSRF-Token": token}


def create_project_target_scope(client: TestClient, headers: dict[str, str]) -> dict[str, Any]:
    project = client.post("/api/v1/projects", json={"name": "Demo"}, headers=headers).json()
    target = client.post(
        "/api/v1/targets",
        json={
            "project_id": project["id"],
            "name": "Demo target",
            "base_url": "https://ai.example.test/chat",
        },
        headers=headers,
    ).json()
    scope = client.post(
        "/api/v1/scopes",
        json={
            "project_id": project["id"],
            "name": "confirmed",
            "allowed_hosts": ["ai.example.test"],
            "allowed_ports": [443],
            "confirmed": True,
        },
        headers=headers,
    ).json()
    target = client.post(
        "/api/v1/targets",
        json={
            "project_id": project["id"],
            "name": "Scoped target",
            "base_url": "https://ai.example.test/chat",
            "scope_profile_id": scope["id"],
        },
        headers=headers,
    ).json()
    return {"project": project, "target": target, "scope": scope}


def test_local_mode_can_create_project_without_auth(tmp_path: Path) -> None:
    client = TestClient(create_app(settings(tmp_path)))

    response = client.post("/api/v1/projects", json={"name": "Local"})

    assert response.status_code == 200
    assert response.json()["name"] == "Local"


def test_auth_mode_requires_session_and_csrf(tmp_path: Path) -> None:
    client = TestClient(create_app(settings(tmp_path, auth=True)))

    assert client.post("/api/v1/projects", json={"name": "Nope"}).status_code == 401
    headers = login(client)
    assert client.post("/api/v1/projects", json={"name": "No csrf"}).status_code == 403
    response = client.post("/api/v1/projects", json={"name": "Protected"}, headers=headers)

    assert response.status_code == 200


def test_target_scope_candidates_and_scan_start_require_confirmed_scope(tmp_path: Path) -> None:
    client = TestClient(create_app(settings(tmp_path, auth=True)))
    headers = login(client)
    project = client.post("/api/v1/projects", json={"name": "Demo"}, headers=headers).json()
    target = client.post(
        "/api/v1/targets",
        json={"project_id": project["id"], "name": "T", "base_url": "https://ai.example.test/chat"},
        headers=headers,
    ).json()
    scan = client.post(
        "/api/v1/scans",
        json={"project_id": project["id"], "target_id": target["id"]},
        headers=headers,
    ).json()

    assert target["scope_candidates"] == {"allowed_hosts": ["ai.example.test"], "allowed_ports": [443]}
    assert client.post(f"/api/v1/scans/{scan['id']}/start", headers=headers).status_code == 400

    rows = create_project_target_scope(client, headers)
    scan = client.post(
        "/api/v1/scans",
        json={"project_id": rows["project"]["id"], "target_id": rows["target"]["id"]},
        headers=headers,
    ).json()
    started = client.post(f"/api/v1/scans/{scan['id']}/start", headers=headers)

    assert started.status_code == 200
    assert started.json()["status"] == "running"


def test_secret_values_are_not_returned_and_are_audited(tmp_path: Path) -> None:
    client = TestClient(create_app(settings(tmp_path, auth=True)))
    headers = login(client)

    created = client.post(
        "/api/v1/settings/secrets",
        json={"name": "openai", "value": "sk-test-secret"},
        headers=headers,
    ).json()
    listed = client.get("/api/v1/settings/secrets", headers=headers).json()
    audit = client.get("/api/v1/audit-log", headers=headers).json()

    assert created["name"] == "openai"
    assert "sk-test-secret" not in str(created)
    assert "encrypted_value" not in str(listed)
    assert any(row["action"] == "secret_created" for row in audit)


def test_raw_evidence_reveal_requires_admin_reauth_and_audit(tmp_path: Path) -> None:
    client = TestClient(create_app(settings(tmp_path, auth=True)))
    headers = login(client)
    rows = create_project_target_scope(client, headers)
    evidence = client.post(
        "/api/v1/evidence",
        json={
            "project_id": rows["project"]["id"],
            "target_id": rows["target"]["id"],
            "evidence_type": "PROMPT",
            "body": "Authorization: Bearer secret-token",
            "raw_body": "Authorization: Bearer secret-token",
        },
        headers=headers,
    ).json()

    assert "secret-token" not in evidence["redacted_body"]
    denied = client.post(
        f"/api/v1/evidence/{evidence['id']}/raw",
        json={"password": "wrong"},
        headers=headers,
    )
    revealed = client.post(
        f"/api/v1/evidence/{evidence['id']}/raw",
        json={"password": "admin-password"},
        headers=headers,
    )
    audit = client.get("/api/v1/audit-log", headers=headers).json()

    assert denied.status_code == 401
    assert revealed.json()["body"] == "Authorization: Bearer secret-token"
    assert any(row["action"] == "raw_evidence_revealed" for row in audit)
