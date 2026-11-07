"""Repository paths shared by every dataset pipeline."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = Path(os.environ.get("EV_DATA_DIR", ROOT / "data"))   # override only for tests
MAX_FILE_MB = 45   # every committed file stays under GitHub's 50 MB warning

# One folder per dataset under data/ and pipeline/, in the order run_all.py builds them.
DATASETS = ("voraus_ad", "robot_failures", "paderborn", "aursad")
