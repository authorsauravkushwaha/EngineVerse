"""Time-based one-time passwords and one-time recovery codes.

The secret is sealed with the application secret before it is stored. This is
application-level encryption, not a hardware module: anyone who can read both
the database and ``ENGINEVERSE_SECRET`` can open it. Rotating that secret makes
existing seals unreadable. ``scripts/create_admin.py --replace`` clears the
super administrator's seal so that recovery does not need the old secret.

No third-party authenticator service is contacted. The settings page shows the
secret and an ``otpauth://`` URI. It does not draw a QR code from a remote host.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import struct
import time
from urllib.parse import quote

from ..config import get_settings

STEP_SECONDS = 30
DIGITS = 6
_LOGIN_TTL = 300
_ENROLL_TTL = 600


def random_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def _decode_secret(secret: str) -> bytes:
    padded = secret.strip().upper() + "=" * ((8 - len(secret.strip()) % 8) % 8)
    return base64.b32decode(padded, casefold=True)


def code_at(secret: str, counter: int) -> str:
    digest = hmac.new(_decode_secret(secret), struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    binary = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return f"{binary % 1_000_000:06d}"


def verify_totp(secret: str, code: str, *, now: float | None = None, window: int = 1) -> bool:
    digits = "".join(ch for ch in (code or "") if ch.isdigit())
    if len(digits) != DIGITS or not secret:
        return False
    moment = time.time() if now is None else now
    counter = int(moment // STEP_SECONDS)
    for delta in range(-window, window + 1):
        if hmac.compare_digest(code_at(secret, counter + delta), digits):
            return True
    return False


def provisioning_uri(secret: str, account: str, issuer: str) -> str:
    label = quote(f"{issuer}:{account}")
    return (
        f"otpauth://totp/{label}?secret={secret}"
        f"&issuer={quote(issuer)}&algorithm=SHA1&digits={DIGITS}&period={STEP_SECONDS}"
    )


def recovery_codes() -> list[str]:
    """Eight single-use codes. Shown once. Only hashes are stored."""
    return [secrets.token_hex(5) for _ in range(8)]


def _hash_code(code: str) -> str:
    compact = "".join(ch for ch in code.lower() if ch in "0123456789abcdef")
    return hashlib.sha256(compact.encode("ascii")).hexdigest()


def _seal_key() -> bytes:
    return hashlib.sha256(get_settings().effective_secret() + b"engineverse-totp-seal").digest()


def _token_key() -> bytes:
    return hashlib.sha256(get_settings().effective_secret() + b"engineverse-totp-token").digest()


def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    blocks = []
    counter = 0
    while sum(len(block) for block in blocks) < length:
        blocks.append(hmac.new(key, nonce + counter.to_bytes(4, "big"), hashlib.sha256).digest())
        counter += 1
    return b"".join(blocks)[:length]


def seal(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    nonce = secrets.token_bytes(16)
    cipher = bytes(a ^ b for a, b in zip(raw, _keystream(_seal_key(), nonce, len(raw))))
    mac = hmac.new(_seal_key(), nonce + cipher, hashlib.sha256).digest()
    return "v1:" + base64.urlsafe_b64encode(nonce + mac + cipher).decode("ascii")


def unseal(stored: str) -> dict | None:
    if not stored or not stored.startswith("v1:"):
        return None
    try:
        blob = base64.urlsafe_b64decode(stored[3:] + "=" * ((4 - len(stored[3:]) % 4) % 4))
    except (ValueError, TypeError):
        return None
    if len(blob) < 48:
        return None
    nonce, mac, cipher = blob[:16], blob[16:48], blob[48:]
    expected = hmac.new(_seal_key(), nonce + cipher, hashlib.sha256).digest()
    if not hmac.compare_digest(mac, expected):
        return None
    raw = bytes(a ^ b for a, b in zip(cipher, _keystream(_seal_key(), nonce, len(cipher))))
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def pack(secret: str, codes: list[str]) -> str:
    return seal({"secret": secret, "recovery": [_hash_code(code) for code in codes]})


def verify_factor(stored: str, code: str) -> tuple[bool, str | None]:
    """Check a TOTP or recovery code.

    The second value is a replacement seal when a recovery code was consumed.
    A TOTP match leaves the seal unchanged.
    """
    payload = unseal(stored)
    if not payload or not payload.get("secret"):
        return False, None
    if verify_totp(str(payload["secret"]), code):
        return True, None
    submitted = _hash_code(code)
    if len(submitted) != 64:
        return False, None
    remaining = []
    matched = False
    for hashed in payload.get("recovery") or []:
        if not matched and hmac.compare_digest(str(hashed), submitted):
            matched = True
            continue
        remaining.append(hashed)
    if not matched:
        return False, None
    payload["recovery"] = remaining
    return True, seal(payload)


def _sign(payload: dict) -> str:
    body = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")).decode("ascii").rstrip("=")
    sig = hmac.new(_token_key(), body.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def _read(token: str) -> dict | None:
    if not token or "." not in token:
        return None
    body, _, sig = token.rpartition(".")
    expected = hmac.new(_token_key(), body.encode("ascii"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return None
    try:
        padded = body + "=" * ((4 - len(body) % 4) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
    except (ValueError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or int(payload.get("e") or 0) < time.time():
        return None
    return payload


def issue_login_token(user_id: str) -> str:
    return _sign({"k": "login", "u": user_id, "e": int(time.time()) + _LOGIN_TTL})


def read_login_token(token: str) -> str | None:
    payload = _read(token)
    if not payload or payload.get("k") != "login" or not payload.get("u"):
        return None
    return str(payload["u"])


def issue_enroll_token(user_id: str, secret: str, codes: list[str]) -> str:
    return _sign({
        "k": "enroll",
        "u": user_id,
        "e": int(time.time()) + _ENROLL_TTL,
        "s": secret,
        "c": codes,
    })


def read_enroll_token(token: str, user_id: str) -> dict | None:
    payload = _read(token)
    if not payload or payload.get("k") != "enroll" or payload.get("u") != user_id:
        return None
    if not payload.get("s") or not isinstance(payload.get("c"), list):
        return None
    return payload
