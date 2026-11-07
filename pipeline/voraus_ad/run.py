"""Build every voraus-AD product in order. Raw steps are skipped when the parquet is missing.

    python pipeline/voraus_ad/run.py            # all steps
    python pipeline/voraus_ad/run.py --no-raw   # only the products that need no raw data

Environment variables: SNIS_REPO (checkout of the SAFEPROCESS 2027 repository),
VORAUS_PARQUET (path of voraus-ad-dataset-100hz.parquet, default data/voraus_ad/raw/).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import config as C

HERE = Path(__file__).resolve().parent
STEPS = ["build_evidence.py", "build_catalog.py", "build_kb.py"]
RAW_STEPS = ["build_from_raw.py"]


def run(script: str) -> None:
    print(f"\n=== voraus_ad/{script}", flush=True)
    subprocess.run([sys.executable, str(HERE / script)], check=True, cwd=C.ROOT)


def main() -> None:
    for s in STEPS:
        run(s)
    if "--no-raw" in sys.argv:
        return
    if C.RAW_PARQUET.exists():
        for s in RAW_STEPS:
            run(s)
    else:
        print(f"\nraw parquet not found at {C.RAW_PARQUET}; skipping {RAW_STEPS}")


if __name__ == "__main__":
    main()
