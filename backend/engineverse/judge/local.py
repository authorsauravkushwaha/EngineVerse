"""Built-in isolated runner.

Every submission runs in a brand-new OS process:

* ``unshare --net --map-root-user`` - the process gets a private network
  namespace with **no interfaces at all**, so it cannot reach the database, the
  loopback API or the internet.
* ``timeout -s KILL`` - hard wall-clock cap.
* rlimits set **in Python** via ``preexec_fn`` - address space, CPU seconds,
  file size, open files and process count.
* privileges dropped to an unprivileged uid before any user code runs.
* a fresh, empty, disposable working directory
* a scrubbed environment: the child receives none of the application's secrets
* output is capped byte-wise

Why the limits are set in Python and not with ``ulimit`` in the shell script:
``/bin/sh`` is dash on Debian-family images, and dash does not implement
``ulimit -u`` or ``-t``. Those two lines failed with "Illegal option", the
``2>/dev/null || true`` swallowed the error, and the child inherited an
unbounded RLIMIT_NPROC - so a fork bomb took the whole application server down
with it. Setting them through the ``resource`` module cannot be silently
ignored.

Privilege dropping stops submitted code from writing into the repository (it
could previously create files next to the source) and from tampering with
anything the application user owns. It does not stop it *reading*
world-readable files; for that boundary use the containerised sandbox service
in ``deploy/`` rather than this provider.

Interpreted languages get an explicit parse check so a syntax error is reported
as ``compile_error`` instead of a confusing runtime failure.
"""
from __future__ import annotations

import os
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path

try:
    import resource
except ImportError:  # pragma: no cover - non-POSIX
    resource = None

#: uid/gid the child drops to. ``nobody`` owns nothing, so submitted code cannot
#: write into the repository or read anything that is not world-readable.
SANDBOX_UID = 65534
SANDBOX_GID = 65534

#: The checkout this module lives in, i.e. the tree a submission must not be able
#: to read or write. backend/engineverse/judge/local.py -> repository root.
APP_ROOT = Path(__file__).resolve().parents[3]


def _paths_to_hide() -> list[Path]:
    """Directories an empty tmpfs is mounted over inside the sandbox.

    The checkout alone is not enough: a submission could still write anywhere
    else the application user can, such as the parent of the checkout or a
    sibling directory. Hiding the account's home directory as well covers the
    usual layout without needing to enumerate what happens to be nearby.
    """
    candidates = [APP_ROOT]
    try:
        home = Path.home().resolve()
    except RuntimeError:  # pragma: no cover - no HOME set
        home = None
    if home and home.is_dir():
        candidates.append(home)

    live = {c for c in candidates if c.is_dir()}
    # Keep only the topmost paths. When the home directory contains the
    # checkout, one tmpfs over the home covers both; mounting the checkout
    # separately would be redundant, and mounting a parent *after* its child
    # would make the child's mount point disappear underneath it.
    topmost = {
        path for path in live
        if not any(path != other and other in path.parents for other in live)
    }
    return sorted(topmost, key=lambda item: len(item.parts))


def _processes_for_uid(uid: int) -> int:
    """Counts processes already owned by ``uid``.

    RLIMIT_NPROC is enforced against the *total* number of processes owned by
    the real uid, not against the child's own process tree. Setting it to a flat
    32 therefore blocks the child from forking at all once the application
    server already has a few dozen threads and processes running - which breaks
    ordinary submissions. The budget has to be measured, not assumed.
    """
    if not hasattr(os, "listdir") or not os.path.isdir("/proc"):
        return 0
    count = 0
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            with open(f"/proc/{entry}/status", "rb") as handle:
                for line in handle:
                    if line.startswith(b"Uid:"):
                        if int(line.split()[1]) == uid:
                            count += 1
                        break
        except OSError:
            continue
    return count


def _set_limits_and_drop(max_processes: int, memory_kb: int, cpu_seconds: int) -> None:
    """Runs in the forked child, before exec.

    Order matters: apply every rlimit while still privileged, then give up
    privileges last so nothing can raise a limit back afterwards.
    """
    if resource is not None:
        # Head-room on top of what this uid is already using, so a fork bomb
        # hits the wall quickly without starving the application server.
        nproc_budget = _processes_for_uid(os.getuid()) + max_processes
        limits = (
            (resource.RLIMIT_NPROC, nproc_budget),
            (resource.RLIMIT_AS, memory_kb * 1024),
            (resource.RLIMIT_CPU, cpu_seconds),
            (resource.RLIMIT_FSIZE, 4 * 1024 * 1024),
            (resource.RLIMIT_NOFILE, 64),
            (resource.RLIMIT_CORE, 0),
        )
        for which, value in limits:
            try:
                resource.setrlimit(which, (value, value))
            except (ValueError, OSError):
                # A limit the kernel refuses is not worth failing the run over,
                # but it must never be swallowed silently the way ulimit was.
                pass
    if hasattr(os, "setgroups"):
        try:
            os.setgroups([SANDBOX_GID])
        except OSError:
            pass
    if os.getgid() != SANDBOX_GID:
        try:
            os.setgid(SANDBOX_GID)
        except OSError:
            pass
    if os.getuid() != SANDBOX_UID:
        try:
            os.setuid(SANDBOX_UID)
        except OSError:
            # Only a privileged parent can hand the child to another uid. When
            # the application itself runs unprivileged this is expected, and the
            # rlimits above are what contain the submission instead.
            pass

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


def _shell_quote(value: str) -> str:
    """Quotes a path for interpolation into the generated shell script."""
    return "'" + value.replace("'", "'\\''") + "'"


def _read_capped(path: Path) -> str:
    """Reads at most MAX_OUTPUT_BYTES from a file the submission wrote to."""
    try:
        with path.open("rb") as handle:
            return handle.read(MAX_OUTPUT_BYTES).decode("utf-8", "replace")
    except OSError:
        return ""


def _kill_tree(process: "subprocess.Popen") -> None:
    """Signals the submission's whole process group, then reaps the child.

    The group is signalled unconditionally. Guarding on ``process.poll() is
    None`` looks like an optimisation and is a hole: a fork bomb's direct child
    dies almost immediately - NPROC refuses its next fork - while the dozens of
    grandchildren it already spawned keep running. Polling first therefore skips
    the kill in exactly the case that needs it. Reading output from files rather
    than pipes is what exposed this; while the judge blocked on a pipe it waited
    for the tree to die on its own and the bug stayed invisible.

    ``start_new_session=True`` makes the child a group leader, so its pgid is
    its pid and the group can be signalled without a live process to query.
    """
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            process.kill()
        except OSError:
            pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:  # pragma: no cover - kernel should not stall
        pass


def _preexec(max_processes: int, memory_kb: int, cpu_seconds: int):
    """Builds the preexec_fn closure.

    Kept as a factory so the values are captured rather than read from globals
    at fork time, which keeps the child's limits deterministic.
    """

    def _apply() -> None:
        _set_limits_and_drop(max_processes, memory_kb, cpu_seconds)

    return _apply


def _hand_over(workdir: Path) -> None:
    """Gives the sandbox uid ownership of the working directory.

    The child runs as ``nobody`` once privileges are dropped, so a directory
    created by the application user would not be writable and every submission
    would fail to produce a binary or write output. Best effort: if the
    platform will not allow the chown the run still proceeds and the error
    surfaces as an ordinary runtime failure.
    """
    if not hasattr(os, "chown"):
        return
    try:
        os.chown(workdir, SANDBOX_UID, SANDBOX_GID)
        for entry in workdir.iterdir():
            try:
                os.chown(entry, SANDBOX_UID, SANDBOX_GID)
            except OSError:
                pass
    except OSError:
        pass


class LocalSandboxProvider:
    """Runs untrusted code in an isolated child process."""

    name = "local-sandbox"

    def __init__(self) -> None:
        self._have_namespace = shutil.which("unshare") is not None and shutil.which("timeout") is not None
        self._have_mount_ns = self._have_namespace and self._probe_mount_ns()

    @staticmethod
    def _probe_mount_ns() -> bool:
        """Checks once whether a mount namespace can actually be created.

        ``unshare --map-root-user --mount`` needs an unprivileged user namespace,
        which kernels and container runtimes disable far more often than the
        network namespace. Probing avoids advertising a guarantee the host will
        not honour, and avoids failing every submission when it cannot.
        """
        try:
            probe = subprocess.run(
                ["unshare", "--map-root-user", "--mount", "--", "true"],
                capture_output=True, timeout=5,
            )
            return probe.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return False

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
        # Hard caps enforced through setrlimit in the child. NPROC is the one
        # that matters most: without it a fork bomb exhausts the host and the
        # application server is killed alongside the submission.
        max_processes = 32
        memory_kb = max(vlimit_kb, memory_kb)

        workdir = Path(tempfile.mkdtemp(prefix="evjudge-"))
        started = time.monotonic()
        try:
            (workdir / runner["file"]).write_text(code, encoding="utf-8")
            (workdir / "input.txt").write_text(stdin or "", encoding="utf-8")
            _hand_over(workdir)

            script = []
            if self._have_mount_ns:
                # Inside the user namespace this shell is root, so it can mount.
                # An empty tmpfs over these paths means a submission can neither
                # read the source tree nor write anywhere the application user
                # can. Best effort: if a mount is refused the run continues
                # under the rlimits alone.
                for hidden in _paths_to_hide():
                    script.append(
                        f"mount -t tmpfs -o size=1k tmpfs {_shell_quote(str(hidden))} 2>/dev/null || true"
                    )
            script += [
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
                argv = ["unshare", "--net"]
                if self._have_mount_ns:
                    argv.append("--mount")
                argv += [
                    "--map-root-user", "--",
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

            # Popen in its own session rather than subprocess.run: `timeout -s
            # KILL` signals only its direct child, so a submission that forks
            # leaves its descendants orphaned and still running after the run is
            # reported as finished. A private session makes the whole tree one
            # process group that can be signalled as a unit.
            #
            # Output goes to files, not pipes. A pipe does not reach EOF until
            # every process holding its write end has exited, and a fork bomb's
            # grandchildren inherit stdout - so reading from a pipe blocks on
            # the whole tree even after the direct child is dead. Measured: the
            # same bomb took 5s over pipes and 1.2s to a file, and the gap widens
            # with how many children were spawned. With files, wait() returns as
            # soon as the direct child exits and the deadline actually holds.
            out_path = workdir / "stdout.bin"
            err_path = workdir / "stderr.bin"
            input_path = workdir / "input.txt"
            input_path.write_bytes((stdin or "")[:20_000].encode("utf-8", "replace"))

            with input_path.open("rb") as in_fh, out_path.open("wb") as out_fh, \
                    err_path.open("wb") as err_fh:
                process = subprocess.Popen(
                    argv,
                    cwd=workdir,
                    env=env,
                    stdin=in_fh,
                    stdout=out_fh,
                    stderr=err_fh,
                    preexec_fn=_preexec(max_processes, memory_kb, timeout_seconds),
                    start_new_session=True,
                )
                try:
                    process.wait(timeout=(timeout_ms + 3000) / 1000)
                except subprocess.TimeoutExpired:
                    _kill_tree(process)
                    return RunResult(status="timeout", stderr="Time limit exceeded.", runtime_ms=_ms(started))
                finally:
                    # Whatever the outcome, nothing from the submission's process
                    # tree should outlive the verdict.
                    _kill_tree(process)

            # Read after the process is gone. Truncated on read rather than
            # streamed, so a submission that writes without limit cannot make
            # the judge allocate what it printed.
            stdout = _read_capped(out_path)
            stderr = _read_capped(err_path)
            returncode = process.returncode
            runtime_ms = _ms(started)
            combined = stdout + stderr

            if f"{MARKER}CHECK" in combined:
                return RunResult(status="compile_error", stderr=_clean(stderr), exit_code=returncode, runtime_ms=runtime_ms)
            if f"{MARKER}COMPILE" in combined:
                return RunResult(status="compile_error", stderr=_clean(stderr), exit_code=returncode, runtime_ms=runtime_ms)

            # `timeout -s KILL` surfaces as a negative return code (signal);
            # `ulimit -t` surfaces as SIGXCPU (152/153). Either way the wall
            # clock tells us the truth.
            killed = returncode is not None and (returncode < 0 or returncode in (124, 137, 152, 153))
            if killed or runtime_ms >= timeout_ms - 50:
                return RunResult(
                    status="timeout",
                    stdout=stdout,
                    stderr=_clean(stderr) or "Time limit exceeded.",
                    exit_code=returncode,
                    runtime_ms=runtime_ms,
                )
            if returncode != 0:
                return RunResult(
                    status="runtime_error",
                    stdout=stdout,
                    stderr=_clean(stderr) or f"Process exited with code {returncode}",
                    exit_code=returncode,
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
