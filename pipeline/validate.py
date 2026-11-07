"""Validate every dataset's products, then the repository-wide rules.

    python pipeline/validate.py              # all datasets
    python pipeline/validate.py aursad       # one or more datasets by folder name

Each dataset's own checks live in pipeline/<dataset>/validate.py (run here in a subprocess,
since every dataset folder has its own config module). Repository-wide rules: every committed
data file stays below the GitHub size limit, and every dataset folder carries a README and a
licence entry. Exits with status 1 if any check fails.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common.checks import Checker  # noqa: E402
from common.paths import DATA_ROOT, DATASETS, MAX_FILE_MB, ROOT  # noqa: E402


def committable_files() -> list[Path]:
    """Data files git would commit (tracked or new, not ignored); every file if git is unavailable."""
    try:
        out = subprocess.run(["git", "ls-files", "-co", "--exclude-standard", "--", str(DATA_ROOT)],
                             cwd=ROOT, capture_output=True, text=True, check=True).stdout
        return [ROOT / line for line in out.splitlines() if (ROOT / line).is_file()]
    except (OSError, subprocess.CalledProcessError):
        return [p for p in DATA_ROOT.rglob("*") if p.is_file()]


def repository_rules(ck: Checker, chosen: list[str]) -> None:
    tracked = committable_files()
    worst = max(tracked, key=lambda p: p.stat().st_size)
    total = sum(p.stat().st_size for p in tracked) / 2**20
    ck.check("every data file below the GitHub limit", worst.stat().st_size / 2**20 < MAX_FILE_MB,
             f"largest {worst.relative_to(ROOT)} = {worst.stat().st_size / 2**20:.1f} MB, total {total:.1f} MB")
    licence = (DATA_ROOT / "LICENSE.md").read_text(encoding="utf-8")
    for ds in chosen:
        d = DATA_ROOT / ds
        if not d.exists():
            ck.wait(f"{ds}: data folder", "not built yet")
            continue
        ck.check(f"{ds}: README present", (d / "README.md").exists())
        ck.check(f"{ds}: licence listed in data/LICENSE.md", f"data/{ds}/" in licence)


def main() -> None:
    chosen = sys.argv[1:] or list(DATASETS)
    failed = []
    for ds in chosen:
        v = HERE / ds / "validate.py"
        if not v.exists():
            print(f"\n## {ds}: no validator yet")
            continue
        if subprocess.run([sys.executable, str(v)], cwd=ROOT).returncode != 0:
            failed.append(ds)
    ck = Checker("repository")
    repository_rules(ck, chosen)
    if failed or ck.failed:
        print(f"\nchecks failed: {failed + ck.failed}")
        sys.exit(1)
    print("\nall checks passed")


if __name__ == "__main__":
    main()
