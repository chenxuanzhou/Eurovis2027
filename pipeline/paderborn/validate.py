"""Check the Paderborn products.

Run from the repository root:  python pipeline/paderborn/validate.py   (or python pipeline/validate.py)
"""
from __future__ import annotations

import json
import sys

import pandas as pd

import config as C  # noqa: I001  (puts pipeline/ on sys.path)
import kb_spec as K
from common.checks import Checker
from common.lattice import check_lattice


def run(ck: Checker | None = None) -> Checker:
    ck = ck or Checker("Paderborn bearings")
    m = pd.read_csv(C.DATA / "measurements.csv")
    per = m.groupby(["bearing", "condition"]).size()
    ck.check("960 measurements: 12 bearings x 4 conditions x 20", len(m) == 960 and per.eq(20).all()
             and per.index.get_level_values(0).nunique() == 12)
    ck.check("every bearing is described in kb_spec", set(m["bearing"]) == set(K.BEARINGS))
    g = pd.read_csv(C.DATA / "measurement_groups.csv")
    off = g[g["quality_flag"].fillna("") == "unsteady_speed"]
    ck.check("measured speed within 1 % of the set point except one flagged unsteady file",
             list(off["file"]) == ["N09_M07_F10_KA04_13.mat"], f"{list(off['file'])}")
    dup = m[m["signal_hash"].duplicated(keep=False)]
    ck.check("identical signals only inside KA04 (measuring log documents one copy)",
             set(dup["bearing"]) <= {"KA04"} and int(m["signal_hash"].duplicated().sum()) == 4,
             f"{sorted(dup['file'])}")
    for name in ("envelope_orders", "current_sidebands"):
        s = pd.read_parquet(C.DATA / "spectra" / f"{name}.parquet")
        ck.check(f"{name}: 1201 bins per measurement, no gaps",
                 len(s) == 960 * 1201 and s["measurement_id"].nunique() == 960 and not s.isna().any().any())
    z = pd.read_csv(C.DATA / "evidence" / "features_z.csv")
    ck.check("evidence: 16 features per measurement", len(z) == 960 * 16)
    sp = json.loads((C.DATA / "splits" / "leave_bearing_out.json").read_text(encoding="utf-8"))
    ok = True
    for f in sp["seeds"].values():
        for k in range(4):
            held = [b for b, v in f.items() if v == k]
            ok &= sorted(K.BEARINGS[b][0] for b in held) == ["IR", "OR", "healthy"]
    ck.check("each fold holds out one healthy, one OR and one IR bearing", ok)
    lat = json.loads((C.DATA / "kb" / "refinement_lattice.json").read_text(encoding="utf-8"))
    problems = check_lattice(lat)
    ck.check("lattice: each level refines the previous one, blocks contiguous", not problems, "; ".join(problems))
    l4 = next(lv for lv in lat["levels"] if lv["id"] == "L4")
    ck.check("outer-ring damage types stay twins until raceway inspection",
             [sorted(b) for b in l4["twin_blocks"]] == [["OR_indentation", "OR_pitting", "OR_pitting_repetitive"]]
             and lat["levels"][-1]["twin_blocks"] == [])
    return ck


if __name__ == "__main__":
    sys.exit(1 if run().failed else 0)
