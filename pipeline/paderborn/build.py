"""Build the Paderborn products from the extracted measurements (no raw data needed).

Inputs (committed, written by extract.py from the raw .mat files):
  data/paderborn/measurements.csv, data/paderborn/spectra/*.parquet

Outputs (data/paderborn/)
  bearings.csv                  12 bearings: folder class, fact-sheet failure mode, maker, damage summary
  measurement_groups.csv        per measurement: failure mode, measurements with identical signals, quality flag
  evidence/features_z.csv       per measurement and feature: value and robust z against the healthy bearings
                                under the same operating condition, leaving the measurement's own bearing out
  splits/leave_bearing_out.json 4 folds x 5 seeds; each fold holds out one healthy, one outer-ring and one
                                inner-ring bearing
  kb/failure_modes.json, kb/assumptions.json, kb/fsm.csv, kb/refinement_lattice.json,
  kb/twin_groups.json, kb/evidence_map.json

Run from the repository root:  python pipeline/paderborn/build.py
"""
from __future__ import annotations

import json
from collections import Counter

import numpy as np
import pandas as pd

import config as C  # noqa: I001  (puts pipeline/ on sys.path)
import kb_spec as K
from common.lattice import fsm_table, refinement_lattice, twin_resolution

FEATURES = ["vib_rms", "vib_kurtosis", "vib_crest", "env_fr_dB", "env_FTF_dB", "env_BSF_dB", "env_BPFO_dB",
            "env_BPFO2_dB", "env_BPFI_dB", "env_BPFI2_dB", "env_BPFI-fr_dB", "env_BPFI+fr_dB",
            "cur1_rms", "cur2_rms", "cur_BPFO_sb_dB", "cur_BPFI_sb_dB"]


def bearings() -> pd.DataFrame:
    return pd.DataFrame([{"bearing": b, "folder_class": v[0], "mode": v[1], "manufacturer": v[2], "damage": v[3]}
                         for b, v in K.BEARINGS.items()])


def groups(meas: pd.DataFrame) -> pd.DataFrame:
    first = {}
    rows = []
    for r in meas.itertuples():
        f = first.setdefault(r.signal_hash, r.measurement_id)
        unsteady = abs(r.speed_rpm - r.speed_set_rpm) > 0.01 * r.speed_set_rpm
        rows.append({"measurement_id": r.measurement_id, "file": r.file, "bearing": r.bearing,
                     "condition": r.condition, "mode": K.BEARINGS[r.bearing][1],
                     "same_signals_as": "" if f == r.measurement_id else int(f),
                     # mean speed more than 1 % off the set point: the speed was not steady, so the
                     # order-domain spectra of this file are smeared
                     "quality_flag": "unsteady_speed" if unsteady else ""})
    return pd.DataFrame(rows)


def features_z(meas: pd.DataFrame) -> pd.DataFrame:
    healthy = meas[meas["bearing"].map(lambda b: K.BEARINGS[b][1] == "healthy")]
    out = []
    for r in meas.itertuples(index=False):
        ref = healthy[(healthy["condition"] == r.condition) & (healthy["bearing"] != r.bearing)]
        for f in FEATURES:
            x = ref[f].to_numpy(float)
            med = np.nanmedian(x)
            mad = 1.4826 * np.nanmedian(np.abs(x - med))
            scale = max(mad, 0.05 * abs(med), 1e-9)
            v = getattr(r, f) if f.isidentifier() else r[meas.columns.get_loc(f)]
            out.append({"measurement_id": r.measurement_id, "feature": f, "value": v,
                        "z": round(float((v - med) / scale), 3), "reference_n": len(x)})
    return pd.DataFrame(out)


def splits() -> dict:
    by_class: dict[str, list[str]] = {}
    for b, v in K.BEARINGS.items():
        by_class.setdefault(v[0], []).append(b)
    out = {"description": "Leave-bearing-out cross-validation: each of the 4 folds holds out one healthy, one "
                          "outer-ring (KA) and one inner-ring (KI) bearing, so no bearing is seen in training and "
                          "testing. Measurements with identical signals all belong to one bearing, so they stay "
                          "together. Value per seed: bearing -> fold.",
           "folds": 4, "group": "bearing", "seeds": {}}
    for seed in C.CV_SEEDS:
        rng = np.random.default_rng(seed)
        fold = {}
        for cls in sorted(by_class):
            perm = list(rng.permutation(sorted(by_class[cls])))
            for k, b in enumerate(perm):
                fold[str(b)] = k
        out["seeds"][str(seed)] = dict(sorted(fold.items()))
    return out


def knowledge_base(meas: pd.DataFrame) -> dict:
    counts = Counter(K.BEARINGS[b][1] for b in meas["bearing"])
    modes = list(K.MODES)
    columns = {lv["id"]: {m: K.column(m, lv["id"]) for m in modes} for lv in K.LEVELS}
    lat = refinement_lattice(
        "paderborn", K.LEVELS, columns, counts,
        description="Isolability refinement chain of the symptom model authored for the Paderborn subset "
                    "(pipeline/paderborn/kb_spec.py). Instances are measurements (80 per bearing). The healthy "
                    "bearing is part of the hypothesis set (null_modes).",
        mode_label={m: "/".join(sorted(b for b, v in K.BEARINGS.items() if v[1] == m)) for m in modes},
        null_modes=["healthy"])
    fsm = fsm_table(K.LEVELS, columns, lat["modes"])
    fm = [{"id": m, "name": K.MODES[m][0], "damaged_rings": sorted(K.MODES[m][1]),
           "raceway_geometry": sorted(K.MODES[m][2]), "assumptions": K.MODES[m][3],
           "bearings": [b for b, v in K.BEARINGS.items() if v[1] == m],
           "folder_classes": sorted({v[0] for v in K.BEARINGS.values() if v[1] == m}),
           "instances": counts[m]} for m in lat["modes"]]
    tg = twin_resolution(lat, fsm)
    for g in tg:
        g["note"] = (f"Structural twins from {g['twins_from']} until {g['resolved_at']} adds "
                     f"{', '.join(g['resolving_rows'])}." if g["resolved_at"] else
                     "No level separates these modes.")
    return {"failure_modes": fm, "fsm": fsm, "lattice": lat, "twin_groups": tg}


def main() -> None:
    meas = pd.read_csv(C.DATA / "measurements.csv")
    bearings().to_csv(C.DATA / "bearings.csv", index=False)
    groups(meas).to_csv(C.DATA / "measurement_groups.csv", index=False)
    (C.DATA / "evidence").mkdir(exist_ok=True)
    features_z(meas).to_csv(C.DATA / "evidence" / "features_z.csv", index=False)
    (C.DATA / "splits").mkdir(exist_ok=True)
    (C.DATA / "splits" / "leave_bearing_out.json").write_text(json.dumps(splits(), indent=1), encoding="utf-8")
    kb = knowledge_base(meas)
    out = C.DATA / "kb"
    out.mkdir(exist_ok=True)
    (out / "failure_modes.json").write_text(json.dumps(kb["failure_modes"], indent=1), encoding="utf-8")
    (out / "assumptions.json").write_text(json.dumps(K.ASSUMPTIONS, indent=1), encoding="utf-8")
    (out / "evidence_map.json").write_text(json.dumps(K.EVIDENCE_MAP, indent=1), encoding="utf-8")
    pd.DataFrame(kb["fsm"]).to_csv(out / "fsm.csv", index=False)
    (out / "refinement_lattice.json").write_text(json.dumps(kb["lattice"], indent=1), encoding="utf-8")
    (out / "twin_groups.json").write_text(json.dumps(kb["twin_groups"], indent=1), encoding="utf-8")
    print(f"measurements: {len(meas)} from {meas['bearing'].nunique()} bearings; "
          f"identical-signal duplicates: {int(meas['signal_hash'].duplicated().sum())}")
    for lv in kb["lattice"]["levels"]:
        print(f"{lv['id']} {lv['label']:22s} blocks={lv['n_blocks']}  twin blocks={lv['twin_blocks']}")


if __name__ == "__main__":
    main()
