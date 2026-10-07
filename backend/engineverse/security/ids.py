"""ULID generation.

26-character, lexicographically sortable identifiers (48-bit millisecond
timestamp + 80 bits of randomness). Sortable keys let the PostgreSQL schema
range-partition hot tables by time without a global sequence - which is what
makes horizontal sharding possible later.
"""
from __future__ import annotations

import os
import threading
import time
from datetime import date, datetime, timedelta, timezone

_ENCODING = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"  # Crockford base32
_MASK = (1 << 80) - 1
_lock = threading.Lock()
_last_ms = -1
_last_random = int.from_bytes(os.urandom(10), "big")


def _encode(value: int, length: int) -> str:
    out = []
    for _ in range(length):
        out.append(_ENCODING[value & 0x1F])
        value >>= 5
    return "".join(reversed(out))


def ulid(when: float | None = None) -> str:
    """Returns a new ULID. Monotonic within the same millisecond."""
    global _last_ms, _last_random
    ms = int((time.time() if when is None else when) * 1000)
    with _lock:
        if ms <= _last_ms:
            # Same (or regressed) millisecond: keep the timestamp monotonic and
            # increment the random component so ids stay unique and ordered.
            ms = _last_ms
            _last_random = (_last_random + 1) & _MASK
        else:
            _last_ms = ms
            _last_random = int.from_bytes(os.urandom(10), "big")
        random_part = _last_random
    return _encode(ms, 10) + _encode(random_part, 16)


def now_ms() -> int:
    return int(time.time() * 1000)


def today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def day_string(offset_days: int = 0) -> str:
    return (datetime.now(timezone.utc).date() + timedelta(days=offset_days)).isoformat()


def parse_day(value: str) -> date:
    return date.fromisoformat(value)
