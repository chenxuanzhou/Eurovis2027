"""Check the voraus-AD products against the counts of the voraus-AD paper and the SAFEPROCESS study.

Products that need the raw parquet are reported as PENDING until build_from_raw.py has run.
Run from the repository root:  python pipeline/voraus_ad/validate.py   (or python pipeline/validate.py)
"""
from __future__ import annotations

import json
import sys

import pandas as pd

import config as C  # noqa: I001  (puts pipeline/ on sys.path)
from common.checks import Checker
from common.lattice import check_lattice


def catalog(ck: Checker) -> None:
    d = C.DATA / "catalog"
    n = {f: len(pd.read_csv(d / f)) for f in ("signals.csv", "categories.csv", "variants.csv", "actions.csv")}
    ck.check("catalog sizes", n == {"signals.csv": 130, "categories.csv": 13, "variants.csv": 77, "actions.csv": 15}, str(n))


def evidence_and_splits(ck: Checker) -> dict:
    recs = json.loads((C.DATA / "evidence" / "records_anomalous.json").read_text(encoding="utf-8"))
    cats = pd.Series([r["detector"]["ground_truth_category"] for r in recs]).value_counts().sort_index()
    ck.check("755 anomalous evidence records", len(recs) == 755)
    ck.check("72 anomalous settings", len({r["detector"]["ground_truth_setting"] for r in recs}) == 72)
    lso = json.loads((C.DATA / "splits" / "leave_setting_out.json").read_text(encoding="utf-8"))
    ok = all(set(s["fit_settings"]).isdisjoint(s["test_settings"]) and
             len(s["fit_cycles"]) + len(s["test_cycles"]) == 755 for s in lso["seeds"].values())
    ck.check("leave-setting-out splits are disjoint by setting and cover all 755 cycles", ok)
    return cats.to_dict()


def kb(ck: Checker) -> None:
    d = C.DATA / "kb"
    modes = json.loads((d / "failure_modes.json").read_text(encoding="utf-8"))
    lat = json.loads((d / "refinement_lattice.json").read_text(encoding="utf-8"))
    ck.check("14 failure modes", len(modes) == 14)
    l2 = next(lv for lv in lat["levels"] if lv["id"] == "L2")
    ck.check("4 twin groups in the deployed representation", len(l2["twin_blocks"]) == 4)
    problems = check_lattice(lat)
    ck.check("lattice: each level refines the previous one, blocks contiguous", not problems, "; ".join(problems))


def raw_products(ck: Checker, cats: dict) -> None:
    cyc_path = C.DATA / "cycles" / "cycles.parquet"
    if not cyc_path.exists():
        for name in ("cycles", "action segments", "normal envelope", "grid500 signals",
                     "normal test evidence records", "regeneration check"):
            ck.wait(name, "run pipeline/voraus_ad/build_from_raw.py with the raw parquet")
        return
    cyc = pd.read_parquet(cyc_path)
    ck.check("2122 cycles", len(cyc) == 2122, f"{len(cyc)}")
    train = cyc[cyc["official_split"] == "train"]
    ck.check("948 official training cycles, all anomaly-free",
             len(train) == 948 and not train["anomaly"].any(), f"{len(train)}")
    test = cyc[cyc["official_split"] == "test"]
    ck.check("419 anomaly-free and 755 anomalous test cycles",
             (int((~test["anomaly"]).sum()), int(test["anomaly"].sum())) == (419, 755))
    raw_cats = cyc[cyc["anomaly"]]["category"].value_counts().sort_index().to_dict()
    ck.check("anomalous cycles per category match the evidence records", raw_cats == cats)

    env = pd.read_parquet(C.DATA / "envelope" / "normal_envelope_grid500.parquet")
    ck.check("envelope covers 130 channels x 500 points without gaps",
             len(env) == 130 * C.GRID_N and not env.isna().any().any())
    ck.check("envelope scale >= std", bool((env["scale"] >= env["std"] - 1e-6).all()))

    man = json.loads((C.DATA / "signals" / "grid500" / "manifest.json").read_text(encoding="utf-8"))
    n = 0
    for name, part in man["parts"].items():
        df = pd.read_parquet(C.DATA / "signals" / "grid500" / part["file"])
        n += part["n_cycles"]
        ck.check(f"grid500 {name}: {part['n_cycles']} cycles x {C.GRID_N} rows, no gaps",
                 len(df) == part["n_cycles"] * C.GRID_N and not df.isna().any().any())
    ck.check("grid500 holds every test cycle plus the training sample", n == 1174 + man["train_sample"]["n"])

    normal = json.loads((C.DATA / "evidence" / "records_normal_test.json").read_text(encoding="utf-8"))
    ck.check("419 evidence records for anomaly-free test cycles", len(normal) == 419)
    reg = json.loads((C.DATA / "evidence" / "regeneration_check.json").read_text(encoding="utf-8"))
    ck.check("rebuilt anomalous records match the SAFEPROCESS records",
             reg["n_rebuilt"] == 755 and reg["max_abs_slot_diff"] <= 0.002 and reg["share_same_top5"] >= 0.99,
             f"max slot diff {reg['max_abs_slot_diff']}, same top-5 {reg['share_same_top5']:.3f}")


def run(ck: Checker | None = None) -> Checker:
    ck = ck or Checker("voraus-AD")
    catalog(ck)
    cats = evidence_and_splits(ck)
    kb(ck)
    raw_products(ck, cats)
    return ck


if __name__ == "__main__":
    sys.exit(1 if run().failed else 0)
