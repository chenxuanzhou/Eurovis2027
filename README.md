# EuroVis 2027 — data for visual analytics of fault diagnosis

Data and processing code for a EuroVis 2027 full-paper project on interactive visual analytics of fault
diagnosis for industrial robots. Four public datasets are prepared the same way, so the same views can
run on each:

| Dataset | System | Folder |
|---|---|---|
| [voraus-AD](https://github.com/vorausrobotik/voraus-ad-dataset) | Yu-Cobot pick-and-place, 130 signals, 12 anomaly categories | `data/voraus_ad/` |
| [AURSAD](https://zenodo.org/records/4559556) | UR3e screwdriving, 125 robot and screwdriver signals, 4 anomaly types | `data/aursad/` |
| [Robot Execution Failures](https://doi.org/10.24432/C5M89N) (UCI) | wrist force/torque after failure detection, 5 motions, 16 failure classes | `data/robot_failures/` |
| [Paderborn bearings](https://mb.uni-paderborn.de/kat/forschung/kat-datacenter/bearing-datacenter) | drive test rig, vibration and motor current, real bearing damage | `data/paderborn/` |

The voraus-AD knowledge base and evidence records come from the SAFEPROCESS 2027 study
([Structural Non-Isolability in Knowledge-Based Robot Fault Diagnosis](https://github.com/chenxuanzhou/Structural-Non-Isolability-in-Knowledge-Based-Robot-Fault-Diagnosis));
the knowledge bases of the other three were authored for this repository in the same schema.

`data/README.md` explains the shared conventions (knowledge-base schema, evidence, splits, duplicates);
each dataset folder documents its files. **Status:** all products are built (86 MB) and pass
`pipeline/validate.py`. Rebuilt from raw, the 755 voraus-AD evidence records match the SAFEPROCESS
records exactly.

## Rebuild

Python 3.10 or newer.

```bash
python -m pip install -r requirements.txt
python pipeline/run_all.py --no-raw     # everything that needs no raw data
python pipeline/run_all.py              # also the raw extraction steps, where the raw files are present
python pipeline/run_all.py aursad       # one dataset
```

Each dataset's `raw/README.md` says which raw file it needs and where to put it. Without raw files every
product is rebuilt from the committed intermediate tables; with them, the extraction steps run first
(voraus-AD about 1 minute and 2.5 GB of memory, AURSAD about 1 minute, Paderborn about 5 minutes).
`pipeline/validate.py` checks every dataset against its published counts, the split invariants and the
knowledge-base structure, and every file against the GitHub size limit.

## Layout

```
data/<dataset>/      derived data, documented in data/<dataset>/README.md (licences: data/LICENSE.md)
pipeline/common/     shared code: refinement lattice, compact Parquet, checks
pipeline/<dataset>/  build steps of one dataset (run.py, extract.py where raw data are needed,
                     build.py, kb_spec.py with the authored knowledge base, validate.py)
pipeline/voraus_ad/vendor/   the official voraus-AD enums and the knowledge base and evidence
                     builder of the SAFEPROCESS study, unchanged
```

## Licence

Code: MIT (`LICENSE`). Vendored code keeps its MIT licences (`pipeline/voraus_ad/vendor/LICENSE-*.txt`).
Data: each folder keeps the licence of its source dataset — voraus-AD CC BY-NC-SA 4.0, AURSAD CC BY 4.0,
UCI CC BY 4.0, Paderborn CC BY-NC 4.0 (`data/LICENSE.md`).

## Citations of the datasets

> J. T. Brockmann, M. Rudolph, B. Rosenhahn and B. Wandt, "The voraus-AD Dataset for Anomaly
> Detection in Robot Applications," IEEE Transactions on Robotics, vol. 40, pp. 438–451, 2024.

> B. Leporowski, D. Tola, C. Hansen and A. Iosifidis, "AURSAD: Universal Robot Screwdriving Anomaly
> Detection Dataset," arXiv:2102.01409, 2021.

> L. Seabra Lopes and L. M. Camarinha-Matos, "Robot Execution Failures," UCI Machine Learning
> Repository, 1999, doi:10.24432/C5M89N.

> C. Lessmeier, J. K. Kimotho, D. Zimmer and W. Sextro, "Condition Monitoring of Bearing Damage in
> Electromechanical Drive Systems by Using Motor Current Signals of Electric Motors: A Benchmark Data
> Set for Data-Driven Classification," European Conference of the PHM Society, 2016.
