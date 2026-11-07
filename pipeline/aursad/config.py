"""Paths and constants of the AURSAD pipeline."""
from __future__ import annotations

import os
import sys
from pathlib import Path

PIPELINE = Path(__file__).resolve().parents[1]
if str(PIPELINE) not in sys.path:
    sys.path.insert(0, str(PIPELINE))

from common.paths import DATA_ROOT, ROOT  # noqa: E402,F401

DATA = DATA_ROOT / "aursad"
# AURSAD.h5 (6.4 GB, Zenodo record 4559556) is not redistributed; extract.py reads it from here.
RAW_H5 = Path(os.environ.get("AURSAD_H5", DATA / "raw" / "AURSAD.h5"))
RAW_MD5 = "08e4706cf15144761a12cb86bd071d72"
CV_FOLDS = 5
CV_SEEDS = (0, 1, 2, 3, 4)
RUN_GAP_S = 1.0     # consecutive samples of one recording follow each other within this gap
