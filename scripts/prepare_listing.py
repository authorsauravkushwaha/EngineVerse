#!/usr/bin/env python3
"""Build the Play listing pack from the configured site name.

This writes text and a feature graphic. It does not upload anything, does not
create a keystore, and does not say the listing is approved. Core learning
stays free. Certificates are not described as accredited degrees.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ICON = ROOT / "backend" / "static" / "icons" / "icon-512.png"
FONT = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
FORBIDDEN = (
    "play approved",
    "published on google play",
    "available on google play",
    "this is an accredited degree",
)


def listing_text(site_name: str) -> dict[str, str]:
    name = (site_name or "EngineVerse").strip() or "EngineVerse"
    if len(name) > 30:
        raise SystemExit("Site name is longer than the Play title limit of 30 characters.")
    short = f"Free engineering notes, practice and projects."
    if len(short) > 80:
        raise SystemExit("Short description exceeds 80 characters.")
    full = (
        f"{name} is a free study app for engineering students. Notes, practice, "
        "flashcards and projects are included. Certificates are completion records "
        "from this app. They are not accredited degrees and they are not issued by "
        "a university.\n\n"
        "Sign-in is first-party. The app does not load third-party scripts. "
        "Install it when the site is served over HTTPS; the package is a Trusted "
        "Web Activity around that site, not a second catalogue.\n\n"
        "This listing text is a pack in the repository. It is not a submission "
        "and it has not been reviewed by Google Play."
    )
    if len(full) > 4000:
        raise SystemExit("Full description exceeds 4000 characters.")
    blob = " ".join((name, short, full)).lower()
    for phrase in FORBIDDEN:
        if phrase in blob:
            raise SystemExit(f"Listing text must not say {phrase!r}.")
    return {
        "title": name,
        "short_description": short,
        "full_description": full,
        "privacy_policy_path": "/privacy",
        "free": "true",
        "submitted": "false",
        "play_approved": "false",
    }


def write_pack(dest: Path, site_name: str) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    text = listing_text(site_name)
    (dest / "listing.json").write_text(json.dumps(text, indent=2) + "\n", encoding="utf-8")
    if not ICON.is_file():
        raise SystemExit(f"Missing icon: {ICON}")
    shutil.copyfile(ICON, dest / "icon-512.png")
    graphic = dest / "feature-graphic.png"
    subprocess.run(
        [
            "convert", "-size", "1024x500", "gradient:#e4e9f1-#c9d4e6",
            "(", str(ICON), "-resize", "280x280", ")",
            "-gravity", "west", "-geometry", "+72+0", "-composite",
            "-font", str(FONT), "-fill", "#1e293b", "-pointsize", "64",
            "-gravity", "west", "-annotate", "+400-30", text["title"],
            "-font", str(FONT), "-fill", "#475569", "-pointsize", "28",
            "-annotate", "+400+40", "Free notes. Not an accredited degree.",
            str(graphic),
        ],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Write the Play listing pack. Does not upload it.")
    parser.add_argument("--site-name", default="EngineVerse")
    parser.add_argument("--dest", default=str(ROOT / "android" / "listing"))
    args = parser.parse_args()
    write_pack(Path(args.dest), args.site_name)
    print(f"Wrote {args.dest}. Nothing was uploaded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
