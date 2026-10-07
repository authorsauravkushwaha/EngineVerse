"""Client for a self-hosted Judge0-compatible API."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from ..config import get_settings
from . import RunResult

LANGUAGE_IDS = {
    "python": 71, "javascript": 63, "c": 50, "cpp": 54,
    "java": 62, "bash": 46, "csharp": 51, "go": 60, "rust": 73,
    "kotlin": 78, "php": 68, "typescript": 74, "sql": 82, "ruby": 72,
}

STATUS_MAP = {
    "Accepted": "accepted",
    "Wrong Answer": "wrong_answer",
    "Time Limit Exceeded": "timeout",
    "Memory Limit Exceeded": "memory_limit",
    "Compilation Error": "compile_error",
}


class Judge0Provider:
    name = "judge0"

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.judge0_url.rstrip("/")
        self.api_key = settings.judge0_key

    @property
    def available(self) -> bool:
        return bool(self.base_url)

    def supports(self, language: str) -> bool:
        return self.available and language in LANGUAGE_IDS

    def run(self, language: str, code: str, stdin: str = "", *, timeout_ms: int | None = None) -> RunResult:
        if not self.available:
            return RunResult(status="internal_error", stderr="ENGINEVERSE_JUDGE0_URL is not configured.")
        settings = get_settings()
        timeout_ms = timeout_ms or settings.judge_timeout_ms
        body = json.dumps(
            {
                "language_id": LANGUAGE_IDS.get(language, 71),
                "source_code": code,
                "stdin": stdin or "",
                "cpu_time_limit": min(10, timeout_ms / 1000),
                "memory_limit": settings.judge_memory_kb,
            }
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(
            f"{self.base_url}/submissions?base64_encoded=false&wait=true", data=body, headers=headers, method="POST"
        )
        started = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=(timeout_ms + 8000) / 1000) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:  # pragma: no cover - network dependent
            return RunResult(status="internal_error", stderr=f"Judge0 responded {exc.code}", runtime_ms=_ms(started))
        except (urllib.error.URLError, TimeoutError) as exc:  # pragma: no cover
            return RunResult(status="internal_error", stderr=f"Judge0 unreachable: {exc}", runtime_ms=_ms(started))

        description = (payload.get("status") or {}).get("description", "")
        return RunResult(
            status=STATUS_MAP.get(description, "runtime_error"),
            stdout=(payload.get("stdout") or "")[:65_536],
            stderr=(payload.get("stderr") or payload.get("compile_output") or "")[:65_536],
            exit_code=payload.get("exit_code"),
            runtime_ms=int(float(payload.get("time") or 0) * 1000),
            memory_kb=payload.get("memory"),
        )


def _ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


__all__ = ["Judge0Provider", "LANGUAGE_IDS"]
