#!/usr/bin/env python3
"""Run the Judge0 canary. Prints a sentence. Does not print the URL or the key.

Exit 0 always when the process itself worked. Exit 2 when the arguments are
wrong. A held canary is not a certification, so this script does not exit 0
to mean "isolated".
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (ROOT, os.path.join(ROOT, "backend")):
    if path not in sys.path:
        sys.path.insert(0, path)

from engineverse.judge.isolation import probe  # noqa: E402


def main() -> int:
    url = os.environ.get("ENGINEVERSE_JUDGE0_URL", "")
    key = os.environ.get("ENGINEVERSE_JUDGE0_KEY", "")
    os.environ.pop("ENGINEVERSE_JUDGE0_KEY", None)
    result = probe(url, key)
    print(result["sentence"])
    print(
        "configured={configured} reachable={reachable} canary_held={canary_held} "
        "secret_leaked={secret_leaked} isolated={isolated}".format(**result)
    )
    if url and url in result["sentence"]:
        print("refusing to print the URL", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
