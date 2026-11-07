# EuroVis 2027 — data for visual analytics of fault diagnosis

Data for a EuroVis 2027 full-paper project on interactive visual analytics of fault diagnosis for
industrial robots. Four public datasets are prepared the same way, so the same views can run on each:

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
each dataset folder documents its files. **Status:** all products are built (86 MB) and validated.
Rebuilt from raw, the 755 voraus-AD evidence records match the SAFEPROCESS records exactly.

This repository holds data only. The processing code is kept by the authors and is not published;
file descriptions that mention `pipeline/…` refer to it.

## Licence

Each folder keeps the licence of its source dataset — voraus-AD CC BY-NC-SA 4.0, AURSAD CC BY 4.0,
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
