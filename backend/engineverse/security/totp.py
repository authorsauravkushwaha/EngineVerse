"""Time-based one-time passwords and one-time recovery codes.

The TOTP secret is sealed with the application secret before it is stored. MFA
login and enrollment challenges are random, hashed, short-lived database records
that can be consumed once; no challenge token carries the authenticator secret
or recovery codes. Rotating ``ENGINEVERSE_SECRET`` makes existing seals
unreadable. ``scripts/create_admin.py --replace`` clears the super
administrator's seal so recovery does not need the old secret.

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
import re
from urllib.parse import quote

from .. import db
from ..config import get_settings

STEP_SECONDS = 30
DIGITS = 6
_LOGIN_TTL = 300
_ENROLL_TTL = 600
_CHALLENGE_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{43}$")


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


def matching_counter(
    secret: str, code: str, *, now: float | None = None, window: int = 1,
) -> int | None:
    """Return the matching time-step, allowing the small clock skew window.

    Callers persist this counter with the sealed factor. Returning ``None`` for
    any previously accepted counter prevents a valid TOTP from being replayed
    inside its 30-second validity period.
    """
    if not isinstance(code, str) or not isinstance(secret, str) or not secret:
        return None
    digits = "".join(ch for ch in code if ch in "0123456789")
    if len(digits) != DIGITS:
        return None
    moment = time.time() if now is None else now
    if not isinstance(moment, (int, float)) or moment < 0:
        return None
    current = int(moment // STEP_SECONDS)
    skew = max(0, min(2, int(window)))
    matches: list[int] = []
    for counter in range(max(0, current - skew), current + skew + 1):
        try:
            candidate = code_at(secret, counter)
        except (ValueError, TypeError, struct.error):
            return None
        if hmac.compare_digest(candidate, digits):
            matches.append(counter)
    # A six-digit collision across adjacent counters is rare, but choosing the
    # newest match avoids moving a user's recorded counter backwards.
    return max(matches) if matches else None


def verify_totp(secret: str, code: str, *, now: float | None = None, window: int = 1) -> bool:
    return matching_counter(secret, code, now=now, window=window) is not None


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
    if not isinstance(code, str) or len(code) > 128:
        return ""
    compact = "".join(ch for ch in code.lower() if ch in "0123456789abcdef")
    return hashlib.sha256(compact.encode("ascii")).hexdigest()


def _seal_key() -> bytes:
    return hashlib.sha256(get_settings().effective_secret() + b"engineverse-totp-seal").digest()


def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    blocks = []
    counter = 0
    written = 0
    while written < length:
        block = hmac.new(key, nonce + counter.to_bytes(4, "big"), hashlib.sha256).digest()
        blocks.append(block)
        written += len(block)
        counter += 1
    return b"".join(blocks)[:length]


def seal(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    nonce = secrets.token_bytes(16)
    cipher = bytes(a ^ b for a, b in zip(raw, _keystream(_seal_key(), nonce, len(raw))))
    mac = hmac.new(_seal_key(), nonce + cipher, hashlib.sha256).digest()
    return "v1:" + base64.urlsafe_b64encode(nonce + mac + cipher).decode("ascii")


def unseal(stored: str) -> dict | None:
    if not isinstance(stored, str) or len(stored) > 4096 or not stored.startswith("v1:"):
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


def pack(secret: str, codes: list[str], *, last_counter: int | None = None) -> str:
    """Seal a factor, its recovery-code hashes and the last accepted TOTP step."""
    return seal({
        "secret": secret,
        "recovery": [_hash_code(code) for code in codes[:16]],
        "last_counter": last_counter,
    })


def verify_factor(stored: str, code: str) -> tuple[bool, str | None]:
    """Check a TOTP or recovery code and return an updated seal on success.

    The replacement seal stores the accepted TOTP counter or removes the
    consumed recovery hash. Persist the replacement with a compare-and-set
    against the previously read seal so concurrent requests cannot both win.
    """
    payload = unseal(stored)
    if not payload or not isinstance(payload.get("secret"), str):
        return False, None
    counter = matching_counter(payload["secret"], code)
    if counter is not None:
        last_counter = payload.get("last_counter")
        try:
            last_counter = int(last_counter) if last_counter is not None else -1
        except (ValueError, TypeError, OverflowError):
            return False, None
        if counter <= last_counter:
            return False, None
        payload["last_counter"] = counter
        return True, seal(payload)

    recovery = payload.get("recovery")
    if not isinstance(recovery, list) or len(recovery) > 16:
        return False, None
    submitted = _hash_code(code)
    if not submitted:
        return False, None
    remaining = []
    matched = False
    for hashed in recovery:
        if not matched and isinstance(hashed, str) and hmac.compare_digest(hashed, submitted):
            matched = True
            continue
        remaining.append(hashed)
    if not matched:
        return False, None
    payload["recovery"] = remaining
    return True, seal(payload)


def _challenge_hash(token: str) -> str:
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def new_challenge(user_id: str, purpose: str, ttl_seconds: int, payload: str | None = None) -> str:
    """Keep at most one challenge row per account and purpose.

    Replacing the previous token bounds storage if a user starts MFA repeatedly
    and makes older browser prompts invalid immediately. Lock the user row on
    PostgreSQL so concurrent requests cannot leave multiple live challenges.
    """
    token = secrets.token_urlsafe(32)
    now = int(time.time() * 1000)
    lock = " FOR UPDATE" if db.uses_postgres() else ""
    with db.transaction():
        db.query_one("SELECT id FROM users WHERE id = ?" + lock, user_id)
        db.execute("DELETE FROM security_challenges WHERE expires_at < ?", now)
        db.execute(
            "DELETE FROM security_challenges WHERE user_id = ? AND purpose = ?",
            user_id, purpose,
        )
        db.execute(
            "INSERT INTO security_challenges "
            "(token_hash,user_id,purpose,payload,created_at,expires_at) VALUES (?,?,?,?,?,?)",
            _challenge_hash(token), user_id, purpose, payload, now, now + ttl_seconds * 1000,
        )
    return token


def active_challenge(token: str, purpose: str, user_id: str | None = None) -> dict | None:
    if not isinstance(token, str) or not _CHALLENGE_TOKEN_RE.fullmatch(token):
        return None
    now = int(time.time() * 1000)
    sql = (
        "SELECT token_hash,user_id,purpose,payload,expires_at FROM security_challenges "
        "WHERE token_hash = ? AND purpose = ? AND consumed_at IS NULL AND expires_at >= ?"
    )
    args: list = [_challenge_hash(token), purpose, now]
    if user_id is not None:
        sql += " AND user_id = ?"
        args.append(user_id)
    return db.query_one(sql, *args)


def consume_challenge(token: str, purpose: str, user_id: str) -> bool:
    if not isinstance(token, str) or not _CHALLENGE_TOKEN_RE.fullmatch(token):
        return False
    now = int(time.time() * 1000)
    changed = db.execute(
        "UPDATE security_challenges SET consumed_at = ? "
        "WHERE token_hash = ? AND user_id = ? AND purpose = ? "
        "AND consumed_at IS NULL AND expires_at >= ?",
        now, _challenge_hash(token), user_id, purpose, now,
    )
    return changed == 1


def issue_login_token(user_id: str) -> str:
    """Create a 5-minute MFA challenge whose database hash can be used once."""
    return new_challenge(user_id, "mfa_login", _LOGIN_TTL)


def read_login_token(token: str) -> str | None:
    row = active_challenge(token, "mfa_login")
    return str(row["user_id"]) if row else None


def consume_login_token(token: str, user_id: str) -> bool:
    return consume_challenge(token, "mfa_login", user_id)


def issue_enroll_token(user_id: str, secret: str, codes: list[str]) -> str:
    """Create a 10-minute enrollment challenge; sensitive state stays sealed."""
    payload = seal({"secret": secret, "codes": codes[:16]})
    return new_challenge(user_id, "mfa_enroll", _ENROLL_TTL, payload)


def read_enroll_token(token: str, user_id: str) -> dict | None:
    row = active_challenge(token, "mfa_enroll", user_id)
    if not row or not row.get("payload"):
        return None
    payload = unseal(row["payload"])
    if not payload or not isinstance(payload.get("secret"), str):
        return None
    codes = payload.get("codes")
    if not isinstance(codes, list) or len(codes) > 16 or not all(isinstance(code, str) for code in codes):
        return None
    return {"s": payload["secret"], "c": codes}


def consume_enroll_token(token: str, user_id: str) -> bool:
    return consume_challenge(token, "mfa_enroll", user_id)


def update_challenge_payload(
    token: str,
    purpose: str,
    user_id: str,
    payload: str,
    *,
    expected_payload: str | None = None,
) -> bool:
    """Replace the sealed payload of one live challenge.

    OTP attempt counters live in the sealed payload. Keeping this update
    conditional on the same live row (and, when supplied, the payload that was
    read) prevents a late request from changing a challenge that another
    request already consumed or replaced.
    """
    if not isinstance(token, str) or not _CHALLENGE_TOKEN_RE.fullmatch(token):
        return False
    if not isinstance(payload, str) or len(payload) > 4096:
        return False
    now = int(time.time() * 1000)
    sql = (
        "UPDATE security_challenges SET payload = ? WHERE token_hash = ? "
        "AND user_id = ? AND purpose = ? AND consumed_at IS NULL AND expires_at >= ?"
    )
    args: list = [payload, _challenge_hash(token), user_id, purpose, now]
    if expected_payload is not None:
        sql += " AND payload = ?"
        args.append(expected_payload)
    return db.execute(sql, *args) == 1


# Compatibility aliases for callers written against the original private
# helpers. New code should use the public names above.
def _new_challenge(user_id: str, purpose: str, ttl_seconds: int, payload: str | None = None) -> str:
    return new_challenge(user_id, purpose, ttl_seconds, payload)


def _active_challenge(token: str, purpose: str, user_id: str | None = None) -> dict | None:
    return active_challenge(token, purpose, user_id)


def _consume_challenge(token: str, purpose: str, user_id: str) -> bool:
    return consume_challenge(token, purpose, user_id)
