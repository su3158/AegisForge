from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass, field
from urllib.parse import urlparse

from .errors import AegisForgeError, ErrorCode


@dataclass(frozen=True)
class ScopePolicy:
    allowed_hosts: set[str] = field(default_factory=set)
    allowed_ports: set[int] = field(default_factory=lambda: {80, 443})
    allow_private_networks: bool = False
    external_network_allowed: bool = False
    max_requests: int = 10_000
    max_concurrency: int = 5
    requests_per_second: int = 5
    destructive_tests: bool = False
    data_modification: bool = False


def _is_private_host(host: str) -> bool:
    try:
        addresses = {ipaddress.ip_address(host)}
    except ValueError:
        try:
            addresses = {ipaddress.ip_address(addr[4][0]) for addr in socket.getaddrinfo(host, None)}
        except OSError:
            return False
    return any(addr.is_private or addr.is_loopback or addr.is_link_local for addr in addresses)


def assert_url_allowed(url: str, policy: ScopePolicy) -> None:
    # All outbound execution paths call this before touching a target.
    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if parsed.scheme not in {"http", "https"} or not host:
        raise AegisForgeError(ErrorCode.scope_violation, f"Unsupported target URL: {url}")
    if host not in policy.allowed_hosts:
        raise AegisForgeError(ErrorCode.scope_violation, f"Host is outside scope: {host}")
    if port not in policy.allowed_ports:
        raise AegisForgeError(ErrorCode.scope_violation, f"Port is outside scope: {port}")
    if _is_private_host(host) and not policy.allow_private_networks:
        raise AegisForgeError(ErrorCode.scope_violation, f"Private network target requires opt-in: {host}")
