# EuroVis 2027 — data for visual analytics of robot fault diagnosis

Data and processing code for a EuroVis 2027 full-paper project on interactive visual analytics of
fault diagnosis for an industrial robot. Everything is derived from the public
[voraus-AD](https://github.com/vorausrobotik/voraus-ad-dataset) dataset (six-axis collaborative robot,
pick-and-place, 130 signals, 12 anomaly categories) and from the FMEA knowledge base and evidence
records of the SAFEPROCESS 2027 study
([Structural Non-Isolability in Knowledge-Based Robot Fault Diagnosis](https://github.com/chenxuanzhou/Structural-Non-Isolability-in-Knowledge-Based-Robot-Fault-Diagnosis)).

## What is in `data/`

| Folder | Contents | Needs the raw parquet |
|---|---|---|
| `catalog/` | 130 signals, 13 categories, 77 settings (variants), 15 actions | no |
| `kb/` | 14 failure modes, fault signature matrix, isolability refinement lattice (L0–L4), twin groups and what separates them, certificate results | no |
| `evidence/` | Evidence records of the 755 anomalous cycles; statistics of the unread channels; payload torque | no |
| `splits/` | Five leave-setting-out splits of the anomalous cycles (seeds 0–4) | no |
| `cycles/` | One row per cycle with labels, split membership and timing; action segments | yes |
| `envelope/` | Normal envelope of all 130 channels over the 948 training cycles, 500 progress points | yes |
| `signals/grid500/` | The 1,174 test cycles and 100 training cycles on the 500-point progress grid, 44 channels | yes |
| `evidence/` (raw part) | Evidence records of the 419 anomaly-free test cycles; check that the 755 anomalous records rebuild from raw | yes |

`data/README.md` documents every file, its columns and the conventions (cycle id, splits, progress
grid, z-scores). **Status:** the products that need no raw data are built; the raw-derived ones are
produced by `pipeline/build_from_raw.py` once the raw parquet is in `data/raw/`.

## Rebuild

Python 3.11 or newer.

```bash
python -m pip install -r requirements.txt
```

Copy `voraus-ad-dataset-100hz.parquet` into `data/raw/` (see `data/raw/README.md`). For the copied
evidence and the knowledge-base cross-check, point `SNIS_REPO` at a checkout of the SAFEPROCESS 2027
repository (default: a sibling folder of this one). Then:

```bash
python pipeline/run_all.py
```

`run_all.py` runs, in order, `build_evidence.py`, `build_catalog.py`, `build_kb.py`,
`build_from_raw.py` (skipped when the parquet is missing) and `validate.py`, which checks every
product against the dataset counts (2,122 cycles; 948 / 419 / 755; 72 settings) and the split sizes
of the SAFEPROCESS study.

## Layout

```
data/        derived data (CC BY-NC-SA 4.0), documented in data/README.md
pipeline/    build scripts; pipeline/vendor/ holds the official voraus-AD enums and the
             knowledge base and evidence builder of the SAFEPROCESS study, unchanged
```

## Licence

Code: MIT (`LICENSE`). Vendored code keeps its MIT licences (`pipeline/vendor/LICENSE-*.txt`).
Data in `data/`: an adaptation of voraus-AD, released under CC BY-NC-SA 4.0 (`data/LICENSE.md`).

## Citation of the dataset

> J. T. Brockmann, M. Rudolph, B. Rosenhahn and B. Wandt, "The voraus-AD Dataset for Anomaly
> Detection in Robot Applications," IEEE Transactions on Robotics, vol. 40, pp. 438–451, 2024.
