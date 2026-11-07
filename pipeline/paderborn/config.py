"""Paths and constants of the Paderborn pipeline."""
from __future__ import annotations

import os
import sys
from pathlib import Path

PIPELINE = Path(__file__).resolve().parents[1]
if str(PIPELINE) not in sys.path:
    sys.path.insert(0, str(PIPELINE))

from common.paths import DATA_ROOT, ROOT  # noqa: E402,F401

DATA = DATA_ROOT / "paderborn"
# The raw .mat files (12 bearings, about 8.4 GB) are not redistributed; extract.py reads them from here.
RAW = Path(os.environ.get("PADERBORN_RAW", DATA / "raw"))
CV_SEEDS = (0, 1, 2, 3, 4)
