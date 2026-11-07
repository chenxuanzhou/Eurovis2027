"""Extract the per-sample products of AURSAD from the raw AURSAD.h5 (Leporowski et al., 2021).

Self-contained (numpy, pandas, pyarrow, h5py) so it can run wherever the 6.4 GB file is:

    python pipeline/aursad/extract.py --h5 /path/to/AURSAD.h5 --out data/aursad

The file is a pandas "fixed" HDF5 store (key complete_data, 6,249,074 rows at 100 Hz, blocks of
float64 / int64 / uint8 / int32 columns). It is read in row chunks with h5py, so memory stays
below 1.5 GB. Writes, under --out:

  samples.csv                   one row per sample (4,094): label, kind (tightening / loosening), pins,
                                recording run, timing of the three phases, screwdriver and
                                robot-side summary features, and a hash of the signal block
  signals/grid500/<part>.parquet   tightening samples on a phase-aligned 500-point grid
                                (150 points moving to the hole, 250 screwdriving, 100 returning
                                home), 20 channels, float32 rounded to 12 mantissa bits; one part
                                per label; samples whose signals duplicate an earlier sample are
                                stored once (samples.csv says which)
  signals/grid500/manifest.json parts, samples per part, channels, phase layout

Phases come from the screwdriver registers: the tightening (or loosening) command pulse
(output_bit_register_67 / _66) starts screwdriving, the end of the last busy period
(output_bit_register_70) after it ends screwdriving.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

KEY = "complete_data"
LABELS = {0: "normal", 1: "damaged_screw", 2: "extra_component", 3: "missing_screw",
          4: "damaged_plate_thread", 5: "loosening"}
PHASE_POINTS = (150, 250, 100)          # move to hole, screwdriving, return home
GRID_N = sum(PHASE_POINTS)
GRID_CHANNELS = [
    "output_double_register_25",        # current torque of the screwdriver (N m)
    "output_double_register_24",        # achieved torque of the screwdriver (N m)
    "actual_TCP_pose_2",                # tool z (m)
    "actual_TCP_speed_2",               # tool z speed (m/s)
    *[f"actual_TCP_force_{i}" for i in range(6)],   # wrist force (N) and torque (N m) estimate
    *[f"actual_current_{i}" for i in range(6)],     # joint currents (A)
    *[f"actual_tool_accelerometer_{i}" for i in range(3)],
    "actual_robot_current",
]
KEEP_BITS = 12
CHUNK = 300_000


def trim_mantissa(x: np.ndarray, keep_bits: int = KEEP_BITS) -> np.ndarray:
    drop = 23 - keep_bits
    bits = np.ascontiguousarray(x, dtype=np.float32).view(np.uint32)
    rounded = (bits + np.uint32(1 << (drop - 1))) & np.uint32((0xFFFFFFFF << drop) & 0xFFFFFFFF)
    return rounded.view(np.float32)


def runs(x: np.ndarray) -> list[tuple[int, int]]:
    """[start, stop) of every run of True."""
    d = np.diff(np.r_[0, x.astype(np.int8), 0])
    return list(zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)))


def phase_bounds(cmd: np.ndarray, busy: np.ndarray) -> tuple[int, int, bool]:
    """(start of screwdriving, end of screwdriving, command found)."""
    n = len(busy)
    pulses = np.flatnonzero(cmd)
    if len(pulses):
        t0 = int(pulses[0])
    else:                                   # fall back to the longest busy period
        rs = runs(busy)
        t0 = max(rs, key=lambda r: r[1] - r[0])[0] if rs else 0
    after = [r for r in runs(busy) if r[1] > t0]
    t1 = int(after[-1][1]) if after else t0
    return t0, min(max(t1, t0), n), bool(len(pulses))


def phase_grid(x: np.ndarray, bounds: list[tuple[int, int]]) -> np.ndarray:
    """Resample x (rows x channels) piecewise: each phase onto its share of the grid."""
    out = []
    for (a, b), m in zip(bounds, PHASE_POINTS):
        seg = x[a:b]
        if len(seg) == 0:
            seg = x[min(a, len(x) - 1):min(a, len(x) - 1) + 1]
        if len(seg) == 1:
            out.append(np.repeat(seg, m, axis=0))
            continue
        src = np.linspace(0.0, 1.0, len(seg))
        dst = np.linspace(0.0, 1.0, m)
        out.append(np.stack([np.interp(dst, src, seg[:, c]) for c in range(seg.shape[1])], axis=1))
    return np.vstack(out)


def summarize(sig: dict[str, np.ndarray], t0: int, t1: int, fs: float = 100.0) -> dict:
    n = len(sig["output_double_register_25"])
    cur = sig["output_double_register_25"]
    ach = sig["output_double_register_24"]
    tgt = sig["output_double_register_26"]
    target = float(np.max(tgt)) if len(tgt) else np.nan
    scr = slice(t0, max(t1, t0 + 1))
    cur_s = cur[scr]
    rise = np.flatnonzero(cur_s >= 0.5 * target) if target > 0 else np.array([], int)
    drops = np.diff(cur_s)
    z = sig["actual_TCP_pose_2"]
    fz = sig["actual_TCP_force_2"]
    mz = sig["actual_TCP_force_5"]
    acc = np.stack([sig[f"actual_tool_accelerometer_{i}"] for i in range(3)], axis=1)
    acc_s = acc[scr] - acc[scr].mean(0)
    return {
        "n_rows": n, "duration_s": n / fs,
        "move_s": t0 / fs, "screw_s": (t1 - t0) / fs, "return_s": (n - t1) / fs,
        "target_torque": round(target, 4),
        "achieved_torque_final": round(float(ach[-1]), 4),
        "achieved_torque_max": round(float(ach.max()), 4),
        "current_torque_max": round(float(cur_s.max()), 4),
        "current_torque_mean": round(float(cur_s.mean()), 4),
        "torque_rise_s": round(float(rise[0] / fs), 3) if len(rise) else np.nan,
        "torque_drops": int(np.sum(drops < -0.05)),          # sudden losses of torque (slips)
        "z_min": round(float(z.min()), 5), "z_at_screw_end": round(float(z[max(t1 - 1, 0)]), 5),
        "z_travel_screw": round(float(z[scr].max() - z[scr].min()), 5),
        "fz_mean_screw": round(float(fz[scr].mean()), 3), "fz_max_screw": round(float(fz[scr].max()), 3),
        "mz_absmax_screw": round(float(np.abs(mz[scr]).max()), 4),
        "acc_rms_screw": round(float(np.sqrt((acc_s ** 2).sum(1).mean())), 5),
        "joint_temp_mean": round(float(np.mean([sig[f"joint_temperatures_{i}"].mean() for i in range(6)])), 3),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--h5", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    (out / "signals" / "grid500").mkdir(parents=True, exist_ok=True)

    g = h5py.File(args.h5, "r")[KEY]
    items = {b: [x.decode() for x in g[f"block{b}_items"][:]] for b in range(4)}
    sn = g["block3_values"][:, 0]
    n = len(sn)
    if np.any(np.diff(sn) < 0):
        raise SystemExit("sample_nr is not sorted")
    b2 = pd.DataFrame(g["block2_values"][:], columns=items[2])
    b0 = pd.DataFrame(g["block0_values"][:], columns=items[0]).astype(bool)
    starts = np.r_[0, np.flatnonzero(np.diff(sn)) + 1]
    stops = np.r_[starts[1:], n]
    need = sorted(set(GRID_CHANNELS) | {"timestamp", "output_double_register_26", "actual_TCP_force_5"}
                  | {f"joint_temperatures_{i}" for i in range(6)})
    col = {c: items[1].index(c) for c in need}
    ds = g["block1_values"]

    rows, grids, gid, hashes = [], [], [], {}

    def sample_blocks():
        """Yield (row start, row stop, rows of block1) sample by sample, reading whole samples in chunks."""
        i = 0
        while i < len(starts):
            j = i + 1
            while j < len(starts) and stops[j] - starts[i] <= CHUNK:
                j += 1
            lo = starts[i]
            block = ds[lo:stops[j - 1]]
            for k in range(i, j):
                yield starts[k], stops[k], block[starts[k] - lo:stops[k] - lo]
            i = j

    for a, b, blk in sample_blocks():
        s = int(sn[a])
        meta = b2.iloc[a:b]
        bits = b0.iloc[a:b]
        label = int(meta["label"].iat[0])
        kind = "loosening" if label == 5 else "tightening"
        cmd = bits["output_bit_register_66" if kind == "loosening" else "output_bit_register_67"].to_numpy()
        t0, t1, found = phase_bounds(cmd, bits["output_bit_register_70"].to_numpy())
        h = hashlib.sha1(np.ascontiguousarray(blk[:, 1:]).tobytes()).hexdigest()
        sig = {c: blk[:, col[c]] for c in need}
        row = {"sample_nr": s, "label": label, "label_name": LABELS[label], "kind": kind,
               "pin_to": int(meta["output_int_register_25"].max()), "pin_from": int(meta["output_int_register_26"].max()),
               "t_start": round(float(blk[0, col["timestamp"]]), 3), "t_end": round(float(blk[-1, col["timestamp"]]), 3),
               "command_found": found,
               **summarize(sig, t0, t1), "signal_hash": h[:16]}
        first = hashes.setdefault(h, s)
        row["same_signals_as"] = first if first != s else ""
        rows.append(row)
        if kind == "tightening" and first == s:
            x = np.stack([sig[c] for c in GRID_CHANNELS], axis=1)
            grids.append(trim_mantissa(phase_grid(x, [(0, t0), (t0, t1), (t1, b - a)]).astype(np.float32), KEEP_BITS))
            gid.append((s, label))
    samples = pd.DataFrame(rows)
    samples.to_csv(out / "samples.csv", index=False)

    phase = np.repeat(np.arange(3, dtype=np.int8), PHASE_POINTS)
    gidx = np.arange(GRID_N, dtype=np.int16)
    manifest = {"grid_n": GRID_N, "phase_points": dict(zip(("move", "screw", "return"), PHASE_POINTS)),
                "channels": GRID_CHANNELS, "precision": f"float32 rounded to {KEEP_BITS} mantissa bits",
                "parts": {}}
    for label in sorted({lab for _, lab in gid}):
        name = f"tighten_{LABELS[label]}"
        frames = []
        for (s, lab), arr in zip(gid, grids):
            if lab != label:
                continue
            f = pd.DataFrame(arr, columns=GRID_CHANNELS)
            f.insert(0, "phase", phase)
            f.insert(0, "grid_idx", gidx)
            f.insert(0, "sample_nr", np.int32(s))
            frames.append(f)
        path = out / "signals" / "grid500" / f"{name}.parquet"
        pq.write_table(pa.Table.from_pandas(pd.concat(frames, ignore_index=True), preserve_index=False), path,
                       compression="zstd", compression_level=19, use_dictionary=False,
                       use_byte_stream_split=GRID_CHANNELS, row_group_size=50_000)
        manifest["parts"][name] = {"file": path.name, "megabytes": round(path.stat().st_size / 2**20, 2),
                                   "n_samples": len(frames), "samples": sorted(int(s) for s, lab in gid if lab == label)}
    (out / "signals" / "grid500" / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"samples: {len(samples)}, distinct signal blocks: {samples['signal_hash'].nunique()}, "
          f"tightening grids: {len(grids)}")
    for k, v in manifest["parts"].items():
        print(f"  {k}: {v['n_samples']} samples, {v['megabytes']} MB")


if __name__ == "__main__":
    main()
