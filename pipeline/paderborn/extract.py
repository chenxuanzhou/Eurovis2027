"""Extract per-measurement features and spectra from the Paderborn bearing .mat files (KAt-DataCenter).

Self-contained (numpy, scipy, pandas, pyarrow) so it can run wherever the raw files are:

    python pipeline/paderborn/extract.py --raw /path/to/paderborn --out data/paderborn [--work tmpdir] [--budget 150]

--raw holds one folder per bearing (K001, KA04, ...) with the 80 files N{09,15}_M{01,07}_F{04,10}_<code>_<1..20>.mat.
Each file is processed once and cached in --work, so the script can be re-run until every file is done
(--budget stops it after that many seconds; it prints how many files remain). When all are cached it writes:

  measurements.csv                      one row per file: bearing, operating condition, measured speed,
                                        torque, force and temperature, the characteristic frequencies of
                                        the bearing, vibration and current features, and a signal hash
  spectra/envelope_orders.parquet       envelope spectrum of the vibration, 0-12 shaft orders in 0.01 steps
  spectra/current_sidebands.parquet     phase-current spectrum around the supply frequency, offsets of
                                        -12..+12 shaft orders in 0.02 steps, in dB re the fundamental

Signal processing (per file): vibration band-passed 2-16 kHz by FFT masking, Hilbert envelope, amplitude
spectrum of the envelope (4 s, 0.25 Hz resolution) resampled to shaft orders. Peak levels at a
characteristic frequency are the maximum within +-1.5 % of it, in dB above the median level of the
surrounding +-5 Hz (outside +-1.5 %). The supply frequency is the largest peak of phase current 1 between
10 and 250 Hz.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import scipy.io as sio
from scipy.stats import kurtosis

FS = 64_000
BAND = (2_000.0, 16_000.0)
ORDERS = np.round(np.arange(0, 12.0001, 0.01), 2)
OFFSETS = np.round(np.arange(-12, 12.0001, 0.02), 2)
N_BALLS, BALL_D = 8, 6.75
PITCH_D = {"FAG": 28.55}            # other manufacturers in this subset: 29.05 mm (fact sheets)
FACT = {                            # manufacturer per bearing, from the fact sheets
    "K001": "IBU", "K002": "IBU", "K003": "IBU", "K004": "IBU", "KA04": "FAG", "KA15": "FAG", "KA16": "MTK",
    "KA22": "IBU/IBB", "KI04": "MTK", "KI14": "MTK", "KI16": "FAG", "KI18": "MTK",
}
NAME = re.compile(r"N(\d\d)_M(\d\d)_F(\d\d)_(K[A-Z]?\d\d+)_(\d+)\.mat$")
KEEP_BITS = 12


def trim_mantissa(x: np.ndarray, keep_bits: int = KEEP_BITS) -> np.ndarray:
    drop = 23 - keep_bits
    bits = np.ascontiguousarray(x, dtype=np.float32).view(np.uint32)
    rounded = (bits + np.uint32(1 << (drop - 1))) & np.uint32((0xFFFFFFFF << drop) & 0xFFFFFFFF)
    return rounded.view(np.float32)


def char_orders(bearing: str) -> dict[str, float]:
    """Defect frequencies in shaft orders (contact angle 0, outer ring fixed)."""
    pitch = PITCH_D.get(FACT[bearing], 29.05)
    r = BALL_D / pitch
    return {"FTF": 0.5 * (1 - r), "BPFO": N_BALLS / 2 * (1 - r), "BPFI": N_BALLS / 2 * (1 + r),
            "BSF": pitch / (2 * BALL_D) * (1 - r ** 2), "pitch_diameter_mm": pitch}


def channels(path: Path) -> dict[str, np.ndarray]:
    m = sio.loadmat(path, squeeze_me=True, struct_as_record=False)
    s = m[[k for k in m if not k.startswith("__")][0]]
    return {e.Name: np.asarray(e.Data, dtype=float).ravel() for e in np.atleast_1d(s.Y)}


def amp_spectrum(x: np.ndarray, fs: float) -> tuple[np.ndarray, np.ndarray]:
    x = x - x.mean()
    spec = np.abs(np.fft.rfft(x * np.hanning(len(x)))) * 2 / (0.5 * len(x))
    return np.fft.rfftfreq(len(x), 1 / fs), spec


def envelope(x: np.ndarray) -> np.ndarray:
    n = len(x)
    X = np.fft.fft(x - x.mean())
    f = np.fft.fftfreq(n, 1 / FS)
    X[(np.abs(f) < BAND[0]) | (np.abs(f) > BAND[1])] = 0
    h = np.zeros(n)                       # analytic signal of the band-passed vibration
    h[0] = 1
    h[1:(n + 1) // 2] = 2
    if n % 2 == 0:
        h[n // 2] = 1
    return np.abs(np.fft.ifft(X * h))


def peak_db(freq: np.ndarray, spec: np.ndarray, target: float) -> float:
    if target <= 0 or target >= freq[-1]:
        return float("nan")
    tol = 0.015 * target
    near = (freq >= target - tol) & (freq <= target + tol)
    ring = (freq >= target - 5) & (freq <= target + 5) & ~near
    floor = np.median(spec[ring]) if ring.any() else np.nan
    return float(20 * np.log10(spec[near].max() / floor)) if near.any() and floor > 0 else float("nan")


def process(path: Path) -> dict:
    m = NAME.search(path.name)
    n_set, m_set, f_set, bearing, idx = m.groups()
    ch = channels(path)
    vib, i1, i2 = ch["vibration_1"], ch["phase_current_1"], ch["phase_current_2"]
    speed = float(np.mean(ch["speed"]))                     # rpm
    fr = speed / 60.0
    co = char_orders(bearing)
    env = envelope(vib)
    fe_, se = amp_spectrum(env, FS)
    fi, si = amp_spectrum(i1, FS)
    band = (fi >= 10) & (fi <= 250)
    f_el = float(fi[band][np.argmax(si[band])])
    a_el = float(si[band].max())
    row = {
        "file": path.name, "bearing": bearing, "condition": f"N{n_set}_M{m_set}_F{f_set}", "index": int(idx),
        "speed_set_rpm": int(n_set) * 100, "torque_set_Nm": int(m_set) / 10, "force_set_N": int(f_set) * 100,
        "speed_rpm": round(speed, 2), "torque_Nm": round(float(np.mean(ch["torque"])), 4),
        "force_N": round(float(np.mean(ch["force"])), 2), "temp_C": round(float(np.mean(ch["temp_2_bearing_module"])), 2),
        "f_shaft_Hz": round(fr, 4), "f_supply_Hz": round(f_el, 3),
        "pitch_diameter_mm": co["pitch_diameter_mm"],
        **{f"{k}_order": round(co[k], 4) for k in ("FTF", "BPFO", "BPFI", "BSF")},
        "vib_rms": round(float(np.sqrt(np.mean((vib - vib.mean()) ** 2))), 5),
        "vib_kurtosis": round(float(kurtosis(vib, fisher=False)), 4),
        "vib_crest": round(float(np.abs(vib - vib.mean()).max() / np.sqrt(np.mean((vib - vib.mean()) ** 2))), 4),
        "cur1_rms": round(float(np.sqrt(np.mean(i1 ** 2))), 5), "cur2_rms": round(float(np.sqrt(np.mean(i2 ** 2))), 5),
        "n_samples": len(vib),
        "signal_hash": hashlib.sha1(np.ascontiguousarray(np.r_[vib, i1, i2]).tobytes()).hexdigest()[:16],
    }
    for name, order in (("fr", 1.0), ("FTF", co["FTF"]), ("BSF", co["BSF"]), ("BPFO", co["BPFO"]),
                        ("BPFO2", 2 * co["BPFO"]), ("BPFI", co["BPFI"]), ("BPFI2", 2 * co["BPFI"]),
                        ("BPFI-fr", co["BPFI"] - 1), ("BPFI+fr", co["BPFI"] + 1)):
        row[f"env_{name}_dB"] = round(peak_db(fe_, se, order * fr), 3)
    for name, order in (("BPFO", co["BPFO"]), ("BPFI", co["BPFI"])):
        lo = peak_db(fi, si, f_el - order * fr)
        hi = peak_db(fi, si, f_el + order * fr)
        row[f"cur_{name}_sb_dB"] = round(float(np.nanmax([lo, hi])), 3)
    env_orders = np.interp(ORDERS * fr, fe_, se)
    cur_db = 20 * np.log10(np.interp(f_el + OFFSETS * fr, fi, si) / a_el + 1e-12)
    return {"row": row, "env": env_orders.astype(np.float32), "cur": cur_db.astype(np.float32)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--work", default=None)
    ap.add_argument("--budget", type=float, default=1e9)
    args = ap.parse_args()
    raw, out = Path(args.raw), Path(args.out)
    work = Path(args.work) if args.work else out / "_work"
    work.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in raw.glob("K*/*.mat") if NAME.search(p.name))
    t0 = time.time()
    for p in files:
        cache = work / (p.stem + ".npz")
        if cache.exists():
            continue
        if time.time() - t0 > args.budget:
            break
        r = process(p)
        np.savez(cache, env=r["env"], cur=r["cur"], row=np.array([json.dumps(r["row"])]))
    done = [work / (p.stem + ".npz") for p in files]
    left = sum(not c.exists() for c in done)
    if left:
        print(f"{len(files) - left} of {len(files)} files processed; run again for the remaining {left}")
        return
    rows, env, cur = [], [], []
    for k, c in enumerate(done):
        z = np.load(c)
        rows.append(json.loads(str(z["row"][0])))
        env.append(z["env"])
        cur.append(z["cur"])
    meas = pd.DataFrame(rows)
    meas.insert(0, "measurement_id", np.arange(len(meas), dtype=np.int32))
    (out / "spectra").mkdir(parents=True, exist_ok=True)
    meas.to_csv(out / "measurements.csv", index=False)
    for name, arr, axis, col in (("envelope_orders", env, ORDERS, "order"), ("current_sidebands", cur, OFFSETS, "offset_order")):
        a = np.stack(arr)
        df = pd.DataFrame({"measurement_id": np.repeat(meas["measurement_id"].to_numpy(), len(axis)),
                           col: np.tile(axis.astype(np.float32), len(a)),
                           "value": trim_mantissa(a.ravel().astype(np.float32))})
        pq.write_table(pa.Table.from_pandas(df, preserve_index=False), out / "spectra" / f"{name}.parquet",
                       compression="zstd", compression_level=19, use_dictionary=False,
                       use_byte_stream_split=[col, "value"], row_group_size=200_000)
    print(f"{len(meas)} measurements from {meas['bearing'].nunique()} bearings; "
          f"{meas['signal_hash'].duplicated().sum()} duplicate signal blocks")


if __name__ == "__main__":
    main()
