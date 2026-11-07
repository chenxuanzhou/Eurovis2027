"""Paths and constants of the UCI Robot Execution Failures pipeline."""
from __future__ import annotations

import sys
from pathlib import Path

PIPELINE = Path(__file__).resolve().parents[1]
if str(PIPELINE) not in sys.path:
    sys.path.insert(0, str(PIPELINE))

from common.paths import DATA_ROOT, ROOT  # noqa: E402,F401

DATA = DATA_ROOT / "robot_failures"
RAW = DATA / "raw"          # the five UCI files are small and CC BY 4.0, so they are committed

CHANNELS = ("Fx", "Fy", "Fz", "Tx", "Ty", "Tz")
STEPS = 15                  # force/torque samples per instance, starting at failure detection
WINDOW_MS = 315             # total observation window per instance (UCI description)
CV_FOLDS = 5
CV_SEEDS = (0, 1, 2, 3, 4)
SCALE_FLOOR = 1.0           # readings are integers, so one unit is the resolution

# Expected instance counts per problem (UCI description), checked on every build.
EXPECTED = {"LP1": 88, "LP2": 47, "LP3": 47, "LP4": 117, "LP5": 164}
RAW_SHA256 = {
    "lp1.data": "e146de5aeaffd864f0e57ce2fe0b58e98582c3e808e6c0e8deb9b25a54ef0cb5",
    "lp2.data": "565096a67cc8b9e4cef299316b3ab769054215a6342636e208611eafa780f950",
    "lp3.data": "38e5cb0b22477772a03edee82599591375790cb945cf1256ed0a4b516cc30e1a",
    "lp4.data": "f0c901ead751ff3104d7e1aeb23165efb88270b219c1954c43bfff2344a7bb3c",
    "lp5.data": "0f327415504dccec9509a84f6fa7aea9ebc28e5fa85f2f00933c90565d51108d",
}
