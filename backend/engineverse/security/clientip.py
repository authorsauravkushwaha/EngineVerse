"""Client address for rate limits and the audit log.

The default is the TCP peer. ``X-Forwarded-For`` is ignored unless
``ENGINEVERSE_TRUST_PROXY`` is on, and even then only when the peer is a
loopback or private address. A public peer that sends the header is the
client. Turning the flag on while the process is reachable from anywhere
other than the proxy lets that client pick their own address.
"""
from __future__ import annotations

import ipaddress

from ..config import get_settings


def client_ip(request) -> str:
    peer = ""
    client = getattr(request, "client", None)
    if client is not None:
        peer = getattr(client, "host", "") or ""
    peer = peer[:64]
    if not get_settings().trust_proxy or not peer:
        return peer or "unknown"
    try:
        addr = ipaddress.ip_address(peer)
    except ValueError:
        return peer
    if not (addr.is_private or addr.is_loopback):
        return peer
    headers = getattr(request, "headers", {}) or {}
    forwarded = headers.get("x-forwarded-for", "") if hasattr(headers, "get") else ""
    first = str(forwarded).split(",")[0].strip()
    if not first:
        return peer
    try:
        ipaddress.ip_address(first)
    except ValueError:
        return peer
    return first[:64]
