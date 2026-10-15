#!/usr/bin/env python3
"""Refuse to build an APK unless the full app trusts its signing certificate."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.export_pages import normalise_app_url  # noqa: E402
from scripts.verify_hosted_app import fetch  # noqa: E402

PACKAGE = re.compile(r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+\Z")
FINGERPRINT = re.compile(r"[A-F0-9]{2}(?::[A-F0-9]{2}){31}\Z")


def verify(origin: str, package: str, fingerprint: str, *, get=fetch) -> None:
    origin = normalise_app_url(origin)
    fingerprint = fingerprint.upper().strip()
    if not origin.startswith("https://") or not PACKAGE.fullmatch(package) or not FINGERPRINT.fullmatch(fingerprint):
        raise ValueError("HTTPS app origin, Android package and SHA-256 fingerprint are required")
    kind, body = get(origin, "/.well-known/assetlinks.json")
    if "application/json" not in kind:
        raise ValueError("Digital Asset Links did not return JSON")
    rows = json.loads(body)
    if not isinstance(rows, list) or not any(
        isinstance(row, dict) and isinstance(row.get("relation"), list)
        and "delegate_permission/common.handle_all_urls" in row["relation"]
        and isinstance(row.get("target"), dict)
        and row["target"].get("namespace") == "android_app"
        and row["target"].get("package_name") == package
        and isinstance(row["target"].get("sha256_cert_fingerprints"), list)
        and fingerprint in row["target"]["sha256_cert_fingerprints"]
        for row in rows
    ):
        raise ValueError("The hosted site's Digital Asset Links do not match the APK signer")
    print("Verified Digital Asset Links match the package and signing certificate.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--package", required=True)
    parser.add_argument("--fingerprint", required=True)
    args = parser.parse_args()
    try:
        verify(args.url, args.package, args.fingerprint)
    except (HTTPError, URLError, OSError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Refusing Android release: {exc}") from None
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
