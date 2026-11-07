# Licences of the data in `data/`

Each dataset folder is an adaptation of a public dataset and keeps that dataset's licence. The
knowledge-base files authored for this repository (`kb/` of each folder) and every derived table are
released under the licence of the folder they sit in. Raw files are not redistributed, except the five
small UCI files in `data/robot_failures/raw/`, which are copied unchanged.

| Folder | Source | Licence of the folder |
|---|---|---|
| `data/voraus_ad/` | voraus-AD (voraus robotik GmbH) | CC BY-NC-SA 4.0 |
| `data/aursad/` | AURSAD (Aarhus University, Technicon ApS) | CC BY 4.0 |
| `data/robot_failures/` | Robot Execution Failures (UCI Machine Learning Repository) | CC BY 4.0 |
| `data/paderborn/` | Bearing DataCenter (KAt, Paderborn University) | CC BY-NC 4.0 |

## data/voraus_ad/

> J. T. Brockmann, M. Rudolph, B. Rosenhahn and B. Wandt, "The voraus-AD Dataset for Anomaly
> Detection in Robot Applications," *IEEE Transactions on Robotics*, vol. 40, pp. 438–451, 2024,
> doi:10.1109/TRO.2023.3332224. Rights holder: voraus robotik GmbH.

voraus-AD is licensed under CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/). Its
NonCommercial and ShareAlike terms carry over: non-commercial use only, with attribution, adaptations
under the same licence. `data/voraus_ad/evidence/` (records, unread-channel statistics, payload torque)
and `data/voraus_ad/kb/certificates.json` are copied from the SAFEPROCESS 2027 repository
(https://github.com/chenxuanzhou/Structural-Non-Isolability-in-Knowledge-Based-Robot-Fault-Diagnosis,
commit 438389f), where they are released under the same licence.

## data/aursad/

> B. Leporowski, D. Tola, C. Hansen and A. Iosifidis, "AURSAD: Universal Robot Screwdriving Anomaly
> Detection Dataset," arXiv:2102.01409, 2021. Data: Zenodo, doi:10.5281/zenodo.4559556 (version 1.1).

AURSAD is licensed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). The derived files
are released under CC BY 4.0 with attribution to the authors above.

## data/robot_failures/

> L. Seabra Lopes and L. M. Camarinha-Matos, "Robot Execution Failures," UCI Machine Learning
> Repository, 1999, doi:10.24432/C5M89N.

Licensed under CC BY 4.0. `raw/lp1.data` … `raw/lp5.data` are the original files, unchanged.

## data/paderborn/

> C. Lessmeier, J. K. Kimotho, D. Zimmer and W. Sextro, "Condition Monitoring of Bearing Damage in
> Electromechanical Drive Systems by Using Motor Current Signals of Electric Motors: A Benchmark Data
> Set for Data-Driven Classification," European Conference of the PHM Society, Bilbao, 2016.
> KAt-DataCenter, Chair of Design and Drive Technology, Paderborn University
> (https://mb.uni-paderborn.de/kat/forschung/kat-datacenter/bearing-datacenter).

The bearing data are licensed under CC BY-NC 4.0 (https://creativecommons.org/licenses/by-nc/4.0/):
non-commercial academic use with citation of the origin. The derived files are released under
CC BY-NC 4.0 with the same citation.
