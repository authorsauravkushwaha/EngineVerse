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
            secret = "engineverse-development-secret-not-for-production"
        return secret.encode("utf-8")

    def new_secret_hint(self) -> str:
        return secrets.token_hex(32)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def reload_settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()
