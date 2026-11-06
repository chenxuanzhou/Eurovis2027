"""Rebuild every data product in order, then validate. Works on Windows, macOS and Linux.

    python pipeline/run_all.py            # all steps; raw steps are skipped if the parquet is missing
    python pipeline/run_all.py --no-raw   # only the products that need no raw data

Environment variables: SNIS_REPO (checkout of the SAFEPROCESS 2027 repository),
VORAUS_PARQUET (path of voraus-ad-dataset-100hz.parquet, default data/raw/).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import config as C

HERE = Path(__file__).resolve().parent
STEPS_NO_RAW = ["build_evidence.py", "build_catalog.py", "build_kb.py"]
STEPS_RAW = ["build_from_raw.py"]


def run(script: str) -> None:
    print(f"\n=== {script}", flush=True)
    subprocess.run([sys.executable, str(HERE / script)], check=True, cwd=C.ROOT)


def main() -> None:
    for s in STEPS_NO_RAW:
        run(s)
    if "--no-raw" not in sys.argv:
        if C.RAW_PARQUET.exists():
            for s in STEPS_RAW:
                run(s)
        else:
            print(f"\nraw parquet not found at {C.RAW_PARQUET}; skipping {STEPS_RAW}")
    run("validate.py")


if __name__ == "__main__":
    main()
