"""Bridge to the Java sandbox service (``sandbox-java/``).

The Java sandbox is a separate JVM that runs one submission per process with
its own security policy. This bridge only starts that process and reads back a
JSON verdict - the web server itself never loads or executes user classes.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from ..config import REPO_ROOT, get_settings
from . import RunResult


def _java_binary() -> str | None:
    settings = get_settings()
    if settings.java_home:
        candidate = Path(settings.java_home) / "bin" / "java"
        if candidate.exists():
            return str(candidate)
    found = shutil.which("java")
    if found:
        return found
    bundled = REPO_ROOT / ".toolchain" / "jdk21" / "bin" / "java"
    return str(bundled) if bundled.exists() else None


def _jar_path() -> Path:
    settings = get_settings()
    path = Path(settings.java_sandbox_jar)
    return path if path.is_absolute() else (REPO_ROOT / path).resolve()


class JavaSandboxProvider:
    """Runs submissions through the Java sandbox service."""

    name = "java-sandbox"
    LANGUAGES = ("java", "python", "javascript", "c", "cpp", "bash")

    def __init__(self) -> None:
        self.java = _java_binary()
        self.jar = _jar_path()

    @property
    def available(self) -> bool:
        return self.java is not None and self.jar.exists()

    def supports(self, language: str) -> bool:
        return self.available and language in self.LANGUAGES

    def run(self, language: str, code: str, stdin: str = "", *, timeout_ms: int | None = None) -> RunResult:
        if not self.available:
            return RunResult(
                status="internal_error",
                stderr="Java sandbox unavailable: install a JDK and build sandbox-java (mvn -q package).",
            )
        settings = get_settings()
        timeout_ms = min(max(timeout_ms or settings.judge_timeout_ms, 500), 20_000)

        payload = json.dumps(
            {
                "language": language,
                "code": code,
                "stdin": stdin or "",
                "timeoutMs": timeout_ms,
                "memoryKb": settings.judge_memory_kb,
            }
        )
        started = time.monotonic()
        env = dict(os.environ)
        env.pop("ENGINEVERSE_SECRET", None)
        env.pop("ENGINEVERSE_DB_URL", None)
        env.pop("ENGINEVERSE_DB_PATH", None)
        try:
            completed = subprocess.run(
                [self.java, "-Xmx256m", "-Xss8m", "-jar", str(self.jar)],
                input=payload.encode("utf-8"),
                capture_output=True,
                timeout=(timeout_ms + 8000) / 1000,
                env=env,
            )
        except subprocess.TimeoutExpired:
            return RunResult(status="timeout", stderr="Java sandbox timed out.", runtime_ms=_ms(started))
        except OSError as exc:  # pragma: no cover
            return RunResult(status="internal_error", stderr=str(exc), runtime_ms=_ms(started))

        raw = completed.stdout.decode("utf-8", "replace").strip()
        try:
            verdict = json.loads(raw.splitlines()[-1]) if raw else {}
        except json.JSONDecodeError:
            return RunResult(
                status="internal_error",
                stderr=(completed.stderr.decode("utf-8", "replace") or raw)[:4000],
                runtime_ms=_ms(started),
            )
        return RunResult(
            status=verdict.get("status", "internal_error"),
            stdout=verdict.get("stdout", "")[:65_536],
            stderr=verdict.get("stderr", "")[:65_536],
            exit_code=verdict.get("exitCode"),
            runtime_ms=int(verdict.get("runtimeMs") or _ms(started)),
            memory_kb=verdict.get("memoryKb"),
        )


def _ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


__all__ = ["JavaSandboxProvider"]
