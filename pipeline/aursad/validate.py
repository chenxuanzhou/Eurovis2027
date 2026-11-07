"""Check the AURSAD products.

Run from the repository root:  python pipeline/aursad/validate.py   (or python pipeline/validate.py)
"""
from __future__ import annotations

import json
import sys

import pandas as pd

import config as C  # noqa: I001  (puts pipeline/ on sys.path)
from common.checks import Checker
from common.lattice import check_lattice

ZENODO = {0: 1420, 1: 221, 2: 183, 3: 218, 4: 3, 5: 2049}   # label table of the Zenodo record


def run(ck: Checker | None = None) -> Checker:
    ck = ck or Checker("AURSAD")
    s = pd.read_csv(C.DATA / "samples.csv")
    ck.check("label counts match the Zenodo record", s["label"].value_counts().sort_index().to_dict() == ZENODO)
    ck.check("screwdriving phases found in > 99 % of samples", s["command_found"].mean() > 0.99,
             f"{s['command_found'].mean():.4f}")
    g = pd.read_csv(C.DATA / "sample_groups.csv")
    q = json.loads((C.DATA / "data_quality.json").read_text(encoding="utf-8"))
    ck.check("3127 distinct signal blocks, 61 duplicate pairs with conflicting labels",
             q["distinct_signal_blocks"] == 3127 and q["duplicate_groups_with_conflicting_labels"] == 61)
    man = json.loads((C.DATA / "signals" / "grid500" / "manifest.json").read_text(encoding="utf-8"))
    n = 0
    for name, part in man["parts"].items():
        df = pd.read_parquet(C.DATA / "signals" / "grid500" / part["file"])
        n += part["n_samples"]
        ck.check(f"grid500 {name}: {part['n_samples']} samples x 500 rows, no gaps",
                 len(df) == part["n_samples"] * 500 and not df.isna().any().any())
    ck.check("grids hold every distinct tightening sample once", n == q["distinct_tightening"])
    env = pd.read_parquet(C.DATA / "envelope" / "normal_envelope_grid500.parquet")
    ck.check("envelope: 20 channels x 500 points", len(env) == 20 * 500 and not env.isna().any().any())
    z = pd.read_csv(C.DATA / "evidence" / "features_z.csv")
    ck.check("evidence: 16 features per tightening sample", len(z) == 2045 * 16)
    sp = json.loads((C.DATA / "splits" / "leave_session_out.json").read_text(encoding="utf-8"))
    ok = True
    for f in sp["seeds"].values():
        folds = g["sample_nr"].astype(str).map(f)
        ok &= folds.notna().all() and g.assign(f=folds).groupby("duplicate_group")["f"].nunique().max() == 1 \
            and g.assign(f=folds).groupby("session")["f"].nunique().max() == 1
    ck.check("every seed keeps sessions and duplicated recordings inside one fold", bool(ok))
    lat = json.loads((C.DATA / "kb" / "refinement_lattice.json").read_text(encoding="utf-8"))
    problems = check_lattice(lat)
    ck.check("lattice: each level refines the previous one, blocks contiguous", not problems, "; ".join(problems))
    l4 = next(lv for lv in lat["levels"] if lv["id"] == "L4")
    ck.check("damaged screw and damaged plate thread stay twins until history",
             [sorted(b) for b in l4["twin_blocks"]] == [["damaged_plate_thread", "damaged_screw"]]
             and lat["levels"][-1]["twin_blocks"] == [])
    return ck


if __name__ == "__main__":
    sys.exit(1 if run().failed else 0)
