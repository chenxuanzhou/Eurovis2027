"""Rebuild every dataset's products, then validate. Works on Windows, macOS and Linux.

    python pipeline/run_all.py              # all datasets, all steps (raw steps skipped where raw data is missing)
    python pipeline/run_all.py --no-raw     # only the products that need no raw data
    python pipeline/run_all.py paderborn    # one or more datasets by folder name

Each dataset has its own pipeline/<dataset>/run.py; see its README for the raw data it needs.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common.paths import DATASETS, ROOT  # noqa: E402


def main() -> None:
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    chosen = [a for a in sys.argv[1:] if not a.startswith("--")] or list(DATASETS)
    unknown = set(chosen) - set(DATASETS)
    if unknown:
        raise SystemExit(f"unknown dataset(s) {sorted(unknown)}; choose from {DATASETS}")
    for ds in chosen:
        runner = HERE / ds / "run.py"
        if not runner.exists():
            print(f"\n### {ds}: no pipeline yet")
            continue
        print(f"\n### {ds}", flush=True)
        subprocess.run([sys.executable, str(runner), *flags], check=True, cwd=ROOT)
    subprocess.run([sys.executable, str(HERE / "validate.py"), *chosen], check=True, cwd=ROOT)


if __name__ == "__main__":
    main()
