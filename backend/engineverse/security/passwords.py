"""Password hashing and policy.

Algorithm: **scrypt** (RFC 7914) - memory-hard, so GPU/ASIC brute force is
expensive. Parameters live inside the stored hash, so costs can be raised later
and existing hashes keep verifying (they are transparently upgraded on the next
successful login). No credentials ever leave this server.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import unicodedata
from dataclasses import dataclass

# Current cost. Raise over time; older hashes still verify.
N = 1 << 14  # 16384
R = 8
P = 1
KEY_LENGTH = 64
PREFIX = "scrypt"
MAX_PASSWORD_LENGTH = 256

COMMON_PASSWORDS = {
    "password", "password1", "password123", "123456", "12345678", "123456789",
    "qwerty", "qwerty123", "letmein", "welcome", "admin", "iloveyou",
    "engineer", "engineering", "engineverse", "monkey", "dragon", "abc123",
    "qwertyuiop", "1q2w3e4r", "sunshine", "princess",
}


@dataclass(frozen=True)
class ParsedHash:
    n: int
    r: int
    p: int
    salt: bytes
    digest: bytes


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(
        _normalise(password), salt=salt, n=N, r=R, p=P, dklen=KEY_LENGTH, maxmem=256 * 1024 * 1024
    )
    return "$".join(
        [PREFIX, str(N), str(R), str(P), base64.b64encode(salt).decode(), base64.b64encode(digest).decode()]
    )


def parse_hash(stored: str) -> ParsedHash | None:
    parts = stored.split("$")
    if len(parts) != 6 or parts[0] != PREFIX:
        return None
    try:
        n, r, p = int(parts[1]), int(parts[2]), int(parts[3])
        salt = base64.b64decode(parts[4])
        digest = base64.b64decode(parts[5])
    except (ValueError, TypeError):
        return None
    if n <= 0 or (n & (n - 1)) != 0 or r <= 0 or p <= 0 or not salt or not digest:
        return None
    return ParsedHash(n=n, r=r, p=p, salt=salt, digest=digest)


def verify_password(password: str, stored: str) -> bool:
    """Constant-time verification. Always does work, even for bad input."""
    parsed = parse_hash(stored)
    if parsed is None:
        # Burn comparable time so timing cannot reveal hash validity.
        hashlib.scrypt(b"x", salt=b"0" * 16, n=N, r=R, p=P, dklen=KEY_LENGTH, maxmem=256 * 1024 * 1024)
        return False
    if len(password) > MAX_PASSWORD_LENGTH:
        return False
    try:
        digest = hashlib.scrypt(
            _normalise(password),
            salt=parsed.salt,
            n=parsed.n,
            r=parsed.r,
            p=parsed.p,
            dklen=len(parsed.digest),
            maxmem=256 * 1024 * 1024,
        )
    except (ValueError, OverflowError):
        return False
    return hmac.compare_digest(digest, parsed.digest)


def needs_rehash(stored: str) -> bool:
    parsed = parse_hash(stored)
    if parsed is None:
        return True
    return (parsed.n, parsed.r, parsed.p) != (N, R, P)


def _normalise(password: str) -> bytes:
    """NFKC normalisation stops two visually identical passwords differing."""
    return unicodedata.normalize("NFKC", password).encode("utf-8")


@dataclass(frozen=True)
class PasswordIssue:
    code: str
    message: str


def check_password_strength(password: str, context: list[str] | None = None) -> list[PasswordIssue]:
    """Length-first policy (NIST SP 800-63B), with identity checks."""
    issues: list[PasswordIssue] = []
    if len(password) < 10:
        issues.append(PasswordIssue("too_short", "Use at least 10 characters."))
    if len(password) > MAX_PASSWORD_LENGTH:
        issues.append(PasswordIssue("too_long", "Use at most 256 characters."))
    if 10 <= len(password) < 16:
        classes = sum(
            1
            for pattern in (r"[a-z]", r"[A-Z]", r"\d", r"[^A-Za-z0-9]")
            if re.search(pattern, password)
        )
        if classes < 3:
            issues.append(PasswordIssue("weak_mix", "Mix upper case, lower case, numbers and symbols."))
    lowered = password.lower()
    if lowered in COMMON_PASSWORDS:
        issues.append(PasswordIssue("common", "That password is too common to be safe."))
    for word in context or []:
        clean = (word or "").strip().lower()
        if len(clean) >= 4 and clean in lowered:
            issues.append(PasswordIssue("contains_identity", "Do not use your name, username or email in the password."))
            break
    if re.search(r"(.)\1{4,}", password):
        issues.append(PasswordIssue("repeats", "Avoid long runs of the same character."))
    return issues


def password_score(password: str) -> int:
    score = min(len(password) * 4, 60)
    if re.search(r"[a-z]", password) and re.search(r"[A-Z]", password):
        score += 10
    if re.search(r"\d", password):
        score += 10
    if re.search(r"[^A-Za-z0-9]", password):
        score += 15
    if password.lower() in COMMON_PASSWORDS:
        return 0
    return max(0, min(100, score))
