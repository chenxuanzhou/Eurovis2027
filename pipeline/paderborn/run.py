"""Build the Paderborn products. Extraction from the raw .mat files runs only when they are present.

    python pipeline/paderborn/run.py            # extract (if PADERBORN_RAW or data/paderborn/raw has the files), then build
    python pipeline/paderborn/run.py --no-raw   # build from the committed measurements and spectra only
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import config as C

HERE = Path(__file__).resolve().parent


def main() -> None:
    if "--no-raw" not in sys.argv and any(C.RAW.glob("K*/*.mat")):
        print("\n=== paderborn/extract.py", flush=True)
        subprocess.run([sys.executable, str(HERE / "extract.py"), "--raw", str(C.RAW), "--out", str(C.DATA),
                        "--work", str(C.DATA / "raw" / "_cache")], check=True, cwd=C.ROOT)
    elif "--no-raw" not in sys.argv:
        print(f"\nraw .mat files not found under {C.RAW}; building from the committed measurements")
    print("\n=== paderborn/build.py", flush=True)
    subprocess.run([sys.executable, str(HERE / "build.py")], check=True, cwd=C.ROOT)


if __name__ == "__main__":
    main()
