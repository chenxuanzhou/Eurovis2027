"""Derive the cycle-level data products from the raw voraus-AD parquet (100 Hz).

Needs data/voraus_ad/raw/voraus-ad-dataset-100hz.parquet (or VORAUS_PARQUET=<path>).

Outputs
  data/voraus_ad/cycles/cycles.parquet               one row per cycle (2122): labels, setting, official split,
                                           duration, sampling, leave-setting-out membership
  data/voraus_ad/cycles/action_segments.parquet      one row per (cycle, action): start/end time and progress
  data/voraus_ad/envelope/normal_envelope_grid500.parquet
                                           per channel (all 130) x 500 progress points: mean, std,
                                           scale (the SAFEPROCESS z denominator), q05/q25/q50/q75/q95,
                                           over the 948 official training cycles (setting PRE_A)
  data/voraus_ad/envelope/normal_phase_grid500.csv   modal action per progress point over the training cycles
  data/voraus_ad/signals/grid500/<part>.parquet      the 1174 test cycles (one part per anomaly category plus
                                           normal_test) and a fixed sample of 100 training cycles,
                                           resampled onto the 500-point progress grid for the channels
                                           in config.grid_channels(), plus the action code per point
  data/voraus_ad/signals/grid500/manifest.json       parts, cycles per part, channels, precision
  data/voraus_ad/evidence/records_normal_test.json   evidence records (schema 0.3) for the 419 test cycles
                                           without an anomaly, built exactly like the anomalous ones
  data/voraus_ad/evidence/regeneration_check.json    the 755 anomalous records rebuilt from raw and compared with
                                           the copied SAFEPROCESS records

Resampling follows attribution_bridge._resample: time is normalized per cycle to [0, 1]
and every channel is linearly interpolated onto np.linspace(0, 1, 500), in float64.

The released file is a single 2.3-million-row group, so filtering on read saves nothing;
columns are decoded a few at a time instead, which keeps the peak memory near 1.5 GB.

Run from the repository root:  python pipeline/build_from_raw.py
"""
from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

import config as C  # noqa: I001  (puts pipeline/vendor on sys.path)
import attribution_bridge as AB
from common.parquet_io import trim_mantissa
from voraus_enums import Signals

EPS = AB.EPS
META = ["time", "sample", "anomaly", "category", "setting", "action", "active"]
KB_CHANNELS = [f"{f}_{j}" for f in AB.JOINT_SIGNALS for j in AB.JOINTS] + list(AB.ROBOT_SIGNALS)
QUANTILES = (0.05, 0.25, 0.5, 0.75, 0.95)
BATCH = 16          # channels decoded per read


def log(msg: str) -> None:
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def progress(t: np.ndarray) -> np.ndarray:
    return (t - t.min()) / (t.max() - t.min() + EPS)


class Raw:
    """The raw parquet with rows in (sample, time) order, read a few columns at a time."""

    def __init__(self, path=C.RAW_PARQUET):
        self.pf = pq.ParquetFile(path)
        meta = self.pf.read(columns=META).to_pandas()
        order = np.lexsort((meta["time"].to_numpy(), meta["sample"].to_numpy()))  # stable
        self.order = None if np.array_equal(order, np.arange(len(order))) else order
        self.meta = meta if self.order is None else meta.iloc[order].reset_index(drop=True)
        s = self.meta["sample"].to_numpy()
        starts = np.flatnonzero(np.r_[True, s[1:] != s[:-1]])
        ends = np.r_[starts[1:], len(s)]
        self.slices = {int(s[a]): (int(a), int(b)) for a, b in zip(starts, ends)}
        t = self.meta["time"].to_numpy()
        self.tn = np.empty_like(t)                     # per-cycle progress in [0, 1]
        for a, b in self.slices.values():
            self.tn[a:b] = progress(t[a:b])
        self.action = self.meta["action"].to_numpy()

    def columns(self, names: list[str]):
        """Yield (name, float64 values in (sample, time) order)."""
        for k in range(0, len(names), BATCH):
            batch = names[k:k + BATCH]
            table = self.pf.read(columns=batch)
            for n in batch:
                x = table.column(n).to_numpy().astype(np.float64, copy=False)
                yield n, (x if self.order is None else x[self.order])
            del table

    def resample(self, names: list[str], samples: list[int], grid: np.ndarray,
                 dtype=np.float32) -> np.ndarray:
        """(cycles, channels, grid) on the progress grid, as attribution_bridge._resample does it."""
        out = np.empty((len(samples), len(names), len(grid)), dtype=dtype)
        for j, (_, x) in enumerate(self.columns(names)):
            for i, sid in enumerate(samples):
                a, b = self.slices[sid]
                out[i, j] = np.interp(grid, self.tn[a:b], x[a:b])
        return out

    def actions(self, samples: list[int], grid: np.ndarray) -> np.ndarray:
        """Action code at each grid point (the sample at or just before it, as in attribute())."""
        out = np.empty((len(samples), len(grid)), dtype=np.int8)
        for i, sid in enumerate(samples):
            a, b = self.slices[sid]
            out[i] = self.action[a:b][np.searchsorted(self.tn[a:b], grid, side="right") - 1]
        return out


# ---------------------------------------------------------------------------
def build_cycles(raw: Raw) -> pd.DataFrame:
    lso = json.loads((C.DATA / "splits" / "leave_setting_out.json").read_text(encoding="utf-8"))
    member = {seed: ({int(i) for i in s["fit_cycles"]}, {int(i) for i in s["test_cycles"]})
              for seed, s in lso["seeds"].items()}
    meta = raw.meta
    rows, segs = [], []
    for sid, (a, b) in sorted(raw.slices.items()):
        run = meta.iloc[a:b]
        for col in ("anomaly", "category", "setting"):
            if run[col].nunique() != 1:
                raise ValueError(f"cycle {sid}: {col} not constant")
        t = run["time"].to_numpy()
        tn = raw.tn[a:b]
        dt = np.diff(t)
        row = {
            "sample": sid, "category": int(run["category"].iat[0]),
            "setting": int(run["setting"].iat[0]), "anomaly": bool(run["anomaly"].iat[0]),
            "n_rows": int(b - a), "t_start": float(t.min()), "duration_s": float(t.max() - t.min()),
            "dt_median_s": float(np.median(dt)) if len(dt) else np.nan,
            "active_fraction": float(run["active"].astype(float).mean()),
            "n_actions": int(run["action"].nunique()),
        }
        row["official_split"] = "train" if row["setting"] == C.TRAIN_SETTING else "test"
        for seed, (fit, test) in member.items():
            row[f"lso{seed}"] = "fit" if sid in fit else "test" if sid in test else None
        rows.append(row)
        act = run["action"].to_numpy()
        change = np.flatnonzero(np.r_[True, act[1:] != act[:-1]])
        stop = np.r_[change[1:], len(act)]
        for k, (p, q) in enumerate(zip(change, stop)):
            segs.append({"sample": sid, "segment": k, "action": int(act[p]),
                         "t_start": float(t[p] - t.min()), "t_end": float(t[q - 1] - t.min()),
                         "progress_start": float(tn[p]), "progress_end": float(tn[q - 1]),
                         "n_rows": int(q - p)})
    cycles = pd.DataFrame(rows)
    out = C.DATA / "cycles"
    out.mkdir(parents=True, exist_ok=True)
    cycles.to_parquet(out / "cycles.parquet", index=False, compression="zstd")
    cycles.to_csv(out / "cycles.csv", index=False)
    pd.DataFrame(segs).to_parquet(out / "action_segments.parquet", index=False, compression="zstd")
    log(f"cycles: {len(cycles)} rows, segments: {len(segs)}")
    return cycles


def build_envelope(raw: Raw, train: list[int], grid: np.ndarray) -> dict:
    cols = list(Signals.machine())
    stack = raw.resample(cols, train, grid, np.float64)          # (948, 130, 500), ~0.5 GB
    acts = raw.actions(train, grid)
    mean, std = stack.mean(axis=0), stack.std(axis=0)
    ptp = np.ptp(mean, axis=1, keepdims=True)
    scale = np.maximum(std, 0.05 * np.where(ptp > 0, ptp, 1.0))
    qs = np.quantile(stack, QUANTILES, axis=0)
    del stack
    n_ch, n_g = mean.shape
    f32 = lambda a: a.ravel().astype(np.float32)  # noqa: E731
    env = pd.DataFrame({
        "channel": np.repeat(cols, n_g), "grid_idx": np.tile(np.arange(n_g, dtype=np.int16), n_ch),
        "progress": np.tile(grid.astype(np.float32), n_ch),
        "mean": f32(mean), "std": f32(std), "scale": f32(scale),
        **{f"q{int(q * 100):02d}": f32(qs[k]) for k, q in enumerate(QUANTILES)},
    })
    out = C.DATA / "envelope"
    out.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pandas(env, preserve_index=False), out / "normal_envelope_grid500.parquet",
                   compression="zstd", compression_level=19, use_dictionary=["channel"],
                   use_byte_stream_split=[c for c in env.columns if env[c].dtype == np.float32])
    modal = np.array([np.bincount(acts[:, g], minlength=15).argmax() for g in range(n_g)])
    frac = np.array([(acts[:, g] == modal[g]).mean() for g in range(n_g)])
    pd.DataFrame({"grid_idx": np.arange(n_g), "progress": grid, "modal_action": modal,
                  "modal_fraction": frac.round(4)}).to_csv(out / "normal_phase_grid500.csv", index=False)
    log(f"envelope: {len(train)} training cycles x {n_ch} channels")
    idx = {c: k for k, c in enumerate(cols)}
    # float64 reference for the evidence records, exactly as build_reference computes it
    return {c: {"mean": mean[idx[c]], "scale": scale[idx[c]]} for c in KB_CHANNELS}


def write_part(frames: list[pd.DataFrame], name: str, schema_cols: list[str]) -> dict:
    out = C.DATA / "signals" / "grid500"
    out.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(pd.concat(frames, ignore_index=True), preserve_index=False)
    path = out / f"{name}.parquet"
    # dictionary encoding would block byte_stream_split and triples the size of float columns
    pq.write_table(table, path, compression="zstd", compression_level=19, use_dictionary=False,
                   use_byte_stream_split=schema_cols, row_group_size=50_000)
    mb = path.stat().st_size / 2**20
    if mb > C.MAX_FILE_MB:
        raise RuntimeError(f"{path.name} is {mb:.1f} MB > {C.MAX_FILE_MB} MB; split the part further")
    log(f"  {path.name}: {mb:.1f} MB")
    return {"file": path.name, "megabytes": round(mb, 2)}


def build_grid_signals(raw: Raw, cycles: pd.DataFrame, grid: np.ndarray) -> None:
    cols = C.grid_channels()
    parts: dict[str, list[int]] = {}
    for r in cycles.itertuples():
        if r.anomaly:
            key = f"anomalous_cat{r.category:02d}"
        elif r.official_split == "test":
            key = "normal_test"
        else:
            continue
        parts.setdefault(key, []).append(int(r.sample))
    train = sorted(int(s) for s in cycles.loc[cycles["official_split"] == "train", "sample"])
    rng = np.random.default_rng(C.TRAIN_SAMPLE_SEED)
    parts["normal_train_sample"] = sorted(int(s) for s in rng.choice(
        train, size=min(C.TRAIN_SAMPLE_N, len(train)), replace=False))
    ids = sorted({s for v in parts.values() for s in v})
    pos = {s: i for i, s in enumerate(ids)}
    values = raw.resample(cols, ids, grid, np.float32)            # (1274, 44, 500)
    acts = raw.actions(ids, grid)
    g = np.arange(len(grid), dtype=np.int16)
    manifest = {"grid_n": len(grid), "channels": cols,
                "precision": f"float32 rounded to {C.GRID_KEEP_MANTISSA_BITS} mantissa bits "
                             f"(relative error <= {2.0 ** -(C.GRID_KEEP_MANTISSA_BITS + 1):.1e})",
                "train_sample": {"n": len(parts["normal_train_sample"]), "seed": C.TRAIN_SAMPLE_SEED},
                "parts": {}}
    for name, members in sorted(parts.items()):
        frames = []
        for sid in sorted(members):
            i = pos[sid]
            f = pd.DataFrame(trim_mantissa(values[i], C.GRID_KEEP_MANTISSA_BITS).T, columns=cols)
            f.insert(0, "action", acts[i])
            f.insert(0, "grid_idx", g)
            f.insert(0, "sample", np.int32(sid))
            frames.append(f)
        info = write_part(frames, name, cols)
        manifest["parts"][name] = {**info, "n_cycles": len(members), "samples": sorted(members)}
    (C.DATA / "signals" / "grid500" / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")


def build_records(raw: Raw, ref: dict, cycles: pd.DataFrame, grid: np.ndarray) -> None:
    data = {"time": raw.meta["time"].to_numpy(), "action": raw.action}
    data.update(dict(raw.columns(KB_CHANNELS)))
    df = pd.DataFrame(data)
    test = cycles[cycles["official_split"] == "test"]
    normal_records, rebuilt = [], {}
    for r in test.itertuples():
        a, b = raw.slices[int(r.sample)]
        rec = AB.to_bridge_record(AB.attribute(df.iloc[a:b], ref, grid), sample_id=int(r.sample),
                                  category=int(r.category), setting=int(r.setting))
        rec.pop("_notes", None)
        if r.anomaly:
            rebuilt[int(r.sample)] = rec
        else:
            rec["detector"]["verdict"] = "normal (ground truth; no detector score yet)"
            normal_records.append(rec)
    ev = C.DATA / "evidence"
    (ev / "records_normal_test.json").write_text(json.dumps(normal_records), encoding="utf-8")
    cached = {r["cycle_id"]: r for r in json.loads((ev / "records_anomalous.json").read_text(encoding="utf-8"))}
    diffs = []
    for cid, old in cached.items():
        new = rebuilt.get(cid)
        if new is None:
            diffs.append({"cycle_id": cid, "issue": "missing in raw"})
            continue
        so, sn = old["signature"]["slots"], new["signature"]["slots"]
        worst = max(abs(x - y) for k in so for x, y in zip(so[k], sn.get(k, [np.inf] * 5)))
        diffs.append({
            "cycle_id": cid, "max_abs_slot_diff": round(float(worst), 4),
            "same_top5": [s["signal"] for s in old["attributed_signals"]]
                         == [s["signal"] for s in new["attributed_signals"]],
            "same_dominant_joint": old["localization"]["dominant_joint"] == new["localization"]["dominant_joint"],
        })
    d = pd.DataFrame(diffs)
    summary = {
        "n_cached": len(cached), "n_rebuilt": len(rebuilt),
        "max_abs_slot_diff": float(d["max_abs_slot_diff"].max()),
        "share_same_top5": float(d["same_top5"].mean()),
        "share_same_dominant_joint": float(d["same_dominant_joint"].mean()),
        "note": "slot values are rounded to 3 decimals in the records, so diffs up to 0.001 are rounding",
        "per_cycle": diffs,
    }
    (ev / "regeneration_check.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    log(f"records: {len(normal_records)} normal test; anomalous rebuilt max slot diff "
        f"{summary['max_abs_slot_diff']:.4f}, same top-5 {summary['share_same_top5']:.3f}, "
        f"same dominant joint {summary['share_same_dominant_joint']:.3f}")


def main() -> None:
    if not C.RAW_PARQUET.exists():
        raise SystemExit(f"raw parquet not found: {C.RAW_PARQUET} (see data/voraus_ad/raw/README.md)")
    grid = np.linspace(0, 1, C.GRID_N)
    log("reading meta columns")
    raw = Raw()
    cycles = build_cycles(raw)
    log("normal envelope")
    train = sorted(int(s) for s in cycles.loc[cycles["official_split"] == "train", "sample"])
    ref = build_envelope(raw, train, grid)
    log("grid500 signals")
    build_grid_signals(raw, cycles, grid)
    log("evidence records")
    build_records(raw, ref, cycles, grid)
    log("done")


if __name__ == "__main__":
    main()
