"""Code execution facade (spec §17, §71).

The web server NEVER interprets user code in-process. Three interchangeable
providers exist and are selected by ``ENGINEVERSE_JUDGE``:

``java``    the Java sandbox service in ``sandbox-java/`` (a separate JVM
            process per submission, with a SecurityManager-style policy,
            thread/CPU/memory caps and no network).
``python``  the built-in runner: a fresh OS process per submission inside a
            new network+user namespace (``unshare -rn``), with rlimits and a
            wall-clock kill.
``judge0``  forwards to a self-hosted Judge0 API.
``auto``    Java sandbox when a JDK+jar are present, otherwise the built-in
            runner.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from ..config import get_settings

MAX_OUTPUT = 65_536

# Every language the platform offers. Whether one is actually runnable depends on
# the host toolchain; `runnable_languages()` answers that at runtime.
KNOWN_LANGUAGES = ("python", "javascript", "java", "cpp", "c", "bash", "ruby")

STATUSES = (
    "accepted", "wrong_answer", "runtime_error", "timeout",
    "compile_error", "memory_limit", "unsupported_language", "internal_error",
)


@dataclass
class RunResult:
    status: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    runtime_ms: int = 0
    memory_kb: int | None = None


@dataclass
class CaseOutcome:
    id: str
    input: str
    expected: str
    actual: str
    passed: bool
    runtime_ms: int
    is_sample: bool = False
    explanation: str | None = None


@dataclass
class Evaluation:
    status: str
    passed: int = 0
    total: int = 0
    runtime_ms: int = 0
    memory_kb: int | None = None
    stderr: str = ""
    cases: list[CaseOutcome] = field(default_factory=list)


class Provider(Protocol):
    name: str

    def supports(self, language: str) -> bool: ...

    def run(self, language: str, code: str, stdin: str = "", *, timeout_ms: int | None = None) -> RunResult: ...


_provider: Provider | None = None


def resolve_provider() -> Provider:
    """Picks a provider, caching the decision for the process lifetime."""
    global _provider
    if _provider is not None:
        return _provider
    settings = get_settings()
    choice = settings.judge
    if choice == "judge0":
        from .judge0 import Judge0Provider

        _provider = Judge0Provider()
    elif choice == "java":
        from .java_bridge import JavaSandboxProvider

        _provider = JavaSandboxProvider()
    elif choice == "python":
        from .local import LocalSandboxProvider

        _provider = LocalSandboxProvider()
    else:  # auto
        from .java_bridge import JavaSandboxProvider
        from .local import LocalSandboxProvider

        java = JavaSandboxProvider()
        _provider = java if java.available else LocalSandboxProvider()
    return _provider


def reset_provider() -> None:
    global _provider
    _provider = None


def provider_info() -> dict:
    """Describes the active provider, including what it actually isolates.

    Reporting only the name invites an operator to assume a hard boundary. The
    containment flags come from the provider itself so they reflect the host
    rather than what the code hopes for - a kernel with unprivileged user
    namespaces disabled simply reports fewer guarantees.
    """
    provider = resolve_provider()
    info: dict = {"name": provider.name, "available": getattr(provider, "available", True)}
    for flag in ("_have_namespace", "_have_mount_ns"):
        if hasattr(provider, flag):
            info[flag.lstrip("_")] = bool(getattr(provider, flag))
    if hasattr(provider, "_have_namespace"):
        info["network_isolated"] = bool(provider._have_namespace)
        info["filesystem_isolated"] = bool(getattr(provider, "_have_mount_ns", False))
    return info


def runnable_languages() -> list[str]:
    """Languages the active provider can actually execute right now.

    The UI uses this to disable (never silently accept) languages whose toolchain
    is missing on this host, so a student is never told their Java submission was
    "submitted" when no JVM exists.
    """
    provider = resolve_provider()
    return [lang for lang in KNOWN_LANGUAGES if provider.supports(lang)]


def as_dict(result) -> dict:
    """Serialises a RunResult or Evaluation (and its nested cases) for JSON."""
    from dataclasses import asdict, is_dataclass

    if not is_dataclass(result):
        return dict(result)
    payload = asdict(result)
    if "cases" in payload:
        payload["cases"] = [asdict(case) if is_dataclass(case) else dict(case) for case in result.cases]
    return payload


def run_custom(language: str, code: str, stdin: str = "") -> RunResult:
    provider = resolve_provider()
    if not provider.supports(language):
        return RunResult(
            status="unsupported_language",
            stderr=f'"{language}" is not available on the {provider.name} runner.',
        )
    return provider.run(language, code, stdin)


def normalise_output(value: str) -> str:
    """Trailing-whitespace/newline insensitive comparison form."""
    lines = (value or "").replace("\r\n", "\n").split("\n")
    return "\n".join(line.rstrip() for line in lines).rstrip("\n")


def outputs_match(actual: str, expected: str) -> bool:
    return normalise_output(actual) == normalise_output(expected)


def evaluate(language: str, code: str, cases: list[dict], *, stop_on_compile_error: bool = True) -> Evaluation:
    """Runs the submission against every test case."""
    provider = resolve_provider()
    if not provider.supports(language):
        probe = provider.run(language, "", "")
        return Evaluation(
            status=probe.status if probe.status in ("unsupported_language", "internal_error") else "internal_error",
            total=len(cases),
            stderr=probe.stderr,
        )

    outcomes: list[CaseOutcome] = []
    total_ms = 0
    hard_failure: str | None = None

    for case in cases:
        result = provider.run(language, code, case.get("input", ""))
        total_ms += result.runtime_ms
        if result.status != "accepted":
            hard_failure = result.status
            outcomes.append(
                CaseOutcome(
                    id=case.get("id", ""),
                    input=case.get("input", ""),
                    expected=case.get("expected", ""),
                    actual=result.stderr or result.stdout,
                    passed=False,
                    runtime_ms=result.runtime_ms,
                    is_sample=bool(case.get("is_sample")),
                    explanation=case.get("explanation"),
                )
            )
            if stop_on_compile_error and result.status in ("compile_error", "internal_error", "unsupported_language"):
                break
            continue
        passed = outputs_match(result.stdout, case.get("expected", ""))
        outcomes.append(
            CaseOutcome(
                id=case.get("id", ""),
                input=case.get("input", ""),
                expected=case.get("expected", ""),
                actual=result.stdout,
                passed=passed,
                runtime_ms=result.runtime_ms,
                is_sample=bool(case.get("is_sample")),
                explanation=case.get("explanation"),
            )
        )
        if not passed and hard_failure is None:
            hard_failure = "wrong_answer"

    passed_count = sum(1 for o in outcomes if o.passed)
    status = hard_failure or ("accepted" if passed_count == len(cases) and cases else "wrong_answer")
    return Evaluation(
        status=status,
        passed=passed_count,
        total=len(cases),
        runtime_ms=total_ms,
        stderr=next((o.actual for o in outcomes if not o.passed), ""),
        cases=outcomes,
    )
