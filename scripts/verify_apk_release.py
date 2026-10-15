#!/usr/bin/env python3
"""Fail a Pages publish if its configured signed APK asset does not exist."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from engineverse.distribution import normalise_apk_url  # noqa: E402

REPOSITORY = "authorsauravkushwaha/EngineVerse"


def verify(url: str, *, run=subprocess.run) -> None:
    url = normalise_apk_url(url)
    if not url:
        raise ValueError("No Android release URL was configured")
    tag = url.split("/releases/download/", 1)[1].split("/", 1)[0]
    result = run(
        ["gh", "release", "view", tag, "--repo", REPOSITORY, "--json", "assets,isDraft"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise ValueError("The Android GitHub Release cannot be read")
    release = json.loads(result.stdout)
    if release.get("isDraft") is not False or not any(
        isinstance(asset, dict) and asset.get("name") == "EngineVerse.apk"
        and isinstance(asset.get("size"), int) and asset["size"] > 0
        for asset in release.get("assets", [])
    ):
        raise ValueError("The Android GitHub Release has no public nonempty EngineVerse.apk asset")
    print("Verified the versioned signed APK release asset exists.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    args = parser.parse_args()
    try:
        verify(args.url)
    except (ValueError, OSError) as exc:
        raise SystemExit(f"Refusing an unverified APK link: {exc}") from None
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
