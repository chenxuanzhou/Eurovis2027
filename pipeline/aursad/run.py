"""Build the AURSAD products. Extraction from AURSAD.h5 runs only when the file is present.

    python pipeline/aursad/run.py            # extract (if AURSAD_H5 or data/aursad/raw/AURSAD.h5 exists), then build
    python pipeline/aursad/run.py --no-raw   # build from the committed samples and grids only
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import config as C

HERE = Path(__file__).resolve().parent


def main() -> None:
    if "--no-raw" not in sys.argv and C.RAW_H5.exists():
        print("\n=== aursad/extract.py", flush=True)
        subprocess.run([sys.executable, str(HERE / "extract.py"), "--h5", str(C.RAW_H5), "--out", str(C.DATA)],
                       check=True, cwd=C.ROOT)
    elif "--no-raw" not in sys.argv:
        print(f"\nAURSAD.h5 not found at {C.RAW_H5}; building from the committed samples")
    print("\n=== aursad/build.py", flush=True)
    subprocess.run([sys.executable, str(HERE / "build.py")], check=True, cwd=C.ROOT)


if __name__ == "__main__":
    main()
