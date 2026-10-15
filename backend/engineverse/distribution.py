"""Public Android download links. Never accept a caller-controlled APK URL.

An APK is executable code installed outside an app store. Only an explicitly
configured, versioned release asset from *this* repository is advertised. The
release must be signed with the certificate advertised by the app origin's
Digital Asset Links; setting this URL does not build or sign an APK.
"""
from __future__ import annotations

import re

_APK_RELEASE = re.compile(
    r"https://github\.com/authorsauravkushwaha/EngineVerse/releases/download/"
    r"android-v[0-9][A-Za-z0-9._-]{0,63}/EngineVerse\.apk\Z"
)


def normalise_apk_url(value: str | None) -> str:
    """Return a safe, absolute download URL, or an empty string if unset."""
    url = (value or "").strip()
    if not url:
        return ""
    if not _APK_RELEASE.fullmatch(url) or ".." in url:
        raise ValueError(
            "ENGINEVERSE_APK_URL must point to a versioned EngineVerse.apk "
            "asset in this repository's Android GitHub Releases"
        )
    return url
