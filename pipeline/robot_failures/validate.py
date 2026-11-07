"""Check the UCI Robot Execution Failures products.

Run from the repository root:  python pipeline/robot_failures/validate.py   (or python pipeline/validate.py)
"""
from __future__ import annotations

import json
import sys

import pandas as pd

import config as C  # noqa: I001  (puts pipeline/ on sys.path)
import kb_spec as K
from common.checks import Checker
from common.lattice import check_lattice

# class shares published with the dataset (UCI description), in percent
PUBLISHED = {
    "LP1": {"normal": 24, "collision": 19, "fr_collision": 18, "obstruction": 39},
    "LP2": {"normal": 43, "front_col": 13, "back_col": 15, "right_col": 11, "left_col": 19},
    "LP3": {"ok": 43, "slightly_moved": 19, "moved": 32, "lost": 6},
    "LP4": {"normal": 21, "collision": 62, "obstruction": 18},
    "LP5": {"normal": 27, "bottom_collision": 16, "bottom_obstruction": 13, "collision_in_part": 29,
            "collision_in_tool": 16},
}


def run(ck: Checker | None = None) -> Checker:
    ck = ck or Checker("UCI Robot Execution Failures")
    inst = pd.read_csv(C.DATA / "instances.csv")
    n = inst.groupby("problem").size().to_dict()
    ck.check("instances per problem match the UCI description", n == C.EXPECTED, str(n))
    shares = {p: (g["label"].value_counts(normalize=True) * 100).round().astype(int).to_dict()
              for p, g in inst.groupby("problem")}
    ck.check("class shares match the UCI description (rounded %)", shares == PUBLISHED)
    sig = pd.read_csv(C.DATA / "signals.csv")
    ck.check("15 x 6 readings per instance", len(sig) == 463 * C.STEPS and not sig.isna().any().any())
    win = pd.read_csv(C.DATA / "windows.csv")
    ck.check("251 distinct windows", len(win) == 251 and inst["window_id"].nunique() == 251)
    sl = pd.read_csv(C.DATA / "evidence" / "slots.csv")
    ck.check("evidence slots: 463 instances x 6 channels", len(sl) == 463 * 6 and not sl.isna().any().any())
    sp = json.loads((C.DATA / "splits" / "grouped_cv.json").read_text(encoding="utf-8"))
    ok = True
    for f in sp["seeds"].values():
        folds = inst["instance_id"].map(f)
        ok &= folds.notna().all() and inst.assign(f=folds).groupby("window_id")["f"].nunique().max() == 1
    ck.check("every seed assigns every instance, identical windows share a fold", bool(ok))
    lat = json.loads((C.DATA / "kb" / "refinement_lattice.json").read_text(encoding="utf-8"))
    ck.check("knowledge base covers every class", sorted(lat["modes"]) == sorted(K.MODES)
             and sorted(inst["mode"].unique()) == sorted(K.MODES))
    problems = check_lattice(lat)
    ck.check("lattice: each level refines the previous one, blocks contiguous", not problems, "; ".join(problems))
    final = lat["levels"][-1]
    ck.check("only moved / slightly_moved stay twins at the last level",
             final["twin_blocks"] == [["LP3/slightly_moved", "LP3/moved"]], str(final["twin_blocks"]))
    return ck


if __name__ == "__main__":
    sys.exit(1 if run().failed else 0)
