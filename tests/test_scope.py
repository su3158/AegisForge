import pytest

from aegisforge.errors import AegisForgeError, ErrorCode
from aegisforge.scope import ScopePolicy, assert_url_allowed


def test_scope_denies_by_default():
    with pytest.raises(AegisForgeError) as exc:
        assert_url_allowed("https://example.com", ScopePolicy())
    assert exc.value.code is ErrorCode.scope_violation


def test_scope_allows_explicit_host_and_port():
    assert_url_allowed("https://example.com/path", ScopePolicy(allowed_hosts={"example.com"}))


def test_scope_denies_private_ip_without_opt_in():
    with pytest.raises(AegisForgeError):
        assert_url_allowed("http://127.0.0.1", ScopePolicy(allowed_hosts={"127.0.0.1"}))
