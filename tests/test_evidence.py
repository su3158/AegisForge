import hashlib

from aegisforge.evidence import write_evidence


def test_evidence_hashes_raw_and_redacts_body(tmp_path):
    raw = "Authorization: Bearer secret-token"
    record = write_evidence(tmp_path, "HTTP_REQUEST", raw)
    assert record.sha256 == hashlib.sha256(raw.encode()).hexdigest()
    assert "secret-token" not in (tmp_path / f"{record.id}.txt").read_text(encoding="utf-8")
