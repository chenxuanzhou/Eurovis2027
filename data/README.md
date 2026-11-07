# Data

Four public fault datasets, each in its own folder with a README, prepared the same way: tidy tables of
the instances, signals or spectra in compact Parquet, a normal reference, per-instance evidence scored
against it, grouped splits, and a knowledge base in one shared schema. Licences differ per folder
(`LICENSE.md`).

| Folder | System | Instances | Fault classes | Grouped splits |
|---|---|---|---|---|
| `voraus_ad/` | Yu-Cobot pick-and-place (voraus-AD) | 2,122 cycles (755 anomalous) | 12 categories → 14 FMEA modes | leave-setting-out (72 fault settings) |
| `aursad/` | UR3e screwdriving (AURSAD) | 2,045 tightenings + 2,049 loosenings | 4 + normal | leave-session-out (30 sessions) |
| `robot_failures/` | wrist force/torque after failure detection (UCI) | 463 instances, 251 distinct windows | 16 classes in 5 problems | grouped by identical window |
| `paderborn/` | 6203 ball bearings on a drive test rig | 960 measurements of 12 bearings | 5 damage modes + healthy | leave-bearing-out |

## Shared conventions

- **Knowledge base** (`<dataset>/kb/`). `failure_modes.json` lists the modes; `refinement_lattice.json`
  (schema `refinement-lattice/1`) gives, for a chain of cumulative evidence levels L0 (no evidence) →
  L1 → …, the partition of the modes into blocks of structural twins. Following structural FDI, mode a
  is isolable from mode b at a level when some symptom row read so far is 1 for a and 0 for b; equal
  columns are twins, a column strictly inside another is a one-way (nested) pair. Per level: `blocks`,
  `block_parent` (index into the previous level's blocks), `n_blocks`, `twin_blocks`, `nested_pairs`,
  `isolable[a][b]`, `instances_with_true_mode_in_twin_block`; at the top: `modes` (display order that
  keeps every level's blocks contiguous), `mode_label`, `null_modes` (no-fault hypotheses, if any),
  `instances_per_mode`. For the three new datasets, `fsm.csv` holds the full fault signature matrix,
  `twin_groups.json` every twin block with the level and rows that split it, `assumptions.json` what the
  authored symptom model rests on, and `evidence_map.json` (AURSAD, Paderborn) which measured features
  speak to which symptom row.
- **Authored knowledge.** The voraus-AD knowledge base is the FMEA of the SAFEPROCESS 2027 study. The
  other three were written for this repository from each dataset's documentation (class definitions,
  fact sheets, technical report) and the physics of the process; they are structural models (which
  symptoms a mode can switch on), never thresholds learned from the data.
- **Evidence.** Scores are z against the normal reference of the same context (problem, operating
  condition, grid point), robust (median / MAD) for summary features. References always leave out the
  instance's own group (its bearing, session, or itself), so evidence can be used for evaluation.
- **Splits** are grouped by the unit that carries the fault physically or in the recording (fault
  setting, recording session, identical window, bearing) and come with five seeds.
- **Duplicates** are flagged in every dataset that has them: identical readings across the UCI problems,
  duplicated recordings in AURSAD (some with conflicting labels), copied files in Paderborn KA04.
- **Compact signals.** Per-instance curves are float32 rounded to 12 mantissa bits (relative error
  ≤ 1.2e-4) with Parquet BYTE_STREAM_SPLIT + zstd; pandas/pyarrow and DuckDB read them directly.
