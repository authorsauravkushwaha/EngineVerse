"""Write every 3D scene as JSON, for the Node-side build check.

    python scripts/dump_scenes.py | node scripts/check_scenes.js

The scenes are Python objects and the renderer is JavaScript, so verifying that
one can actually draw the other needs both runtimes. This is the bridge: it
emits the raw (pre-validation) scenes so the check sees exactly what the
authors wrote, not what the validator was able to rescue.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from seed_data.models_3d import MODELS_3D  # noqa: E402

if __name__ == "__main__":
    json.dump(MODELS_3D, sys.stdout)
