"""Runtime configuration.

Every knob is an environment variable so the same image runs on a laptop and
in production. Nothing here reaches out to a third-party service.
"""
from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_dotenv() -> None:
    """Minimal .env loader - avoids a dependency for something this small."""
    env_file = REPO_ROOT / ".env"
    if not env_file.exists():
        return
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv()

#: The value ``effective_secret()`` invents when nothing is configured. It is
#: fine for a laptop. It must never be accepted as a production signing key.
DEV_SECRET = "engineverse-development-secret-not-for-production"
MIN_SECRET_LENGTH = 32

#: Judges that execute learner code inside this process's machine. Production
#: refuses them. ``disabled`` runs nothing. ``judge0`` delegates to a URL the
#: operator deployed separately; this process does not verify that host.
LOCAL_JUDGES = frozenset({"", "auto", "python", "java", "local"})

#: The login role the web process uses. It must not own the schema. The
#: official Postgres image makes the first user a superuser, so that user is
#: the migration role and this one is created beside it.
RUNTIME_DB_ROLE = "engineverse_app"

# Older deploy files used these names. They are copied into the names the
# application actually reads, and only when the canonical variable is unset,
# so an explicit ENGINEVERSE_* value always wins.
_ENV_ALIASES = {
    "ENGINEVERSE_SITE_URL": ("SITE_URL",),
    "ENGINEVERSE_JUDGE": ("JUDGE",),
    "ENGINEVERSE_JAVA_SANDBOX_JAR": ("JAVA_SANDBOX_JAR",),
}


def _apply_env_aliases() -> None:
    for canonical, aliases in _ENV_ALIASES.items():
        if os.environ.get(canonical, "").strip():
            continue
        for alias in aliases:
            value = os.environ.get(alias, "").strip()
            if value:
                os.environ[canonical] = value
                break


def _bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # --- identity ---------------------------------------------------------
    site_url: str = field(default_factory=lambda: os.environ.get("ENGINEVERSE_SITE_URL", "http://localhost:8000").rstrip("/"))
    secret: str = field(default_factory=lambda: os.environ.get("ENGINEVERSE_SECRET", ""))
    env: str = field(default_factory=lambda: os.environ.get("ENGINEVERSE_ENV", "development"))

    # --- database ---------------------------------------------------------
    db_path: str = field(default_factory=lambda: os.environ.get("ENGINEVERSE_DB_PATH", "./data/engineverse.sqlite"))
    db_url: str = field(default_factory=lambda: os.environ.get("ENGINEVERSE_DB_URL", ""))

    # --- sessions ---------------------------------------------------------
    session_max_age_days: int = field(default_factory=lambda: int(os.environ.get("ENGINEVERSE_SESSION_DAYS", "30")))
    session_idle_days: int = field(default_factory=lambda: int(os.environ.get("ENGINEVERSE_SESSION_IDLE_DAYS", "7")))
    cookie_secure: bool = field(default_factory=lambda: _bool("ENGINEVERSE_COOKIE_SECURE", False))
    #: Trust X-Forwarded-For only from a private or loopback peer. Default off.
    trust_proxy: bool = field(default_factory=lambda: _bool("ENGINEVERSE_TRUST_PROXY", False))

    # --- code execution ---------------------------------------------------
    judge: str = field(default_factory=lambda: os.environ.get("ENGINEVERSE_JUDGE", "auto").lower())
    judge_timeout_ms: int = field(default_factory=lambda: int(os.environ.get("ENGINEVERSE_JUDGE_TIMEOUT_MS", "5000")))
    judge_memory_kb: int = field(default_factory=lambda: int(os.environ.get("ENGINEVERSE_JUDGE_MEMORY_KB", "524288")))
    judge0_url: str = field(default_factory=lambda: os.environ.get("ENGINEVERSE_JUDGE0_URL", ""))
    judge0_key: str = field(default_factory=lambda: os.environ.get("ENGINEVERSE_JUDGE0_KEY", ""))
    java_home: str = field(default_factory=lambda: os.environ.get("JAVA_HOME", ""))
    java_sandbox_jar: str = field(
        default_factory=lambda: os.environ.get(
            "ENGINEVERSE_JAVA_SANDBOX_JAR", "./sandbox-java/target/engineverse-sandbox.jar"
        )
    )

    # --- outbound mail ----------------------------------------------------
    # Empty smtp_url means this instance has no mail transport. That is the
    # default, and it matters: without it a password reset link has nowhere to
    # go, so it must not be handed to the caller instead. See engineverse.notify.
    smtp_url: str = field(default_factory=lambda: os.environ.get("ENGINEVERSE_SMTP_URL", ""))
    mail_from: str = field(default_factory=lambda: os.environ.get(
        "ENGINEVERSE_MAIL_FROM", "EngineVerse <no-reply@localhost>"))
    #: Shows the reset token in the page instead of emailing it. Development
    #: only, and refused outright when env is production. Default off: turning
    #: it on makes POST /forgot-password an account-takeover endpoint.
    reveal_reset_token: bool = field(default_factory=lambda: _bool("ENGINEVERSE_REVEAL_RESET_TOKEN", False))

    # --- AI tutor ---------------------------------------------------------
    ai_key: str = field(default_factory=lambda: os.environ.get("ENGINEVERSE_AI_KEY", ""))
    ai_url: str = field(default_factory=lambda: os.environ.get("ENGINEVERSE_AI_URL", ""))

    # --- hosting ----------------------------------------------------------
    host: str = field(default_factory=lambda: os.environ.get("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.environ.get("PORT", "8000")))

    @property
    def repo_root(self) -> Path:
        return REPO_ROOT

    @property
    def sqlite_path(self) -> Path:
        p = Path(self.db_path)
        return p if p.is_absolute() else (REPO_ROOT / p).resolve()

    @property
    def uses_postgres(self) -> bool:
        return self.db_url.startswith(("postgresql://", "postgres://"))

    @property
    def is_production(self) -> bool:
        return self.env.lower() in {"production", "prod"}

    @property
    def is_https(self) -> bool:
        return self.site_url.startswith("https://")

    def effective_secret(self) -> bytes:
        """Returns the configured secret, refusing to run unsafely in prod."""
        secret = self.secret.strip()
        if not secret:
            if self.is_production:
                raise RuntimeError(
                    "ENGINEVERSE_SECRET must be set in production. "
                    'Generate one with: python3 -c "import secrets;print(secrets.token_hex(32))"'
                )
            secret = DEV_SECRET
        return secret.encode("utf-8")

    def new_secret_hint(self) -> str:
        return secrets.token_hex(32)

    @property
    def allows_demo_accounts(self) -> bool:
        """Development and the test suite only. Never production, never staging."""
        return self.env.lower() in {"development", "test", "dev", ""}

    def production_problems(self) -> list[str]:
        """Reasons this process must not serve production traffic.

        The messages name the variable, never the secret itself. An empty list
        means the checks in this method passed. It does not mean the deployment
        has been reviewed, backed up, or isolated.
        """
        if not self.is_production:
            return []
        problems: list[str] = []
        secret = self.secret.strip()
        if not secret:
            problems.append("ENGINEVERSE_SECRET is empty")
        elif secret == DEV_SECRET:
            problems.append("ENGINEVERSE_SECRET is the development fallback")
        elif len(secret) < MIN_SECRET_LENGTH:
            problems.append(f"ENGINEVERSE_SECRET is shorter than {MIN_SECRET_LENGTH} characters")
        if not self.db_url:
            problems.append("ENGINEVERSE_DB_URL is required in production; SQLite is not a production database")
        elif not self.uses_postgres:
            problems.append("ENGINEVERSE_DB_URL must be a postgresql:// URL in production")
        from urllib.parse import urlparse

        parsed = urlparse(self.site_url)
        if parsed.scheme != "https" or not parsed.hostname:
            problems.append("ENGINEVERSE_SITE_URL must be an https:// origin in production")
        if self.reveal_reset_token:
            problems.append("ENGINEVERSE_REVEAL_RESET_TOKEN must not be set in production")
        judge = (self.judge or "").lower()
        if judge in LOCAL_JUDGES:
            shown = judge or "auto"
            problems.append(
                f"ENGINEVERSE_JUDGE={shown} would run learner code on this server; "
                "production requires 'disabled' or 'judge0' with ENGINEVERSE_JUDGE0_URL"
            )
        elif judge == "judge0" and not self.judge0_url.strip():
            problems.append("ENGINEVERSE_JUDGE=judge0 requires ENGINEVERSE_JUDGE0_URL")
        elif judge not in {"disabled", "judge0"}:
            problems.append(f"ENGINEVERSE_JUDGE={judge} is not a known production mode")
        return problems


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    _apply_env_aliases()
    return Settings()


def reload_settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()
