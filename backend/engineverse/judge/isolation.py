"""Canary for a Judge0-compatible host.

This does not certify isolation. A missing URL, an unreachable host, or a
canary that prints the application secret is recorded as not isolated. A
canary that holds still does not become a statement that the host is a
separate machine. The sentence is what operators should repeat.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

CANARY = """\
import os
print("CANARY_OK")
secret = os.environ.get("ENGINEVERSE_SECRET", "")
print("SECRET:" + ("present" if secret else "absent"))
try:
    open("/etc/passwd", "r").read(20)
    print("PASSWD:readable")
except Exception:
    print("PASSWD:blocked")
"""


def _post(url: str, api_key: str, timeout: float) -> tuple[int, str]:
    body = json.dumps({
        "language_id": 71,
        "source_code": CANARY,
        "stdin": "",
        "cpu_time_limit": 2,
        "memory_limit": 64000,
    }).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(
        f"{url.rstrip('/')}/submissions?base64_encoded=false&wait=true",
        data=body,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        return exc.code, raw


def probe(url: str, api_key: str = "", *, timeout: float = 8.0) -> dict:
    """Run the canary. Never reports a certification.

    The returned ``isolated`` field is always false. ``canary_held`` is true
    only when the marker printed, the secret did not, and ``/etc/passwd`` was
    not readable. That is a negative result, not a proof.
    """
    result = {
        "configured": bool((url or "").strip()),
        "reachable": False,
        "canary_held": False,
        "secret_leaked": False,
        "host_file_readable": False,
        "isolated": False,
        "sentence": "Judge0 is not configured. Isolation is not established.",
    }
    if not result["configured"]:
        return result
    try:
        status, raw = _post(url, api_key, timeout)
    except (urllib.error.URLError, TimeoutError, OSError):
        result["sentence"] = "Judge0 did not answer. Isolation is not established."
        return result
    result["reachable"] = 200 <= status < 300
    if not result["reachable"]:
        result["sentence"] = f"Judge0 answered {status}. Isolation is not established."
        return result
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        result["sentence"] = "Judge0 answered with a body that was not JSON. Isolation is not established."
        return result
    stdout = payload.get("stdout") or ""
    if "SECRET:present" in stdout or "ENGINEVERSE_SECRET" in stdout:
        result["secret_leaked"] = True
    if "PASSWD:readable" in stdout:
        result["host_file_readable"] = True
    result["canary_held"] = (
        "CANARY_OK" in stdout and not result["secret_leaked"] and not result["host_file_readable"]
    )
    if result["secret_leaked"]:
        result["sentence"] = "The canary printed the application secret. Do not call this host isolated."
    elif result["host_file_readable"]:
        result["sentence"] = "The canary read a host file. Do not call this host isolated."
    elif result["canary_held"]:
        result["sentence"] = (
            "The canary held: the secret was absent and /etc/passwd was not readable. "
            "That is not a certification that the host is isolated."
        )
    else:
        result["sentence"] = "The canary did not complete. Isolation is not established."
    return result
