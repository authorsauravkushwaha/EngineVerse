"""Built-in isolated runner.

Every submission runs in a brand-new OS process:

* ``unshare --net --map-root-user`` - the process gets a private network
  namespace with **no interfaces at all**, so it cannot reach the database, the
  loopback API or the internet.
* ``timeout -s KILL`` - hard wall-clock cap.
* ``ulimit`` - address space, CPU seconds, file size, open files and process
  count are all capped.
* a fresh, empty, disposable working directory
* a scrubbed environment: the child receives none of the application's secrets
* output is capped byte-wise

Interpreted languages get an explicit parse check so a syntax error is reported
as ``compile_error`` instead of a confusing runtime failure.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from ..config import get_settings
from . import RunResult

MAX_OUTPUT_BYTES = 65_536

# Each runner declares:
#   file    - source file name written into the sandbox
#   check   - optional argv that validates syntax before running
#   compile - optional argv that builds a binary
#   run     - argv that executes the program
#   vlimit  - address-space cap in KB (V8 reserves huge virtual ranges it never
#             commits, so Node gets a large -v and a real heap cap instead)
RUNNERS: dict[str, dict] = {
    "python": {
        "file": "main.py",
        "check": ["python3", "-c", "import ast,sys; ast.parse(open('main.py').read())"],
        "run": ["python3", "-I", "-B", "main.py"],
    },
    "javascript": {
        "file": "main.js",
        "check": ["node", "--check", "main.js"],
        "run": ["node", "--max-old-space-size=256", "--max-semi-space-size=8", "main.js"],
        "vlimit": 4 * 1024 * 1024,
    },
    "c": {
        "file": "main.c",
        "compile": ["gcc", "-O2", "-std=c17", "-o", "program", "main.c"],
        "run": ["./program"],
    },
    "cpp": {
        "file": "main.cpp",
        "compile": ["g++", "-O2", "-std=c++17", "-o", "program", "main.cpp"],
        "run": ["./program"],
    },
    "bash": {"file": "main.sh", "check": ["sh", "-n", "main.sh"], "run": ["sh", "main.sh"]},
    "java": {
        "file": "Main.java",
        "compile": ["javac", "-Xlint:none", "Main.java"],
        "run": ["java", "-Xss8m", "-Xmx256m", "Main"],
        "vlimit": 2 * 1024 * 1024,
    },
}

MARKER = "__EV_STEP_FAILED__"


def _quote(value: str) -> str:
    return "'" + value.replace("'", "'\\''") + "'"


def _command(argv: list[str]) -> str:
    return " ".join(_quote(part) for part in argv)


class LocalSandboxProvider:
    """Runs untrusted code in an isolated child process."""

    name = "local-sandbox"

    def __init__(self) -> None:
        self._have_namespace = shutil.which("unshare") is not None and shutil.which("timeout") is not None

    @property
    def available(self) -> bool:
        return True

    def supports(self, language: str) -> bool:
        runner = RUNNERS.get(language)
        if not runner:
            return False
        steps = [runner["run"]]
        if runner.get("compile"):
            steps.append(runner["compile"])
        if runner.get("check"):
            steps.append(runner["check"])
        for argv in steps:
            executable = argv[0]
            if executable.startswith("./"):
                continue  # produced by the compile step
            if shutil.which(executable) is None:
                return False
        return True

    def run(self, language: str, code: str, stdin: str = "", *, timeout_ms: int | None = None) -> RunResult:
        runner = RUNNERS.get(language)
        if runner is None:
            return RunResult(status="unsupported_language", stderr=f'No runner configured for "{language}".')

        settings = get_settings()
        timeout_ms = min(max(timeout_ms or settings.judge_timeout_ms, 500), 15_000)
        memory_kb = min(max(settings.judge_memory_kb, 65_536), 1_048_576)
        vlimit_kb = int(runner.get("vlimit", memory_kb))
        timeout_seconds = max(1, -(-timeout_ms // 1000))

        workdir = Path(tempfile.mkdtemp(prefix="evjudge-"))
        started = time.monotonic()
        try:
            (workdir / runner["file"]).write_text(code, encoding="utf-8")
            (workdir / "input.txt").write_text(stdin or "", encoding="utf-8")

            script = [
                f"ulimit -v {vlimit_kb} 2>/dev/null || true",
                f"ulimit -t {timeout_seconds} 2>/dev/null || true",
                "ulimit -f 8192 2>/dev/null || true",
                "ulimit -n 64 2>/dev/null || true",
                "ulimit -u 32 2>/dev/null || true",
            ]
            if runner.get("check"):
                script.append(f"{_command(runner['check'])} 2> err.txt || {{ cat err.txt >&2; echo {MARKER}CHECK; exit 65; }}")
            if runner.get("compile"):
                script.append(f"{_command(runner['compile'])} 2> err.txt || {{ cat err.txt >&2; echo {MARKER}COMPILE; exit 66; }}")
            script.append(f"exec {_command(runner['run'])} < input.txt")
            (workdir / "run.sh").write_text("\n".join(script), encoding="utf-8")

            if self._have_namespace:
                argv = [
                    "unshare", "--net", "--map-root-user", "--",
                    "timeout", "-s", "KILL", str(timeout_seconds), "sh", "run.sh",
                ]
            else:  # pragma: no cover - only when unshare/timeout are missing
                argv = ["timeout", "-s", "KILL", str(timeout_seconds), "sh", "run.sh"]

            env = {
                "PATH": "/usr/local/bin:/usr/bin:/bin",
                "HOME": str(workdir),
                "TMPDIR": str(workdir),
                "LANG": "C.UTF-8",
                "LC_ALL": "C.UTF-8",
                "PYTHONDONTWRITEBYTECODE": "1",
            }

            try:
                completed = subprocess.run(
                    argv,
                    cwd=workdir,
                    env=env,
                    input=(stdin or "")[:20_000].encode("utf-8", "replace"),
                    capture_output=True,
                    timeout=(timeout_ms + 3000) / 1000,
                )
            except subprocess.TimeoutExpired:
                return RunResult(status="timeout", stderr="Time limit exceeded.", runtime_ms=_ms(started))

            stdout = completed.stdout.decode("utf-8", "replace")[:MAX_OUTPUT_BYTES]
            stderr = completed.stderr.decode("utf-8", "replace")[:MAX_OUTPUT_BYTES]
            runtime_ms = _ms(started)
            combined = stdout + stderr

            if f"{MARKER}CHECK" in combined:
                return RunResult(status="compile_error", stderr=_clean(stderr), exit_code=completed.returncode, runtime_ms=runtime_ms)
            if f"{MARKER}COMPILE" in combined:
                return RunResult(status="compile_error", stderr=_clean(stderr), exit_code=completed.returncode, runtime_ms=runtime_ms)

            # `timeout -s KILL` surfaces as a negative return code (signal);
            # `ulimit -t` surfaces as SIGXCPU (152/153). Either way the wall
            # clock tells us the truth.
            killed = completed.returncode is not None and (completed.returncode < 0 or completed.returncode in (124, 137, 152, 153))
            if killed or runtime_ms >= timeout_ms - 50:
                return RunResult(
                    status="timeout",
                    stdout=stdout,
                    stderr=_clean(stderr) or "Time limit exceeded.",
                    exit_code=completed.returncode,
                    runtime_ms=runtime_ms,
                )
            if completed.returncode != 0:
                return RunResult(
                    status="runtime_error",
                    stdout=stdout,
                    stderr=_clean(stderr) or f"Process exited with code {completed.returncode}",
                    exit_code=completed.returncode,
                    runtime_ms=runtime_ms,
                )
            return RunResult(status="accepted", stdout=stdout, stderr=_clean(stderr), exit_code=0, runtime_ms=runtime_ms)
        except OSError as exc:  # pragma: no cover - environment failure
            return RunResult(status="internal_error", stderr=str(exc), runtime_ms=_ms(started))
        finally:
            shutil.rmtree(workdir, ignore_errors=True)


def _ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


def _clean(text: str) -> str:
    return text.replace(f"{MARKER}CHECK", "").replace(f"{MARKER}COMPILE", "").replace(MARKER, "").strip()[:MAX_OUTPUT_BYTES]


__all__ = ["LocalSandboxProvider", "RUNNERS"]
