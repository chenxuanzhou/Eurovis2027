"""Paths and constants of the voraus-AD pipeline."""
from __future__ import annotations

import os
import sys
from pathlib import Path

PIPELINE = Path(__file__).resolve().parents[1]
VENDOR = Path(__file__).resolve().parent / "vendor"
for p in (PIPELINE, VENDOR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from common.paths import DATA_ROOT, MAX_FILE_MB, ROOT  # noqa: E402,F401

DATA = DATA_ROOT / "voraus_ad"

# The raw voraus-AD file is not redistributed (see data/voraus_ad/raw/README.md).
RAW_PARQUET = Path(os.environ.get(
    "VORAUS_PARQUET", DATA / "raw" / "voraus-ad-dataset-100hz.parquet"))

# Optional: a checkout of the SAFEPROCESS 2027 repository, used only to copy its
# derived evidence records and to cross-check the knowledge-base export.
SNIS_REPO = Path(os.environ.get(
    "SNIS_REPO",
    ROOT.parent / "Structural-Non-Isolability-in-Knowledge-Based-Robot-Fault-Diagnosis"))
SNIS_COMMIT = "438389f10b034c3b215750b9fd4ca734d72b106c"
VORAUS_CODE_COMMIT = "a91a86a642d23df58833b792a53de01edfd81abe"

GRID_N = 500                  # normalized task-progress grid (same as the SAFEPROCESS records)
TRAIN_SETTING = 72            # Variant.PRE_A: the 948 anomaly-free training cycles (official split)
NORMAL_CATEGORY = 12          # Category.NORMAL_OPERATION
LSO_SEEDS = (0, 1, 2, 3, 4)   # leave-setting-out splits of the SAFEPROCESS 2027 study
GRID_KEEP_MANTISSA_BITS = 12  # per-cycle grid signals: ~4 significant digits, see common.parquet_io.trim_mantissa
TRAIN_SAMPLE_N = 100          # training cycles shipped per-cycle (all 948 are summarized in the envelope)
TRAIN_SAMPLE_SEED = 2027

JOINTS = (1, 2, 3, 4, 5, 6)

# Per-cycle signals kept on the progress grid (data/voraus_ad/signals/grid500).
# The four knowledge-base families per joint plus the two robot-level currents
# (what the FMEA reads), the two "unread" families the certificates use, and the
# commanded torque so a command-conditioned residual can be drawn.
GRID_JOINT_FAMILIES = (
    "motor_torque", "torque_sensor_a", "joint_velocity", "joint_position",
    "motor_iq", "power_load_mech", "target_torque",
)
GRID_ROBOT_SIGNALS = ("robot_current", "system_current")


def grid_channels() -> list[str]:
    cols = [f"{fam}_{j}" for fam in GRID_JOINT_FAMILIES for j in JOINTS]
    return cols + list(GRID_ROBOT_SIGNALS)
