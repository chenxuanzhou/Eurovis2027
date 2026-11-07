"""Copy the SAFEPROCESS 2027 evidence records and write the leave-setting-out splits.

Outputs
  data/voraus_ad/evidence/records_anomalous.json   755 evidence records (schema 0.3), one per anomalous cycle
  data/voraus_ad/evidence/unread_features.json     per-cycle statistics of the channels the retrieval never reads
  data/voraus_ad/evidence/payload_torque.json      carried-payload torque measured from normal cycles
  data/voraus_ad/evidence/SOURCE.json              where the three files came from (repository + commit + sha256)
  data/voraus_ad/splits/leave_setting_out.json     the five grouped 50/50 splits (seeds 0-4) over the 755 cycles

The records are derived data of the SAFEPROCESS 2027 study and are copied byte for
byte; `cycle_id` equals the voraus-AD `sample` id. The splits reproduce
`repair._grouped_split` exactly and are checked against the split sizes the study
reports in results/repair_results.json.

Run from the repository root:  python pipeline/build_evidence.py
"""
from __future__ import annotations

import hashlib
import json
import random
import shutil
from collections import Counter, defaultdict

import config as C

EVIDENCE = C.DATA / "evidence"
SPLITS = C.DATA / "splits"
COPIES = {
    "data/records_cache.json": "records_anomalous.json",
    "data/repair_features.json": "unread_features.json",
    "data/payload_torque.json": "payload_torque.json",
}
# (seed, n_fit, n_test) as reported by the SAFEPROCESS study (repair_results.json -> per_seed)
REPORTED_SIZES = {0: (359, 396), 1: (363, 392), 2: (341, 414), 3: (391, 364), 4: (352, 403)}


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def grouped_split(ids, cat_of, set_of, seed):
    """Leave-setting-out 50/50 split stratified by category.

    Identical to repair._grouped_split in the SAFEPROCESS repository: every
    setting (one physical fault instantiation) lands wholly in FIT or in TEST;
    a category with a single setting alternates side by seed.
    """
    rng = random.Random(seed)
    by_cat = defaultdict(set)
    for i in ids:
        by_cat[cat_of[i]].add(set_of[i])
    fit_sets, test_sets = set(), set()
    for cat, settings in sorted(by_cat.items()):
        s = sorted(settings)
        rng.shuffle(s)
        if len(s) == 1:
            (fit_sets if (seed + cat) % 2 == 0 else test_sets).add(s[0])
            continue
        k = max(1, len(s) // 2)
        fit_sets |= set(s[:k])
        test_sets |= set(s[k:])
    fit = [i for i in ids if set_of[i] in fit_sets]
    test = [i for i in ids if set_of[i] in test_sets]
    return fit, test, sorted(fit_sets), sorted(test_sets)


def copy_records() -> list[dict]:
    if not C.SNIS_REPO.exists():
        raise SystemExit(f"SAFEPROCESS repository not found at {C.SNIS_REPO}; set SNIS_REPO.")
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    source = {"repository": "https://github.com/chenxuanzhou/Structural-Non-Isolability-in-Knowledge-Based-Robot-Fault-Diagnosis",
              "commit": C.SNIS_COMMIT, "files": {}}
    for src, dst in COPIES.items():
        shutil.copyfile(C.SNIS_REPO / src, EVIDENCE / dst)
        source["files"][dst] = {"copied_from": src, "sha256": sha256(EVIDENCE / dst)}
    (EVIDENCE / "SOURCE.json").write_text(json.dumps(source, indent=2), encoding="utf-8")
    return json.loads((EVIDENCE / "records_anomalous.json").read_text(encoding="utf-8"))


def write_splits(records: list[dict]) -> None:
    ids = [r["cycle_id"] for r in records]
    cat_of = {r["cycle_id"]: r["detector"]["ground_truth_category"] for r in records}
    set_of = {r["cycle_id"]: r["detector"]["ground_truth_setting"] for r in records}
    out = {
        "description": "Leave-setting-out 50/50 splits of the 755 anomalous cycles, stratified by "
                       "category; identical to repair._grouped_split (SAFEPROCESS 2027). Use them for "
                       "every learned component (classifier, conformal calibration, certificates).",
        "unit": "cycle ids are voraus-AD sample ids",
        "n_cycles": len(ids),
        "n_settings": len(set(set_of.values())),
        "seeds": {},
    }
    for seed in C.LSO_SEEDS:
        fit, test, fit_sets, test_sets = grouped_split(ids, cat_of, set_of, seed)
        assert (len(fit), len(test)) == REPORTED_SIZES[seed], (seed, len(fit), len(test))
        missing_fit = sorted({cat_of[i] for i in ids} - {cat_of[i] for i in fit})
        missing_test = sorted({cat_of[i] for i in ids} - {cat_of[i] for i in test})
        out["seeds"][str(seed)] = {
            "fit_settings": fit_sets, "test_settings": test_sets,
            "fit_cycles": sorted(fit), "test_cycles": sorted(test),
            "categories_absent_from_fit": missing_fit,
            "categories_absent_from_test": missing_test,
        }
    SPLITS.mkdir(parents=True, exist_ok=True)
    (SPLITS / "leave_setting_out.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    per_cat = Counter(cat_of.values())
    settings_per_cat = Counter(cat_of[next(i for i in ids if set_of[i] == s)] for s in set(set_of.values()))
    print(f"{len(ids)} anomalous cycles, {out['n_settings']} settings; split sizes match the study")
    print("cycles per category:  ", dict(sorted(per_cat.items())))
    print("settings per category:", dict(sorted(settings_per_cat.items())))


def main() -> None:
    write_splits(copy_records())


if __name__ == "__main__":
    main()
