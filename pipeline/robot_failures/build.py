"""Build every product of the UCI Robot Execution Failures data (Lopes & Camarinha-Matos, 1999).

Inputs: data/robot_failures/raw/lp1.data ... lp5.data (committed; CC BY 4.0).

Outputs (data/robot_failures/)
  instances.csv               one row per instance (463): id, problem, position in its file, label, mode,
                              window id and the other instances with identical readings
  windows.csv                 the 251 distinct readings and their label in each problem (LP3 relabels the
                              LP2 windows, LP5 pools the LP2 and LP4 windows)
  signals.csv                 the 15 x 6 force/torque readings of every instance (long format)
  envelope.csv                normal profile per problem, step and channel: mean, std, scale, n
  evidence/slots.csv          per instance and channel: z_peak, z_signed, z_step, z_std against the
                              normal profile of its problem (leave-one-out for normal instances)
  splits/grouped_cv.json      5 seeds x 5 folds, grouped by window, stratified by label
  kb/failure_modes.json       21 modes (16 failure classes + the normal class of each problem)
  kb/assumptions.json         the assumptions the symptom model rests on
  kb/fsm.csv                  full fault signature matrix (rows by evidence level, columns = modes)
  kb/refinement_lattice.json  isolability refinement chain L0-L6 (schema refinement-lattice/1)
  kb/twin_groups.json         every twin block, the level that splits it and the rows that do

Run from the repository root:  python pipeline/robot_failures/build.py
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter

import numpy as np
import pandas as pd

import config as C  # noqa: I001  (puts pipeline/ on sys.path)
import kb_spec as K
from common.lattice import fsm_table, refinement_lattice, twin_resolution


def read_raw() -> list[dict]:
    rows = []
    for k, problem in enumerate(K.PROBLEMS, start=1):
        path = C.RAW / f"lp{k}.data"
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != C.RAW_SHA256[path.name]:
            raise SystemExit(f"{path.name}: sha256 {digest} differs from the verified copy")
        toks = path.read_text(encoding="ascii").split()
        i, n = 0, 0
        while i < len(toks):
            label = toks[i]
            values = np.array([int(t) for t in toks[i + 1:i + 1 + C.STEPS * 6]], dtype=np.int32)
            if values.size != C.STEPS * 6:
                raise SystemExit(f"{path.name}: instance {n + 1} has {values.size} values")
            n += 1
            mode = next(m for m, spec in K.MODES.items() if spec[0] == problem and spec[1] == label)
            rows.append({"instance_id": f"{problem}-{n:03d}", "problem": problem, "position": n,
                         "label": label, "mode": mode, "normal": label == K.NORMAL_LABEL[problem],
                         "values": values.reshape(C.STEPS, 6)})
            i += 1 + C.STEPS * 6
        if n != C.EXPECTED[problem]:
            raise SystemExit(f"{problem}: {n} instances, expected {C.EXPECTED[problem]}")
    return rows


PRIMARY = ("LP1", "LP2", "LP4", "LP3", "LP5")   # the problem whose label stratifies a shared window


def windows(rows: list[dict]) -> pd.DataFrame:
    """Give identical 15 x 6 readings one window id: the five files reuse the same windows.

    LP3 relabels the LP2 windows by where the part ended up, and LP5 pools the LP2 and LP4 windows
    under a location/direction taxonomy, so the 463 instances hold 251 distinct windows.
    """
    first: dict[bytes, str] = {}
    for r in rows:
        key = r["values"].tobytes()
        if key not in first:
            first[key] = f"W{len(first) + 1:03d}"
        r["window_id"] = first[key]
    members: dict[str, list[dict]] = {}
    for r in rows:
        members.setdefault(r["window_id"], []).append(r)
    for r in rows:
        r["shared_with"] = ";".join(o["instance_id"] for o in members[r["window_id"]] if o is not r)
    cross = []
    for wid, ms in members.items():
        row = {"window_id": wid}
        for p in K.PROBLEMS:
            labels = [m["label"] for m in ms if m["problem"] == p]
            row[p] = "|".join(labels) if labels else ""
        row["primary"] = next(p for p in PRIMARY if row[p])
        cross.append(row)
    return pd.DataFrame(cross)


def envelope(rows: list[dict]) -> tuple[pd.DataFrame, dict]:
    out, prof = [], {}
    for problem in K.PROBLEMS:
        x = np.stack([r["values"] for r in rows if r["problem"] == problem and r["normal"]]).astype(float)
        mean, std = x.mean(0), x.std(0)
        ptp = np.ptp(mean, axis=0)
        scale = np.maximum(np.maximum(std, 0.05 * ptp), C.SCALE_FLOOR)
        prof[problem] = (x, scale)
        for t in range(C.STEPS):
            for c, ch in enumerate(C.CHANNELS):
                out.append({"problem": problem, "step": t, "channel": ch, "mean": round(mean[t, c], 4),
                            "std": round(std[t, c], 4), "scale": round(scale[t, c], 4), "n": len(x)})
    return pd.DataFrame(out), prof


def slots(rows: list[dict], prof: dict) -> pd.DataFrame:
    """z against the normal profile; a normal instance is scored against the others (leave-one-out)."""
    out = []
    third = C.STEPS // 3
    normal_idx = Counter()
    for r in rows:
        normals, scale = prof[r["problem"]]
        if r["normal"]:
            k = normal_idx[r["problem"]]
            normal_idx[r["problem"]] += 1
            others = np.delete(normals, k, axis=0)
            mean = others.mean(0)
            std = others.std(0)
            scale = np.maximum(np.maximum(std, 0.05 * np.ptp(mean, axis=0)), C.SCALE_FLOOR)
        else:
            mean = normals.mean(0)
        z = (r["values"] - mean) / scale
        for c, ch in enumerate(C.CHANNELS):
            zc = z[:, c]
            out.append({"instance_id": r["instance_id"], "channel": ch,
                        "z_peak": round(float(np.abs(zc).max()), 3),
                        "z_signed": round(float(zc.mean()), 3),
                        "z_step": round(float(zc[-third:].mean() - zc[:third].mean()), 3),
                        "z_std": round(float(zc.std()), 3)})
    return pd.DataFrame(out)


def splits(rows: list[dict], cross: pd.DataFrame) -> dict:
    out = {"description": "Five-fold cross-validation repeated over five seeds, grouped by window: every instance "
                          "that shares a window (identical readings, see windows.csv) falls in the same fold, so "
                          "no reading is seen in training and testing at once, even across problems. Windows are "
                          "stratified by their label in the primary problem (LP1, LP2 or LP4; LP3 and LP5 reuse "
                          "those windows): the windows of each label are shuffled and dealt to the folds in turn. "
                          "The data carry no session information, so folds cannot be grouped beyond identical "
                          "readings. Value per seed: instance id -> fold.",
           "folds": C.CV_FOLDS, "group": "window_id", "seeds": {}}
    strata: dict[str, list[str]] = {}
    for w in cross.itertuples():
        strata.setdefault(f"{w.primary}:{getattr(w, w.primary).split('|')[0]}", []).append(w.window_id)
    for seed in C.CV_SEEDS:
        rng = np.random.default_rng(seed)
        fold_of_window = {}
        for stratum in sorted(strata):
            wids = list(strata[stratum])
            rng.shuffle(wids)
            start = int(rng.integers(C.CV_FOLDS))       # spreads the remainders over the folds
            for j, wid in enumerate(wids):
                fold_of_window[wid] = (start + j) % C.CV_FOLDS
        out["seeds"][str(seed)] = {r["instance_id"]: fold_of_window[r["window_id"]] for r in rows}
    return out


def knowledge_base(rows: list[dict]) -> dict:
    counts = Counter(r["mode"] for r in rows)
    modes = list(K.MODES)
    columns = {lv["id"]: {m: K.column(m, lv["id"]) for m in modes} for lv in K.LEVELS}
    lat = refinement_lattice(
        "robot_failures", K.LEVELS, columns, counts,
        description="Isolability refinement chain of the symptom model authored for the UCI Robot Execution "
                    "Failures data (pipeline/robot_failures/kb_spec.py). Level L1 is the task context, so modes "
                    "of different learning problems are never confused; the structure that matters is inside "
                    "each problem. The normal class of each problem is part of the hypothesis set (null_modes).",
        mode_label={m: f"{K.MODES[m][0]}:{K.MODES[m][1]}" for m in modes},
        null_modes=[m for m in modes if K.MODES[m][3] == "normal"])
    fsm = fsm_table(K.LEVELS, columns, lat["modes"])
    fm = [{"id": m, "problem": K.MODES[m][0], "problem_description": K.PROBLEMS[K.MODES[m][0]],
           "label": K.MODES[m][1], "name": K.MODES[m][2], "kind": K.MODES[m][3],
           "push_from_or_payload": sorted(K.MODES[m][4]), "contact": sorted(K.MODES[m][5]),
           "time_course": K.MODES[m][6], "assumptions": K.MODES[m][7], "instances": counts[m]}
          for m in lat["modes"]]
    groups = twin_resolution(lat, fsm)
    for g in groups:
        g["problem"] = K.MODES[g["members"][0]][0]
        g["note"] = ("No level of the knowledge base separates these modes: they differ only in magnitude (A5), "
                     "so only a quantitative threshold learned from data can tell them apart."
                     if g["resolved_at"] is None else
                     f"Structural twins from {g['twins_from']} until {g['resolved_at']} adds "
                     f"{', '.join(g['resolving_rows'])}.")
    return {"failure_modes": fm, "fsm": fsm, "lattice": lat, "twin_groups": groups}


def main() -> None:
    rows = read_raw()
    C.DATA.mkdir(parents=True, exist_ok=True)
    cross = windows(rows)
    cross.to_csv(C.DATA / "windows.csv", index=False)
    inst = pd.DataFrame([{k: v for k, v in r.items() if k != "values"} for r in rows])
    inst.to_csv(C.DATA / "instances.csv", index=False)
    sig = pd.DataFrame([{"instance_id": r["instance_id"], "step": t,
                         **{ch: int(r["values"][t, c]) for c, ch in enumerate(C.CHANNELS)}}
                        for r in rows for t in range(C.STEPS)])
    sig.to_csv(C.DATA / "signals.csv", index=False)
    env, prof = envelope(rows)
    env.to_csv(C.DATA / "envelope.csv", index=False)
    (C.DATA / "evidence").mkdir(exist_ok=True)
    slots(rows, prof).to_csv(C.DATA / "evidence" / "slots.csv", index=False)
    (C.DATA / "splits").mkdir(exist_ok=True)
    (C.DATA / "splits" / "grouped_cv.json").write_text(json.dumps(splits(rows, cross), indent=1), encoding="utf-8")

    kb = knowledge_base(rows)
    out = C.DATA / "kb"
    out.mkdir(exist_ok=True)
    (out / "failure_modes.json").write_text(json.dumps(kb["failure_modes"], indent=1), encoding="utf-8")
    (out / "assumptions.json").write_text(json.dumps(K.ASSUMPTIONS, indent=1), encoding="utf-8")
    pd.DataFrame(kb["fsm"]).to_csv(out / "fsm.csv", index=False)
    (out / "refinement_lattice.json").write_text(json.dumps(kb["lattice"], indent=1), encoding="utf-8")
    (out / "twin_groups.json").write_text(json.dumps(kb["twin_groups"], indent=1), encoding="utf-8")

    print(f"instances: {len(rows)}  ({dict(Counter(r['problem'] for r in rows))}), distinct windows: {len(cross)}")
    for lv in kb["lattice"]["levels"]:
        print(f"{lv['id']} {lv['label']:18s} blocks={lv['n_blocks']:2d}  twin blocks={len(lv['twin_blocks']):2d}  "
              f"instances in a twin block={lv['instances_with_true_mode_in_twin_block']}")
    for g in kb["twin_groups"]:
        print(f"  {g['twins_from']}->{g['resolved_at']}: {g['members']}")


if __name__ == "__main__":
    main()
