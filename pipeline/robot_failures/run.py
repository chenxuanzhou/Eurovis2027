"""Build every UCI Robot Execution Failures product (the raw files are in the repository)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import config as C

HERE = Path(__file__).resolve().parent

if __name__ == "__main__":
    print("\n=== robot_failures/build.py", flush=True)
    subprocess.run([sys.executable, str(HERE / "build.py")], check=True, cwd=C.ROOT)
