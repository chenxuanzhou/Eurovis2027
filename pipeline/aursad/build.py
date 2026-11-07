"""Build the AURSAD products from the extracted samples (no raw data needed).

Inputs (committed, written by extract.py from AURSAD.h5):
  data/aursad/samples.csv, data/aursad/signals/grid500/*.parquet

Outputs (data/aursad/)
  sample_groups.csv             per sample: recording run, session (runs merged where they share recordings),
                                duplicate group, label conflicts, features of the preceding pick-up
  data_quality.json             duplicated recordings and the labels their copies carry
  envelope/normal_envelope_grid500.parquet
                                normal tightening profile per channel and grid point (distinct, conflict-free
                                normal samples): mean, std, scale, q05/q25/q50/q75/q95
  evidence/features_z.csv       per tightening sample and feature: value and robust z against the normal
                                samples of the other sessions
  splits/leave_session_out.json 5 folds x 5 seeds, grouped by session
  kb/failure_modes.json, kb/assumptions.json, kb/fsm.csv, kb/refinement_lattice.json,
  kb/twin_groups.json, kb/evidence_map.json

Run from the repository root:  python pipeline/aursad/build.py
"""
from __future__ import annotations

import json
from collections import Counter

import numpy as np
import pandas as pd

import config as C  # noqa: I001  (puts pipeline/ on sys.path)
import kb_spec as K
from common.lattice import fsm_table, refinement_lattice, twin_resolution
from common.parquet_io import write_compact

FEATURES = ["screw_s", "move_s", "return_s", "current_torque_max", "current_torque_mean", "achieved_torque_final",
            "torque_rise_s", "torque_drops", "fz_mean_screw", "fz_max_screw", "mz_absmax_screw", "acc_rms_screw",
            "z_at_screw_end", "z_travel_screw", "prev_loosen_screw_s", "prev_loosen_torque_max"]
QUANTILES = (0.05, 0.25, 0.5, 0.75, 0.95)


def sample_groups(s: pd.DataFrame) -> pd.DataFrame:
    s = s.sort_values("sample_nr").reset_index(drop=True)
    gap = s["t_start"].to_numpy()[1:] - s["t_end"].to_numpy()[:-1]          # 0.01 s inside a recording
    run = np.r_[0, np.cumsum(np.abs(gap) > C.RUN_GAP_S)]
    s["run"] = run
    first = s.groupby("signal_hash")["sample_nr"].transform("min")
    copies = s.groupby("signal_hash")["sample_nr"].transform("size")
    labels = s.groupby("signal_hash")["label"].agg(lambda x: sorted(set(int(v) for v in x)))
    # sessions: runs that share a recording are one session (union-find over runs)
    parent = list(range(run.max() + 1))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for _, g in s.groupby("signal_hash"):
        rs = sorted(set(g["run"]))
        for r in rs[1:]:
            parent[find(r)] = find(rs[0])
    roots = {r: find(r) for r in range(run.max() + 1)}
    order = {root: k for k, root in enumerate(sorted(set(roots.values())))}
    s["session"] = s["run"].map(lambda r: order[roots[r]])
    prev = s.shift(1)
    is_prev_loosen = (prev["kind"] == "loosening") & (prev["run"] == s["run"]) & (s["kind"] == "tightening")
    out = pd.DataFrame({
        "sample_nr": s["sample_nr"], "kind": s["kind"], "label": s["label"], "run": s["run"], "session": s["session"],
        "duplicate_group": first, "n_copies": copies,
        "label_conflict": s["signal_hash"].map(lambda h: len(labels[h]) > 1),
        "labels_of_copies": s["signal_hash"].map(lambda h: "|".join(map(str, labels[h]))),
        "prev_loosen_screw_s": prev["screw_s"].where(is_prev_loosen),
        "prev_loosen_torque_max": prev["current_torque_max"].where(is_prev_loosen),
    })
    return out


def data_quality(s: pd.DataFrame, g: pd.DataFrame) -> dict:
    t = g[g["kind"] == "tightening"]
    dup = g[g["n_copies"] > 1]
    pairs = dup.groupby("duplicate_group")["labels_of_copies"].first()
    conflict = pairs[pairs.str.contains(r"\|")]
    return {
        "samples": len(g), "tightening": int(len(t)), "loosening": int((g["kind"] == "loosening").sum()),
        "distinct_signal_blocks": int(s["signal_hash"].nunique()),
        "distinct_tightening": int(t["duplicate_group"].nunique()),
        "samples_in_duplicate_groups": int(len(dup)), "duplicate_groups": int(dup["duplicate_group"].nunique()),
        "duplicate_groups_with_conflicting_labels": int(len(conflict)),
        "conflicting_label_sets": {k: int(v) for k, v in conflict.value_counts().sort_index().items()},
        "recording_runs": int(g["run"].nunique()), "sessions": int(g["session"].nunique()),
        "tightening_per_label": {K.LABEL_MODE[int(k)]: int(v) for k, v in t["label"].value_counts().sort_index().items()},
        "distinct_tightening_per_label_of_first_copy": {
            K.LABEL_MODE[int(k)]: int(v) for k, v in t[t["sample_nr"] == t["duplicate_group"]]["label"].value_counts().sort_index().items()},
        "note": "Copies are byte-identical in all 125 sensor columns and timestamps; they come from recording segments "
                "that appear twice in AURSAD.h5. Copies with different labels cannot both be right.",
    }


def features_z(s: pd.DataFrame, g: pd.DataFrame) -> pd.DataFrame:
    d = s.merge(g[["sample_nr", "session", "label_conflict", "duplicate_group", "prev_loosen_screw_s",
                   "prev_loosen_torque_max"]], on="sample_nr")
    t = d[d["kind"] == "tightening"]
    ref_pool = t[(t["label"] == 0) & ~t["label_conflict"] & (t["sample_nr"] == t["duplicate_group"])]
    rows = []
    for sess, block in t.groupby("session"):
        ref = ref_pool[ref_pool["session"] != sess]
        stats = {}
        for f in FEATURES:
            x = ref[f].to_numpy(float)
            x = x[np.isfinite(x)]
            med = float(np.median(x))
            mad = 1.4826 * float(np.median(np.abs(x - med)))
            stats[f] = (med, max(mad, 0.05 * abs(med), 1e-6), len(x))
        for r in block.itertuples(index=False):
            for f in FEATURES:
                v = getattr(r, f)
                med, sc, n = stats[f]
                rows.append({"sample_nr": r.sample_nr, "feature": f, "value": v,
                             "z": round((v - med) / sc, 3) if np.isfinite(v) else np.nan, "reference_n": n})
    return pd.DataFrame(rows)


def envelope(g: pd.DataFrame) -> pd.DataFrame:
    man = json.loads((C.DATA / "signals" / "grid500" / "manifest.json").read_text(encoding="utf-8"))
    chans = man["channels"]
    df = pd.read_parquet(C.DATA / "signals" / "grid500" / man["parts"]["tighten_normal"]["file"])
    ok = set(g[(g["label"] == 0) & ~g["label_conflict"]]["sample_nr"])
    df = df[df["sample_nr"].isin(ok)]
    n = df["sample_nr"].nunique()
    stack = df.sort_values(["sample_nr", "grid_idx"])[chans].to_numpy(np.float64).reshape(n, man["grid_n"], len(chans))
    mean, std = stack.mean(0), stack.std(0)
    ptp = np.ptp(mean, axis=0, keepdims=True)
    scale = np.maximum(std, 0.05 * np.where(ptp > 0, ptp, 1.0))
    qs = np.quantile(stack, QUANTILES, axis=0)
    phase = df[df["sample_nr"] == df["sample_nr"].iloc[0]].sort_values("grid_idx")["phase"].to_numpy()
    out = []
    for c, ch in enumerate(chans):
        out.append(pd.DataFrame({"channel": ch, "grid_idx": np.arange(man["grid_n"], dtype=np.int16), "phase": phase,
                                 "mean": mean[:, c].astype(np.float32), "std": std[:, c].astype(np.float32),
                                 "scale": scale[:, c].astype(np.float32),
                                 **{f"q{int(q * 100):02d}": qs[k, :, c].astype(np.float32) for k, q in enumerate(QUANTILES)},
                                 "n": np.int32(n)}))
    return pd.concat(out, ignore_index=True)


def splits(g: pd.DataFrame) -> dict:
    t = g[g["kind"] == "tightening"]
    sess = t.groupby("session")["label"].value_counts().unstack(fill_value=0)
    out = {"description": "Leave-session-out cross-validation. A session is a recording run, merged with every run "
                          "that shares recordings with it, so duplicated recordings never straddle a fold. Sessions "
                          "are dealt to folds greedily (largest first, seed-dependent order among similar sizes) to "
                          "balance the tightening labels. Value per seed: sample_nr -> fold (loosening samples follow "
                          "their session).",
           "folds": C.CV_FOLDS, "group": "session", "seeds": {}}
    for seed in C.CV_SEEDS:
        rng = np.random.default_rng(seed)
        order = sorted(sess.index, key=lambda k: (-sess.loc[k].sum(), rng.random()))
        load = np.zeros((C.CV_FOLDS, sess.shape[1]))
        fold_of = {}
        for k in order:
            v = sess.loc[k].to_numpy(float)
            cost = [((load[f] + v) / np.maximum(sess.sum().to_numpy(float), 1)).max() for f in range(C.CV_FOLDS)]
            f = int(np.argmin(cost))
            load[f] += v
            fold_of[int(k)] = f
        out["seeds"][str(seed)] = {str(int(r.sample_nr)): fold_of.get(int(r.session), 0) for r in g.itertuples()}
    return out


def knowledge_base(g: pd.DataFrame) -> dict:
    t = g[g["kind"] == "tightening"]
    counts = Counter(K.LABEL_MODE[int(x)] for x in t["label"])
    modes = list(K.MODES)
    columns = {lv["id"]: {m: K.column(m, lv["id"]) for m in modes} for lv in K.LEVELS}
    lat = refinement_lattice(
        "aursad", K.LEVELS, columns, counts,
        description="Isolability refinement chain of the symptom model authored for AURSAD (pipeline/aursad/kb_spec.py). "
                    "Instances are tightening samples as labelled in AURSAD.h5, duplicates included. Normal "
                    "tightening is part of the hypothesis set (null_modes).",
        mode_label={m: K.MODES[m][1] for m in modes}, null_modes=["normal"])
    fsm = fsm_table(K.LEVELS, columns, lat["modes"])
    distinct = Counter(K.LABEL_MODE[int(x)] for x in t[t["sample_nr"] == t["duplicate_group"]]["label"])
    fm = [{"id": m, "name": K.MODES[m][0], "label": K.MODES[m][1], "assumptions": K.MODES[m][3],
           "instances": counts[m], "instances_first_copy_only": distinct[m]} for m in lat["modes"]]
    tg = twin_resolution(lat, fsm)
    for grp in tg:
        grp["note"] = (f"Structural twins from {grp['twins_from']} until {grp['resolved_at']} adds "
                       f"{', '.join(grp['resolving_rows'])}." if grp["resolved_at"] else "No level separates these modes.")
        if set(grp["members"]) == {"damaged_screw", "damaged_plate_thread"}:
            grp["note"] += (" In AURSAD only recurrence at a hole can be checked (pin_to); the screw identity is not "
                            "recorded, so the resolving evidence is only half observable.")
    return {"failure_modes": fm, "fsm": fsm, "lattice": lat, "twin_groups": tg}


def main() -> None:
    s = pd.read_csv(C.DATA / "samples.csv")
    g = sample_groups(s)
    g.to_csv(C.DATA / "sample_groups.csv", index=False)
    (C.DATA / "data_quality.json").write_text(json.dumps(data_quality(s, g), indent=1), encoding="utf-8")
    (C.DATA / "evidence").mkdir(exist_ok=True)
    features_z(s, g).to_csv(C.DATA / "evidence" / "features_z.csv", index=False)
    write_compact(envelope(g), C.DATA / "envelope" / "normal_envelope_grid500.parquet")
    (C.DATA / "splits").mkdir(exist_ok=True)
    (C.DATA / "splits" / "leave_session_out.json").write_text(json.dumps(splits(g), indent=1), encoding="utf-8")
    kb = knowledge_base(g)
    out = C.DATA / "kb"
    out.mkdir(exist_ok=True)
    (out / "failure_modes.json").write_text(json.dumps(kb["failure_modes"], indent=1), encoding="utf-8")
    (out / "assumptions.json").write_text(json.dumps(K.ASSUMPTIONS, indent=1), encoding="utf-8")
    (out / "evidence_map.json").write_text(json.dumps(K.EVIDENCE_MAP, indent=1), encoding="utf-8")
    pd.DataFrame(kb["fsm"]).to_csv(out / "fsm.csv", index=False)
    (out / "refinement_lattice.json").write_text(json.dumps(kb["lattice"], indent=1), encoding="utf-8")
    (out / "twin_groups.json").write_text(json.dumps(kb["twin_groups"], indent=1), encoding="utf-8")
    q = json.loads((C.DATA / "data_quality.json").read_text(encoding="utf-8"))
    print(f"samples {q['samples']}, distinct signal blocks {q['distinct_signal_blocks']}, duplicate groups "
          f"{q['duplicate_groups']} ({q['duplicate_groups_with_conflicting_labels']} with conflicting labels), "
          f"runs {q['recording_runs']}, sessions {q['sessions']}")
    for lv in kb["lattice"]["levels"]:
        print(f"{lv['id']} {lv['label']:20s} blocks={lv['n_blocks']}  twin blocks={lv['twin_blocks']}  nested={len(lv['nested_pairs'])}")


if __name__ == "__main__":
    main()
